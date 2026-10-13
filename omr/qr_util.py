"""QR da folha: leitura na foto. Formato do texto: FL1:<UUID em 32 hex MAIÚSCULOS>."""
import re
import uuid

import cv2
import numpy as np

from omr_config import QR_CENTRO, QR_LADO

PREFIXO = "FL1"
_RE = re.compile(r"^FL1:([0-9A-Fa-f]{32})$")
ESCALA = 3          # a região do QR é ampliada 3x antes de decodificar


def montar_payload(identificador):
    return f"{PREFIXO}:{uuid.UUID(str(identificador)).hex.upper()}"


def interpretar_payload(texto):
    """'FL1:3F25...' -> uuid.UUID (ou None se não for um QR do FlyLearn)."""
    m = _RE.match((texto or "").strip())
    return uuid.UUID(m.group(1)) if m else None


def _detectores():
    ds = [cv2.QRCodeDetector()]
    aruco = getattr(cv2, "QRCodeDetectorAruco", None)
    if aruco is not None:
        ds.insert(0, aruco())
    return ds


def _tentar(cinza):
    variantes = [cinza]
    _, otsu = cv2.threshold(cinza, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variantes.append(otsu)
    variantes.append(cv2.GaussianBlur(cinza, (0, 0), 1.2))
    # foto tremida: realça bordas e binariza com limiar local
    nitida = cv2.addWeighted(cinza, 2.2, cv2.GaussianBlur(cinza, (0, 0), 4), -1.2, 0)
    variantes.append(nitida)
    variantes.append(cv2.adaptiveThreshold(nitida, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 61, 8))
    for v in variantes:
        v = cv2.copyMakeBorder(v, 30, 30, 30, 30, cv2.BORDER_CONSTANT, value=255)   # zona de silêncio
        for det in _detectores():
            try:
                texto, _, _ = det.detectAndDecode(v)
            except cv2.error:
                continue
            if texto:
                return texto
    return None


def ler_qr(img_bgr, matriz):
    """Lê o QR usando a mesma homografia da folha (foto -> canvas). Devolve o texto ou None."""
    cx, cy = QR_CENTRO
    for margem in (0.85, 1.25):                       # tenta um recorte justo e outro mais folgado
        meia = QR_LADO * margem
        S = np.array([[ESCALA, 0, -ESCALA * (cx - meia)],
                      [0, ESCALA, -ESCALA * (cy - meia)],
                      [0, 0, 1]], dtype="float64")
        lado = int(round(2 * meia * ESCALA))
        recorte = cv2.warpPerspective(img_bgr, S @ matriz, (lado, lado), flags=cv2.INTER_CUBIC,
                                      borderMode=cv2.BORDER_REPLICATE)
        cinza = cv2.cvtColor(recorte, cv2.COLOR_BGR2GRAY)
        texto = _tentar(cinza)
        if texto:
            return texto
    # plano B: posição do QR fora do esperado -> procura o QR na foto inteira
    maior = max(img_bgr.shape[:2])
    for lado in (1600, 1100):
        f = min(1.0, lado / float(maior))
        reduzida = cv2.resize(img_bgr, None, fx=f, fy=f, interpolation=cv2.INTER_AREA) if f < 1.0 else img_bgr
        texto = _tentar(cv2.cvtColor(reduzida, cv2.COLOR_BGR2GRAY))
        if texto:
            return texto
    return None
