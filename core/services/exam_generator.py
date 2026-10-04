from __future__ import annotations

from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .qr_generator import qr_matrix

TEST_MESSAGE = "FlyLearn: QR code de teste"

QR_SIZE_MM = 40      # lado do QR
QR_BOTTOM_MM = 18    # distância da borda de baixo da folha até a base do QR


def generate_test_page(message: str = TEST_MESSAGE) -> bytes:
    """Gera um PDF A4 em branco com o QR code (com `message`) centralizado embaixo."""
    matrix = qr_matrix(message)
    n = len(matrix)

    page_w, _ = A4
    cell = QR_SIZE_MM * mm / n
    x0 = (page_w - QR_SIZE_MM * mm) / 2
    y0 = QR_BOTTOM_MM * mm

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle("FlyLearn - página de teste")

    pdf.setFillColorRGB(0, 0, 0)
    for row_index, row in enumerate(matrix):
        for col_index, is_dark in enumerate(row):
            if is_dark:
                # a linha 0 da matriz é o topo do QR; no PDF o eixo y cresce para cima
                y = y0 + (n - 1 - row_index) * cell
                pdf.rect(x0 + col_index * cell, y, cell + 0.15, cell + 0.15, stroke=0, fill=1)

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()