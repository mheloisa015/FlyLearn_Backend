"""Configuração do layout das folhas de respostas.

A folha é gerada no front (app.js -> folhaRespostasPgApi), em A4, com medidas em mm. Este arquivo
deriva TUDO dessas mesmas medidas, então se o layout do front mudar, mude as constantes de "medidas
do front" abaixo (e só elas).

O "canvas" é a folha já endireitada (homografia a partir dos 4 marcadores quadrados dos cantos).
Os pontos de referência são os CENTROS dos marcadores: (0,0) = centro do marcador superior esquerdo e
(CANVAS_W-1, CANVAS_H-1) = centro do marcador inferior direito. A escala é a mesma em x e y
(PX_POR_MM), então as bolhas continuam circulares no canvas.

Existem dois modelos: 10 questões (2 colunas x 5 linhas) e 20 questões (2 colunas x 10 linhas).
"""
from collections import namedtuple

# ----------------------------------------------------------------------------------------------
# Medidas do front (mm, página A4) — copiadas de app.js / folhaRespostasPgApi
# ----------------------------------------------------------------------------------------------
MARCADOR_X = (11.5, 198.5)     # centros dos quadrados 7x7 mm (left 8 / 195 + 3,5)
MARCADOR_Y = (11.5, 285.5)     # (top 8 / 282 + 3,5)

TOPO_LINHAS = 126.0            # top0
X0_COLUNAS = (14.0, 108.0)     # x0 de cada coluna de questões
X_PRIMEIRA_BOLHA = 21.0        # x0 + 21 = centro da bolha A
PASSO_BOLHA = 14.0             # distância A->B->C...
PASSO_LINHA = {10: 18.0, 20: 11.5}      # pitch
DIAMETRO_BOLHA = {10: 10.0, 20: 8.0}    # dn (diâmetro externo da bolha impressa)
BORDA_BOLHA = 0.3              # espessura do traço do anel

QUANTIDADES = (10, 20)

# ----------------------------------------------------------------------------------------------
# Canvas
# ----------------------------------------------------------------------------------------------
CANVAS_W = 1000
PX_POR_MM = (CANVAS_W - 1) / (MARCADOR_X[1] - MARCADOR_X[0])
CANVAS_H = int(round(PX_POR_MM * (MARCADOR_Y[1] - MARCADOR_Y[0])) + 1)    # ~1466


def _x(mm):
    return (mm - MARCADOR_X[0]) * PX_POR_MM


def _y(mm):
    return (mm - MARCADOR_Y[0]) * PX_POR_MM


# Raio (px do canvas) da linha do anel impresso de cada bolha.
RAIO_ANEL_POR_QTD = {n: (DIAMETRO_BOLHA[n] / 2 - BORDA_BOLHA / 2) * PX_POR_MM for n in QUANTIDADES}
RAIO_ANEL = RAIO_ANEL_POR_QTD[10]   # compatibilidade

# Fração do raio do anel usada como disco de leitura (fica dentro do anel, sem encostar nele).
FRACAO_DISCO = 0.80
LADO_CAMPO_POR_QTD = {n: int(2 * round(RAIO_ANEL_POR_QTD[n] * FRACAO_DISCO)) for n in QUANTIDADES}
LADO_CAMPO = LADO_CAMPO_POR_QTD[10]   # compatibilidade

Layout = namedtuple("Layout", "n_questoes por_coluna centros lado_campo raio_anel")


def _centros(n):
    """Centro (x, y) de cada bolha, na ordem questao*5 + alternativa."""
    por_coluna = n // 2
    passo = PASSO_LINHA[n]
    centros = []
    for questao in range(n):
        coluna = 1 if questao >= por_coluna else 0
        linha = questao % por_coluna
        y_mm = TOPO_LINHAS + linha * passo + passo / 2 - 1
        for alternativa in range(5):
            x_mm = X0_COLUNAS[coluna] + X_PRIMEIRA_BOLHA + PASSO_BOLHA * alternativa
            centros.append((_x(x_mm), _y(y_mm)))
    return centros


LAYOUTS = {
    n: Layout(n, n // 2, _centros(n), LADO_CAMPO_POR_QTD[n], RAIO_ANEL_POR_QTD[n]) for n in QUANTIDADES
}


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

# QR de identificação da versão da prova — mesma posição nas duas folhas (app.js: .qr left 93 / top 246,
# caixa 24 mm, imagem 21 mm). Se o QR não for lido por essa posição, qr_util.ler_qr procura na foto inteira.
QR_CENTRO = (_x(93 + 12), _y(246 + 12))
QR_LADO = 21 * PX_POR_MM

# Parâmetros de detecção de marcadores (não usados por marcadores.py atualmente).
MARCADOR_AREA_MIN_FRAC = 0.00005
MARCADOR_AREA_MAX_FRAC = 0.02
MARCADOR_ASPECTO_MIN = 0.75
MARCADOR_ASPECTO_MAX = 1.25
MARCADOR_EXTENT_MIN = 0.82
