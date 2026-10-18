"""Configuração do layout das folhas de respostas (coordenadas no "canvas" 1000 x 1323).

O canvas é a folha já endireitada (homografia a partir dos 4 marcadores quadrados dos cantos).
Existem dois modelos de folha: 10 questões (2 colunas x 5 linhas) e 20 questões (2 colunas x 10 linhas).
As colunas A..E são as mesmas nos dois; só muda a quantidade e a posição das linhas.
"""
from collections import namedtuple

CANVAS_W = 1000
CANVAS_H = 1323

# Quantidades de questões que o sistema sabe ler (cada uma tem um modelo de folha).
QUANTIDADES = (10, 20)

# Posição relativa (fração do canvas) do centro das bolhas.
COLUNAS_ESQUERDA = [0.0840, 0.1656, 0.2476, 0.3290, 0.4114]   # 1ª metade das questões (A..E)
COLUNAS_DIREITA = [0.6014, 0.6840, 0.7645, 0.8459, 0.9289]    # 2ª metade das questões (A..E)

LINHAS_POR_QTD = {
    10: [0.6076, 0.6720, 0.7368, 0.8020, 0.8674],                                          # 5 linhas por coluna
    20: [0.4950, 0.5373, 0.5796, 0.6219, 0.6643, 0.7066, 0.7489, 0.7912, 0.8336, 0.8759],  # 10 linhas por coluna
}

# Lado do quadrado (px) usado para medir o preenchimento de cada bolha.
# Na folha de 20 as linhas ficam mais juntas (~56 px) e o tracejado entre elas está a ~28 px do centro:
# o campo é menor para o disco de leitura não encostar na linha tracejada.
LADO_CAMPO_POR_QTD = {10: 60, 20: 52}
LADO_CAMPO = LADO_CAMPO_POR_QTD[10]   # compatibilidade

# Raio (px do canvas) do anel impresso de cada bolha (medido na folha real: ~20-21 px).
RAIO_ANEL = 20

Layout = namedtuple("Layout", "n_questoes por_coluna centros lado_campo")


def _centros(n):
    """Centro (x, y) de cada bolha, na ordem questao*5 + alternativa."""
    por_coluna = n // 2
    linhas = LINHAS_POR_QTD[n]
    centros = []
    for questao in range(n):
        colunas = COLUNAS_DIREITA if questao >= por_coluna else COLUNAS_ESQUERDA
        y = linhas[questao % por_coluna] * CANVAS_H
        for alternativa in range(5):
            centros.append((colunas[alternativa] * CANVAS_W, y))
    return centros


LAYOUTS = {n: Layout(n, n // 2, _centros(n), LADO_CAMPO_POR_QTD[n]) for n in QUANTIDADES}


def layout(n):
    if n not in LAYOUTS:
        raise ValueError(f"Folha de {n} questões não suportada (use {' ou '.join(map(str, QUANTIDADES))}).")
    return LAYOUTS[n]


def campos(n):
    """Quadrados (x, y, w, h) de leitura de cada bolha, na ordem questao*5 + alternativa."""
    lay = layout(n)
    lado = lay.lado_campo
    return [(int(round(cx - lado / 2)), int(round(cy - lado / 2)), lado, lado) for cx, cy in lay.centros]


CENTROS = LAYOUTS[10].centros   # compatibilidade com código antigo (folha de 10)

# QR de identificação da versão da prova (coordenadas do canvas) — mesma posição nas duas folhas.
# Se o QR não for lido por essa posição, qr_util.ler_qr procura o QR na foto inteira.
QR_CENTRO = (499.0, 1277.0)
QR_LADO = 80.0

# Parâmetros de detecção de marcadores (não usados por marcadores.py atualmente).
MARCADOR_AREA_MIN_FRAC = 0.00005
MARCADOR_AREA_MAX_FRAC = 0.02
MARCADOR_ASPECTO_MIN = 0.75
MARCADOR_ASPECTO_MAX = 1.25
MARCADOR_EXTENT_MIN = 0.82