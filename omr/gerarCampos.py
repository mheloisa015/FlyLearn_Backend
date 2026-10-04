import pickle

from omr_config import (CANVAS_W,CANVAS_H,COLUNAS_ESQUERDA,COLUNAS_DIREITA,LINHAS,LADO_CAMPO,)

campos = []

num_questoes = 10
num_alternativas = 5


for questao in range(num_questoes):

    linha = questao % 5
    grupo_direita = questao >= 5

    colunas = COLUNAS_DIREITA if grupo_direita else COLUNAS_ESQUERDA
    y_centro = LINHAS[linha] * CANVAS_H

    for alternativa in range(num_alternativas):

        x_centro = colunas[alternativa] * CANVAS_W

        x = int(round(x_centro - LADO_CAMPO / 2))
        y = int(round(y_centro - LADO_CAMPO / 2))
        w = LADO_CAMPO
        h = LADO_CAMPO

        campos.append((x, y, w, h))

with open("campos.pkl", "wb") as arquivo:
    pickle.dump(campos, arquivo)

print("campos.pkl criado!")
print("Quantidade:", len(campos))