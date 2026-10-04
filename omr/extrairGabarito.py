import cv2
import numpy as np

from omr_config import (CANVAS_W,CANVAS_H,MARCADOR_AREA_MIN_FRAC,MARCADOR_AREA_MAX_FRAC,MARCADOR_ASPECTO_MIN,MARCADOR_ASPECTO_MAX,MARCADOR_EXTENT_MIN,)

def _encontrar_contornos(img_bin):
    
    resultado = cv2.findContours(
        img_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if len(resultado) == 3:
        _, contornos, _ = resultado
    else:
        contornos, _ = resultado
    return contornos


def _candidatos_marcadores(img_bin, area_imagem):
   
    contornos = _encontrar_contornos(img_bin)

    candidatos = []

    for c in contornos:
        area = cv2.contourArea(c)

        if area < MARCADOR_AREA_MIN_FRAC * area_imagem:
            continue
        if area > MARCADOR_AREA_MAX_FRAC * area_imagem:
            continue

        x, y, w, h = cv2.boundingRect(c)
        if w == 0 or h == 0:
            continue

        aspecto = w / float(h)
        if aspecto < MARCADOR_ASPECTO_MIN or aspecto > MARCADOR_ASPECTO_MAX:
            continue

        extent = area / float(w * h)
        if extent < MARCADOR_EXTENT_MIN:
            continue

        cx = x + w / 2.0
        cy = y + h / 2.0
        candidatos.append((cx, cy))

    return candidatos


def _selecionar_4_cantos(candidatos, largura_img, altura_img):
    
    if len(candidatos) < 4:
        return None

    alvos = [
        (0.0, 0.0),                       # superior esquerdo
        (largura_img, 0.0),               # superior direito
        (largura_img, altura_img),        # inferior direito
        (0.0, altura_img),                # inferior esquerdo
    ]

    escolhidos = []
    for (tx, ty) in alvos:
        melhor = min(
            candidatos,
            key=lambda p: (p[0] - tx) ** 2 + (p[1] - ty) ** 2,
        )
        escolhidos.append(melhor)

    pts = np.array(escolhidos, dtype="float32")
    largura_detectada = max(
        np.linalg.norm(pts[0] - pts[1]), np.linalg.norm(pts[3] - pts[2])
    )
    altura_detectada = max(
        np.linalg.norm(pts[0] - pts[3]), np.linalg.norm(pts[1] - pts[2])
    )
    if largura_detectada < 0.2 * largura_img or altura_detectada < 0.2 * altura_img:
        return None

    return pts


def _binarizacoes_candidatas(cinza):
    
    _, otsu = cv2.threshold(
        cinza, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )
    yield otsu

    for limiar_fixo in (60, 80, 100):
        _, fixa = cv2.threshold(cinza, limiar_fixo, 255, cv2.THRESH_BINARY_INV)
        yield fixa


def extrairMaiorCtn(img):
    
    if img is None:
        return None, None

    altura_img, largura_img = img.shape[:2]
    area_imagem = float(largura_img * altura_img)

    cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cinza = cv2.GaussianBlur(cinza, (5, 5), 0)

    pontos = None
    for binaria in _binarizacoes_candidatas(cinza):
        candidatos = _candidatos_marcadores(binaria, area_imagem)
        pontos = _selecionar_4_cantos(candidatos, largura_img, altura_img)
        if pontos is not None:
            break

    if pontos is None:
        return None, None

    origem = pontos  # já está na ordem sup_esq, sup_dir, inf_dir, inf_esq
    destino = np.array(
        [
            [0, 0],
            [CANVAS_W - 1, 0],
            [CANVAS_W - 1, CANVAS_H - 1],
            [0, CANVAS_H - 1],
        ],
        dtype="float32",
    )

    matriz = cv2.getPerspectiveTransform(origem, destino)
    recorte = cv2.warpPerspective(img, matriz, (CANVAS_W, CANVAS_H))

    x, y, w, h = cv2.boundingRect(origem.astype("int32"))
    bbox = [x, y, w, h]

    return recorte, bbox