"""Acha a folha na foto e devolve a imagem "endireitada" (canvas) pronta para leitura."""
from collections import namedtuple

import cv2
import numpy as np

import marcadores as mk
from omr_config import CANVAS_H, CANVAS_W, CENTROS, RAIO_ANEL

Folha = namedtuple("Folha", "recorte cinza_norm matriz pontos score_aneis n_candidatos")

SCORE_PRE_MIN = 0.25       # triagem rápida (antes do ajuste fino) para descartar falsos quadriláteros
SCORE_ANEIS_MIN = 0.60     # fração mínima dos anéis que precisa "bater" (certo ≈1.0; errado ≤ 0.25)
CORTE_ANEL = 230           # anel fino e fraco na foto de celular: corte generoso (a checagem de anéis é por fração de pontos)
BUSCA_AJUSTE = 12          # px: ajuste fino de posição (±), separado p/ metade esquerda e direita

_DESTINO = np.float32([[0, 0], [CANVAS_W - 1, 0], [CANVAS_W - 1, CANVAS_H - 1], [0, CANVAS_H - 1]])


TOLERANCIA_RAIO = 3        # px: o raio real do anel pode diferir de RAIO_ANEL (calibração imperfeita)


def _pontos_dos_aneis(delta=0):
    """Pontos (x, y) sobre o anel de cada bolha: usados para conferir orientação/posição."""
    pts = []
    for cx, cy in CENTROS:
        for ang in np.linspace(0, 2 * np.pi, 24, endpoint=False):
            pts.append((cx + (RAIO_ANEL - 1 + delta) * np.cos(ang), cy + (RAIO_ANEL - 1 + delta) * np.sin(ang)))
    return np.round(np.array(pts)).astype(int)


_ANEIS_POR_RAIO = [_pontos_dos_aneis(d) for d in range(-TOLERANCIA_RAIO, TOLERANCIA_RAIO + 1)]


def _score_aneis(tinta, dx=0, dy=0, grupo=None):
    """Fração dos pontos dos anéis que caem em tinta (melhor resultado entre os raios testados).
    grupo: None = todas as bolhas; 0 = questões 1-5 (esquerda); 1 = questões 6-10 (direita)."""
    melhor = 0.0
    for aneis in _ANEIS_POR_RAIO:
        a = aneis if grupo is None else aneis[grupo * _PTS_GRUPO:(grupo + 1) * _PTS_GRUPO]
        xs = np.clip(a[:, 0] + dx, 0, CANVAS_W - 1)
        ys = np.clip(a[:, 1] + dy, 0, CANVAS_H - 1)
        melhor = max(melhor, float(tinta[ys, xs].mean()))
    return melhor


_PTS_GRUPO = 25 * 24            # 25 bolhas (5 questões x 5 alternativas) x 24 pontos por anel


def normalizar_canvas(cinza_canvas):
    """Iluminação uniforme dentro do canvas (kernel maior que a bolha preenchida)."""
    return mk.normalizar_iluminacao(cinza_canvas, kernel=61)


def binarizar(recorte):
    """Imagem binária (tinta = 255) do canvas, imune a sombra. Aceita BGR ou cinza."""
    cinza = cv2.cvtColor(recorte, cv2.COLOR_BGR2GRAY) if recorte.ndim == 3 else recorte
    norm = normalizar_canvas(cinza)
    limiar, _ = cv2.threshold(norm, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    limiar = float(np.clip(limiar, 110, 170))
    return (norm < limiar).astype("uint8") * 255


def _melhor_orientacao(cinza, pts):
    """Testa as 4 rotações (retrato, paisagem, de cabeça p/ baixo...) e fica com a que
    faz os 50 anéis das bolhas caírem no lugar. Também serve para rejeitar falsos achados."""
    melhor = None
    for giro in range(4):
        p = np.roll(pts, -giro, axis=0)
        M = cv2.getPerspectiveTransform(p, _DESTINO)
        canvas = cv2.warpPerspective(cinza, M, (CANVAS_W, CANVAS_H), flags=cv2.INTER_LINEAR)
        fina = (normalizar_canvas(canvas) < CORTE_ANEL).astype("uint8")
        tinta = cv2.dilate(fina, np.ones((3, 3), np.uint8))    # tolera ±1 px
        s = _score_aneis(tinta)
        if melhor is None or s > melhor[0]:
            melhor = (s, M, p, fina)
    return melhor


def _melhor_deslocamento(fina, grupo):
    """(dx, dy, score): deslocamento em que os anéis do grupo mais encaixam (centro do platô)."""
    grade = range(-BUSCA_AJUSTE, BUSCA_AJUSTE + 1)
    pontos = [(dx, dy, _score_aneis(fina, dx, dy, grupo)) for dy in grade for dx in grade]
    topo = max(p[2] for p in pontos)
    bons = [(dx, dy) for dx, dy, s in pontos if s >= topo - 0.03]
    return (float(np.mean([b[0] for b in bons])), float(np.mean([b[1] for b in bons])), topo)


def _ajuste_fino(M, fina):
    """Corrige a posição da grade de bolhas: a metade esquerda e a direita da folha podem estar
    deslocadas de forma diferente (foto com perspectiva/folha levemente torta). Mede cada metade
    separadamente e aplica uma correção linear em x (translação + escala). Retorna (M, score)."""
    dxe, dye, se = _melhor_deslocamento(fina, 0)
    dxd, dyd, sd = _melhor_deslocamento(fina, 1)
    xe = float(np.mean([c[0] for c in CENTROS[:25]]))
    xd = float(np.mean([c[0] for c in CENTROS[25:]]))
    # deslocamento(x) = a + b*x, passando pelos dois grupos (posição real = configurada + deslocamento)
    bx = (dxd - dxe) / (xd - xe)
    ax = dxe - bx * xe
    by = (dyd - dye) / (xd - xe)
    ay = dye - by * xe
    # canvas corrigido: q' = q - deslocamento(q)
    corr = np.array([[1 - bx, 0, -ax], [-by, 1, -ay], [0, 0, 1]], dtype="float64")
    return corr @ M, (se + sd) / 2.0


def localizar_folha(img):
    """Retorna Folha(...) ou (None, n_candidatos) quando não acha a folha de respostas."""
    if img is None:
        return None, 0
    cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    quads, n = mk.localizar_quadrilateros(cinza, maximo=4)
    melhor = None
    for pts in quads:                                    # o 1º quadrilátero que "parece a folha" vence
        s, M, p, tinta = _melhor_orientacao(cinza, pts)
        if s < SCORE_PRE_MIN:
            continue
        M2, s2 = _ajuste_fino(M, tinta)
        if s2 >= SCORE_ANEIS_MIN:
            melhor = (s2, M2, p)
            break
    if melhor is None:
        return None, n
    s, M, p = melhor
    recorte = cv2.warpPerspective(img, M, (CANVAS_W, CANVAS_H), flags=cv2.INTER_CUBIC)
    cinza_canvas = cv2.cvtColor(recorte, cv2.COLOR_BGR2GRAY)
    return Folha(recorte, normalizar_canvas(cinza_canvas), M, p, s, n), n


def extrairMaiorCtn(img):
    """Compatível com o código antigo (mainWebCam): (recorte, bbox) ou (None, None)."""
    folha, _ = localizar_folha(img)
    if folha is None:
        return None, None
    x, y, w, h = cv2.boundingRect(folha.pontos.astype("int32"))
    return folha.recorte, [x, y, w, h]
