import cv2


def lerRespostas(imgTh, campos, resp, limiar=15, margem_dupla=8):
    
    resultado_por_questao = []

    for questao in range(10):
        percentuais = []

        for alternativa in range(5):
            id_campo = questao * 5 + alternativa
            x, y, w, h = campos[id_campo]
            campo = imgTh[y:y + h, x:x + w]

            if campo.size == 0:
                percentuais.append(0.0)
                continue

            tamanho = campo.shape[0] * campo.shape[1]
            pretos = cv2.countNonZero(campo)
            percentual = round((pretos / tamanho) * 100, 2)
            percentuais.append(percentual)

        ordenado = sorted(
            range(5), key=lambda i: percentuais[i], reverse=True
        )
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
    imgTh, campos, resp, respostaCorreta, limiar=15, margem_dupla=8
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