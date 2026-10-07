"""Localização dos 4 marcadores quadrados dos cantos da folha.

Não depende do layout da folha (nada de omr_config aqui): recebe uma imagem e devolve
os 4 pontos em ordem horária. Foi escrito para fotos reais: sombra, mesa escura,
folha girada ou inclinada, retrato ou paisagem.
"""
import itertools
import math

import cv2
import numpy as np

# lado do marcador relativo à maior dimensão da imagem
LADO_MIN_FRAC = 0.006
LADO_MAX_FRAC = 0.06
EXTENT_MIN = 0.82          # quadrado ~0.9+; círculo cheio dá 0.785 e é descartado
SOLIDEZ_MIN = 0.90
ASPECTO_MARCADOR_MAX = 1.45
# proporção (lado maior / lado menor) esperada do retângulo formado pelos 4 marcadores
RAZAO_FOLHA_MIN = 1.10
RAZAO_FOLHA_MAX = 1.75
# níveis de corte aplicados sobre a imagem com iluminação normalizada (0 = tinta, 255 = papel)
CORTES = (120, 150, 95, 180)


def _impar(n):
    n = int(n)
    return n if n % 2 else n + 1


def normalizar_iluminacao(cinza, kernel=None):
    """Divide a imagem pelo 'fundo' local (papel). Remove sombras/gradientes e deixa
    o papel ~255 e a tinta bem escura, não importa a luz da foto."""
    if kernel is None:
        kernel = _impar(max(25, max(cinza.shape[:2]) * 0.05))
    kernel = _impar(kernel)
    fundo = cv2.dilate(cinza, cv2.getStructuringElement(cv2.MORPH_RECT, (kernel, kernel)))
    fundo = cv2.GaussianBlur(fundo, (kernel, kernel), 0)
    return cv2.divide(cinza, np.maximum(fundo, 1), scale=255)


# Passada normal e passada tolerante (marcadores pequenos/borrados deixam de ser quadrados perfeitos)
RIGOROSO = dict(lado_min=LADO_MIN_FRAC, extent=EXTENT_MIN, solidez=SOLIDEZ_MIN)
TOLERANTE = dict(lado_min=0.0035, extent=0.72, solidez=0.84)


def candidatos(binaria, dim, p=RIGOROSO):
    """Blobs escuros quase quadrados e sólidos. Devolve [(cx, cy, lado)]."""
    # RETR_LIST (e não EXTERNAL): numa mesa escura os marcadores ficam "dentro" do
    # contorno da mesa e RETR_EXTERNAL simplesmente os ignora.
    contornos, _ = cv2.findContours(binaria, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[-2:]
    saida = []
    for c in contornos:
        area = cv2.contourArea(c)
        if area < 12:
            continue
        (_, _), (rw, rh), _ = cv2.minAreaRect(c)   # retângulo girado: tolera folha inclinada
        if min(rw, rh) < 1:
            continue
        lado = math.sqrt(rw * rh)
        if not (p["lado_min"] * dim <= lado <= LADO_MAX_FRAC * dim):
            continue
        if max(rw, rh) / min(rw, rh) > ASPECTO_MARCADOR_MAX:
            continue
        if area / (rw * rh) < p["extent"]:
            continue
        hull_area = cv2.contourArea(cv2.convexHull(c))
        if hull_area <= 0 or area / hull_area < p["solidez"]:
            continue
        m = cv2.moments(c)
        if m["m00"] == 0:
            continue
        saida.append((m["m10"] / m["m00"], m["m01"] / m["m00"], lado))
    return saida


def _ordenar_horario(pts):
    """Ordem horária (na tela) começando pelo ponto mais perto do canto sup. esquerdo."""
    c = pts.mean(axis=0)
    ang = np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0])
    pts = pts[np.argsort(ang)]
    inicio = int(np.argmin(pts[:, 0] + pts[:, 1]))
    return np.roll(pts, -inicio, axis=0)


def _angulo(a, b, c):
    v1, v2 = a - b, c - b
    cos = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


def melhores_quadrilateros(cands, largura, altura, maximo=4):
    """Escolhe os grupos de 4 candidatos que formam um retângulo plausível (com
    perspectiva). Devolve [(area, pts 4x2 float32 em ordem horária)], maior área primeiro."""
    if len(cands) < 4:
        return []
    cx0, cy0 = largura / 2.0, altura / 2.0
    if len(cands) > 14:   # os marcadores ficam nas pontas: mantém os mais afastados do centro
        cands = sorted(cands, key=lambda c: -((c[0] - cx0) ** 2 + (c[1] - cy0) ** 2))[:14]
    achados = []
    for comb in itertools.combinations(cands, 4):
        lados = [c[2] for c in comb]
        if max(lados) / min(lados) > 1.8:
            continue
        pts = _ordenar_horario(np.array([[c[0], c[1]] for c in comb], dtype="float32"))
        e = [np.linalg.norm(pts[i] - pts[(i + 1) % 4]) for i in range(4)]
        if min(e) < 1:
            continue
        # lados opostos parecidos (perspectiva moderada)
        if not (0.55 <= e[0] / e[2] <= 1.8 and 0.55 <= e[1] / e[3] <= 1.8):
            continue
        h, v = (e[0] + e[2]) / 2, (e[1] + e[3]) / 2
        razao = max(h, v) / min(h, v)
        if not (RAZAO_FOLHA_MIN <= razao <= RAZAO_FOLHA_MAX):
            continue
        if any(not (50 <= _angulo(pts[i - 1], pts[i], pts[(i + 1) % 4]) <= 130) for i in range(4)):
            continue
        achados.append((cv2.contourArea(pts), pts))
    achados.sort(key=lambda t: -t[0])
    return achados[:maximo]


def localizar_quadrilateros(cinza, maximo=4):
    """Tenta vários cortes (e uma 2ª passada tolerante) até achar quadriláteros.
    Devolve (lista de pts 4x2, nº máximo de candidatos vistos)."""
    altura, largura = cinza.shape[:2]
    dim = max(altura, largura)
    norm = normalizar_iluminacao(cv2.GaussianBlur(cinza, (3, 3), 0))
    melhor_n = 0
    for params in (RIGOROSO, TOLERANTE):
        for corte in CORTES:
            binaria = (norm < corte).astype("uint8") * 255
            cands = candidatos(binaria, dim, params)
            melhor_n = max(melhor_n, len(cands))
            quads = melhores_quadrilateros(cands, largura, altura, maximo)
            if quads:
                return [q[1] for q in quads], len(cands)
    return [], melhor_n
