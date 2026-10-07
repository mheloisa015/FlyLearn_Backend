"""Gera a folha de respostas (A4, PDF) com o QR da versão da prova.

Usa folha_template.png (o mesmo arquivo da calibração) e cola o QR no lugar da
caixa tracejada "Código / QR de Identificação".
"""
import io
import uuid
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw

from qr_util import montar_payload

PASTA = Path(__file__).resolve().parent
TEMPLATE = PASTA / "folha_template.png"

# mesmas medidas de calibrar_folha.py (px do template)
QR_CENTRO_TEMPLATE = (560.5, 1330.0)
QR_LADO_TEMPLATE = 150.0          # 25 módulos x 6 px
CAIXA_TRACEJADA = (516, 1283, 605, 1376)   # área do retângulo tracejado a apagar

A4_300DPI = (2480, 3508)


def _matriz_qr(payload):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=0)
    qr.add_data(payload)
    qr.make(fit=True)
    return qr.get_matrix()


def folha_com_qr(identificador, largura=2480):
    """Imagem PIL (RGB) da folha, na largura pedida, com o QR da versão."""
    payload = montar_payload(identificador)
    base = Image.open(TEMPLATE).convert("RGB")
    f = largura / base.width
    base = base.resize((largura, int(round(base.height * f))), Image.LANCZOS)
    d = ImageDraw.Draw(base)

    x0, y0, x1, y1 = (v * f for v in CAIXA_TRACEJADA)
    d.rectangle([x0, y0, x1, y1], fill="white")           # apaga a caixa de espaço reservado

    matriz = _matriz_qr(payload)
    n = len(matriz)
    modulo = max(2, int(round(QR_LADO_TEMPLATE * f / n)))  # módulo inteiro em px = QR nítido
    lado = n * modulo
    qr_img = Image.new("1", (lado, lado), 1)
    qd = ImageDraw.Draw(qr_img)
    for r, linha in enumerate(matriz):
        for c, escuro in enumerate(linha):
            if escuro:
                qd.rectangle([c * modulo, r * modulo, (c + 1) * modulo - 1, (r + 1) * modulo - 1], fill=0)
    cx, cy = QR_CENTRO_TEMPLATE[0] * f, QR_CENTRO_TEMPLATE[1] * f
    base.paste(qr_img.convert("RGB"), (int(round(cx - lado / 2)), int(round(cy - lado / 2))))
    return base


def gerar_pdf_a4(identificador):
    """Bytes de um PDF A4 (300 dpi) com a folha centralizada na vertical."""
    folha = folha_com_qr(identificador, largura=A4_300DPI[0])
    pagina = Image.new("RGB", A4_300DPI, "white")
    pagina.paste(folha, (0, max(0, (A4_300DPI[1] - folha.height) // 2)))
    saida = io.BytesIO()
    pagina.save(saida, format="PDF", resolution=300.0, quality=95)
    return saida.getvalue()


def uuid_de_texto(texto):
    """Aceita UUID com ou sem hífens; levanta ValueError se inválido."""
    return uuid.UUID(str(texto))
