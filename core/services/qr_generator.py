from __future__ import annotations

import uuid
from dataclasses import dataclass
from io import BytesIO

import qrcode

PAYLOAD_PREFIX = "FL1"  # antes vinha de sheet_layout.py (removido: só servia ao gerador de PDF por bolhas)


@dataclass(frozen=True)
class GeneratedQR:
    identifier: uuid.UUID   # guarde no gabarito (UUIDField)
    payload: str            # ex.: "FL1:3F2504E04F8911D39A0C0305E82C3301" -> texto dentro do QR
    png: bytes              # imagem PNG do QR (com margem branca)


def generate_identifier() -> uuid.UUID:
    """UUID aleatório (versão 4) para um novo gabarito."""
    return uuid.uuid4()


def build_payload(identifier: uuid.UUID | str) -> str:
    """Texto gravado no QR: prefixo + UUID em 32 caracteres hexadecimais MAIÚSCULOS, sem hífens."""
    return f"{PAYLOAD_PREFIX}:{uuid.UUID(str(identifier)).hex.upper()}"


def qr_png_bytes(payload: str, box_size: int = 10) -> bytes:
    """PNG do QR, com a margem branca de 4 módulos exigida pelo padrão."""
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    buffer = BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(buffer, format="PNG")
    return buffer.getvalue()


def generate_qr(identifier: uuid.UUID | str | None = None) -> GeneratedQR:
    """Ponto de entrada: cria (ou reaproveita) o UUID e gera o QR."""
    identifier = generate_identifier() if identifier is None else uuid.UUID(str(identifier))
    payload = build_payload(identifier)
    return GeneratedQR(identifier=identifier, payload=payload, png=qr_png_bytes(payload))