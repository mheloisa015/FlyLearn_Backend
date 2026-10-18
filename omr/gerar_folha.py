"""Gera a folha de respostas (A4, PDF) com o QR da versão da prova.

Usa o modelo da quantidade de questões (folha_template.png = 10 questões,
folha_template_20.png = 20 questões) e cola o QR no lugar da caixa tracejada
"Código / QR de Identificação".
"""
import io
import uuid
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw

from qr_util import montar_payload

PASTA = Path(__file__).resolve().parent

# Um modelo por quantidade de questões. Medidas em px do próprio PNG do modelo:
#   arquivo        : imagem da folha em branco (com a caixa tracejada do QR)
#   qr_centro      : centro da caixa do QR
#   qr_lado        : lado do QR colado (25 módulos x N px)
#   caixa          : retângulo da caixa tracejada, a ser apagado antes de colar o QR
MODELOS = {
    10: dict(arquivo="folha_template.png", qr_centro=(560.5, 1330.0), qr_lado=150.0,
             caixa=(516, 1283, 605, 1376)),
    20: dict(arquivo="folha_template_20.png", qr_centro=(1234.5, 2983.5), qr_lado=175.0,
             caixa=(1124, 2876, 1346, 3092)),   # folha de 2475 x 3202 px
}

A4_300DPI = (2480, 3508)


def _matriz_qr(payload):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=0)
    qr.add_data(payload)
    qr.make(fit=True)
    return qr.get_matrix()


def folha_com_qr(identificador, n_questoes=10, largura=2480):
    """Imagem PIL (RGB) da folha de n_questoes (10 ou 20), na largura pedida, com o QR da versão."""
    if n_questoes not in MODELOS:
        raise ValueError(f"Folha de {n_questoes} questões não existe (use 10 ou 20).")
    m = MODELOS[n_questoes]
    payload = montar_payload(identificador)
    base = Image.open(PASTA / m["arquivo"]).convert("RGB")
    f = largura / base.width
    base = base.resize((largura, int(round(base.height * f))), Image.LANCZOS)
    d = ImageDraw.Draw(base)

    x0, y0, x1, y1 = (v * f for v in m["caixa"])
    d.rectangle([x0, y0, x1, y1], fill="white")           # apaga a caixa de espaço reservado

    matriz = _matriz_qr(payload)
    n = len(matriz)
    modulo = max(2, int(round(m["qr_lado"] * f / n)))     # módulo inteiro em px = QR nítido
    lado = n * modulo
    qr_img = Image.new("1", (lado, lado), 1)
    qd = ImageDraw.Draw(qr_img)
    for r, linha in enumerate(matriz):
        for c, escuro in enumerate(linha):
            if escuro:
                qd.rectangle([c * modulo, r * modulo, (c + 1) * modulo - 1, (r + 1) * modulo - 1], fill=0)
    cx, cy = m["qr_centro"][0] * f, m["qr_centro"][1] * f
    base.paste(qr_img.convert("RGB"), (int(round(cx - lado / 2)), int(round(cy - lado / 2))))
    return base


def gerar_pdf_a4(identificador, n_questoes=10):
    """Bytes de um PDF A4 (300 dpi) com a folha centralizada na vertical."""
    folha = folha_com_qr(identificador, n_questoes, largura=A4_300DPI[0])
    pagina = Image.new("RGB", A4_300DPI, "white")
    pagina.paste(folha, (0, max(0, (A4_300DPI[1] - folha.height) // 2)))
    saida = io.BytesIO()
    pagina.save(saida, format="PDF", resolution=300.0, quality=95)
    return saida.getvalue()


def uuid_de_texto(texto):
    """Aceita UUID com ou sem hífens; levanta ValueError se inválido."""
    return uuid.UUID(str(texto))