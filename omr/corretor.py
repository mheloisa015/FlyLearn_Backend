import numpy as np


_MASCARAS = {}


def _mascara_disco(lado):
    """Disco inscrito no campo quadrado: ignora cantos e o anel impresso da bolha."""
    if lado not in _MASCARAS:
        r = lado / 2.0
        yy, xx = np.ogrid[:lado, :lado]
        _MASCARAS[lado] = (((yy - r + 0.5) ** 2 + (xx - r + 0.5) ** 2) <= r * r)
    return _MASCARAS[lado]


def lerRespostas(imgTh, campos, resp, limiar=45, margem_dupla=15):
    """imgTh: imagem binária do canvas (tinta = 255). Cada campo é um quadrado (x, y, w, h)
    centrado numa bolha; só o disco interno conta. percentuais = % de tinta no disco.
    Uma bolha VAZIA já tem ~10-22% por causa da letra impressa; preenchida passa de ~80%."""
    resultado_por_questao = []

    for questao in range(10):
        percentuais = []

        for alternativa in range(5):
            id_campo = questao * 5 + alternativa
            x, y, w, h = campos[id_campo]
            campo = imgTh[max(y, 0):y + h, max(x, 0):x + w]

            if campo.shape != (h, w):          # campo cortado pela borda do canvas
                percentuais.append(0.0)
                continue

            disco = _mascara_disco(w)
            percentual = round(float((campo[disco] > 0).mean()) * 100, 2)
            percentuais.append(percentual)

        ordenado = sorted(range(5), key=lambda i: percentuais[i], reverse=True)
        maior_idx = ordenado[0]
        maior_percentual = percentuais[maior_idx]
        segundo_percentual = percentuais[ordenado[1]]

        if maior_percentual < limiar:
            resposta = "BRANCO"
        elif (
            segundo_percentual >= limiar
            and (maior_percentual - segundo_percentual) < margem_dupla
        ):
            resposta = "ANULADA"
        else:
            letra = "ABCDE"[maior_idx]
            resposta = f"{questao + 1}-{letra}"

        resultado_por_questao.append(
            {
                "questao": questao + 1,
                "resposta": resposta,
                "percentuais": percentuais,
            }
        )

    return resultado_por_questao


def avaliarRespostas(
    imgTh, campos, resp, respostaCorreta, limiar=45, margem_dupla=15
):
    leitura = lerRespostas(imgTh, campos, resp, limiar, margem_dupla)

    linhas = []
    acertos = 0
    erros = 0
    brancos = 0
    anuladas = 0

    for item in leitura:
        questao = item["questao"]
        marcada = item["resposta"]
        correta = respostaCorreta[questao - 1]
        correta_letra = correta.split("-")[1]

        if marcada == "BRANCO":
            brancos += 1
            situacao = "BRANCO"
            marcada_letra = "-"
        elif marcada == "ANULADA":
            anuladas += 1
            situacao = "ANULADA"
            marcada_letra = "-"
        else:
            marcada_letra = marcada.split("-")[1]
            if marcada == correta:
                acertos += 1
                situacao = "CORRETA"
            else:
                erros += 1
                situacao = "INCORRETA"

        linhas.append(
            {
                "questao": questao,
                "resposta_detectada": marcada_letra,
                "resposta_correta": correta_letra,
                "situacao": situacao,
                "percentuais": item["percentuais"],
            }
        )

    nota = round(acertos * (10.0 / len(respostaCorreta)), 2)

    resumo = {
        "acertos": acertos,
        "erros": erros,
        "brancos": brancos,
        "anuladas": anuladas,
        "total": len(respostaCorreta),
        "nota": nota,
    }

    return linhas, resumo