"""
Geometria da folha de respostas.

Este arquivo é a "fonte da verdade": o gerador do PDF (exam_generator) e o
leitor da foto (answer_reader) usam exatamente as mesmas posições. Se você
mudar qualquer número aqui, mude só aqui.

Todas as medidas estão em milímetros, com origem no canto superior esquerdo
de uma folha A4 em pé (210 x 297 mm).
"""

LETTERS = "ABCDE"
MAX_OPTIONS = len(LETTERS)

# Formato do texto gravado no QR code: FL1:<UUID do gabarito, 32 hex maiúsculos>
PAYLOAD_PREFIX = "FL1"

PAGE_W_MM = 210
PAGE_H_MM = 297

# Resolução da imagem "achatada" que o leitor usa (10 px por mm = 2100 x 2970 px)
PX_PER_MM = 10

# --- Marcadores ArUco nos 4 cantos -----------------------------------------
# ids: 0 = topo esquerdo, 1 = topo direito, 2 = base direita, 3 = base esquerda
ARUCO_DICT_NAME = "DICT_4X4_50"
MARKER_SIZE_MM = 12
MARKER_MARGIN_MM = 8
_c = MARKER_MARGIN_MM + MARKER_SIZE_MM / 2
MARKER_CENTERS_MM = {
    0: (_c, _c),
    1: (PAGE_W_MM - _c, _c),
    2: (PAGE_W_MM - _c, PAGE_H_MM - _c),
    3: (_c, PAGE_H_MM - _c),
}

# --- QR code (canto superior direito, abaixo do marcador) -------------------
QR_X_MM = 150
QR_Y_MM = 28
QR_SIZE_MM = 35

# --- Grade de bolhas --------------------------------------------------------
GRID_LEFT_MM = 20
GRID_TOP_MM = 75
ROW_H_MM = 8
ROWS_PER_COL = 20
COL_W_MM = 56
LABEL_W_MM = 10      # espaço do número da questão
BUBBLE_DX_MM = 8     # distância entre uma bolha e a próxima
BUBBLE_R_MM = 2.8
MAX_COLS = 3
MAX_QUESTIONS = ROWS_PER_COL * MAX_COLS  # 60


def bubble_center_mm(question_index: int, option_index: int) -> tuple[float, float]:
    """Centro (x, y) da bolha. Os dois índices começam em 0."""
    col, row = divmod(question_index, ROWS_PER_COL)
    x = GRID_LEFT_MM + col * COL_W_MM + LABEL_W_MM + option_index * BUBBLE_DX_MM
    y = GRID_TOP_MM + row * ROW_H_MM + ROW_H_MM / 2
    return x, y