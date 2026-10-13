"""Configuração do layout da folha de respostas (coordenadas no "canvas" 1000 x 1323).

O canvas é a folha já endireitada (homografia a partir dos 4 marcadores quadrados dos cantos).
"""

CANVAS_W = 1000
CANVAS_H = 1323

# Posição relativa (fração do canvas) do centro das bolhas.
COLUNAS_ESQUERDA = [0.0840, 0.1656, 0.2476, 0.3290, 0.4114]   # questões 1-5   (A..E)
COLUNAS_DIREITA = [0.6014, 0.6840, 0.7645, 0.8459, 0.9289]    # questões 6-10  (A..E)
LINHAS = [0.6076, 0.6720, 0.7368, 0.8020, 0.8674]             # 5 linhas por coluna

# Lado do quadrado (px) usado para medir o preenchimento de cada bolha (ver gerarCampos.py).
LADO_CAMPO = 60

# Raio (px do canvas) do anel impresso de cada bolha (medido na folha real: ~20-21 px).
RAIO_ANEL = 20


def _centros():
    """Centro (x, y) de cada uma das 50 bolhas, na ordem questao*5 + alternativa."""
    centros = []
    for questao in range(10):
        colunas = COLUNAS_DIREITA if questao >= 5 else COLUNAS_ESQUERDA
        y = LINHAS[questao % 5] * CANVAS_H
        for alternativa in range(5):
            centros.append((colunas[alternativa] * CANVAS_W, y))
    return centros


CENTROS = _centros()

# QR de identificação da versão da prova (coordenadas do canvas).
# Posição medida na caixa tracejada "Código / QR de Identificação" da folha real.
# Se o QR não for lido por essa posição, qr_util.ler_qr procura o QR na foto inteira.
QR_CENTRO = (499.0, 1277.0)
QR_LADO = 80.0

# Parâmetros de detecção de marcadores (não usados por marcadores.py atualmente).
MARCADOR_AREA_MIN_FRAC = 0.00005
MARCADOR_AREA_MAX_FRAC = 0.02
MARCADOR_ASPECTO_MIN = 0.75
MARCADOR_ASPECTO_MAX = 1.25
MARCADOR_EXTENT_MIN = 0.82
