"""Acha a folha na foto e devolve a imagem "endireitada" (canvas) pronta para leitura."""
from collections import namedtuple

import cv2
import numpy as np

import marcadores as mk
from omr_config import CANVAS_H, CANVAS_W, CENTROS, RAIO_ANEL

Folha = namedtuple("Folha", "recorte cinza_norm matriz pontos score_aneis n_candidatos")

SCORE_ANEIS_MIN = 0.60     # fração mínima dos anéis que precisa "bater" (certo ≈1.0; errado ≤ 0.25)
CORTE_ANEL = 200           # anel fino e borrado fica cinza-claro: corte generoso
BUSCA_AJUSTE = 6           # px: ajuste fino de posição (±)

_DESTINO = np.float32([[0, 0], [CANVAS_W - 1, 0], [CANVAS_W - 1, CANVAS_H - 1], [0, CANVAS_H - 1]])


def _pontos_dos_aneis():
    """Pontos (x, y) sobre o anel de cada bolha: usados para conferir orientação/posição."""
    pts = []
    for cx, cy in CENTROS:
        for ang in np.linspace(0, 2 * np.pi, 24, endpoint=False):
            pts.append((cx + (RAIO_ANEL - 1) * np.cos(ang), cy + (RAIO_ANEL - 1) * np.sin(ang)))
    return np.round(np.array(pts)).astype(int)


_ANEIS = _pontos_dos_aneis()


def _score_aneis(tinta, dx=0, dy=0):
    xs = np.clip(_ANEIS[:, 0] + dx, 0, CANVAS_W - 1)
    ys = np.clip(_ANEIS[:, 1] + dy, 0, CANVAS_H - 1)
    return float(tinta[ys, xs].mean())


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


def _ajuste_fino(M, fina):
    """Pequena correção de translação (marcador deslocado, foto borrada): procura o
    deslocamento em que os anéis mais encaixam e usa o centro do platô de melhores."""
    grade = range(-BUSCA_AJUSTE, BUSCA_AJUSTE + 1)
    pontos = [(dx, dy, _score_aneis(fina, dx, dy)) for dy in grade for dx in grade]
    topo = max(p[2] for p in pontos)
    bons = [(dx, dy) for dx, dy, s in pontos if s >= topo - 0.03]
    dx = int(round(np.mean([b[0] for b in bons])))
    dy = int(round(np.mean([b[1] for b in bons])))
    if dx or dy:
        M = np.array([[1, 0, -dx], [0, 1, -dy], [0, 0, 1]], dtype="float64") @ M
    return M


def localizar_folha(img):
    """Retorna Folha(...) ou (None, n_candidatos) quando não acha a folha de respostas."""
    if img is None:
        return None, 0
    cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    quads, n = mk.localizar_quadrilateros(cinza, maximo=4)
    melhor = None
    for pts in quads:                                    # o 1º quadrilátero que "parece a folha" vence
        s, M, p, tinta = _melhor_orientacao(cinza, pts)
        if s >= SCORE_ANEIS_MIN:
            melhor = (s, M, p, tinta)
            break
    if melhor is None:
        return None, n
    s, M, p, tinta = melhor
    M = _ajuste_fino(M, tinta)
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
