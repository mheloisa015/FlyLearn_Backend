import base64
import json
import os
import pickle
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, Response, request
from flask_cors import CORS

import corretor
import extrairGabarito as exG
import gerar_folha
import qr_util
from omr_config import CENTROS, RAIO_ANEL

PASTA_OMR = Path(__file__).resolve().parent

with open(PASTA_OMR / "campos.pkl", "rb") as arquivo:
    campos = pickle.load(arquivo)

with open(PASTA_OMR / "resp.pkl", "rb") as arquivo:
    resp = pickle.load(arquivo)

# gabarito de teste: usado só quando o front não manda o gabarito
respostaCorreta = ["1-A", "2-C", "3-B", "4-D", "5-A", "6-B", "7-C", "8-E", "9-A", "10-D"]

# bolha vazia já tem 10-22% de tinta (a letra impressa); preenchida passa de ~80%
LIMIAR_PREENCHIMENTO = 20   # % de tinta no disco da bolha p/ contar como marcada (rabiscos ~28-41%, vazia <10%)
MARGEM_DUPLA_MARCACAO = 15
LADO_MAX = 2200   # maior lado da foto (px); acima disso reduz (mantém o QR legível)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB

ORIGENS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",") if o.strip()]
CORS(app, resources={r"/*": {"origins": ORIGENS}})


@app.errorhandler(413)
def arquivo_grande(_erro):
    return {"ok": False, "mensagem": "Imagem muito grande (maximo 8 MB)."}, 413


@app.route("/")
def raiz():
    return {"servico": "FlyLearn OMR", "ok": True}


@app.route("/health")
def health():
    return {"ok": True}


def _ler_gabarito(bruto):
    """Converte '["A","C",...]' em ['1-A','2-C',...]. Retorna None se invalido."""
    if not bruto:
        return respostaCorreta
    try:
        letras = json.loads(bruto)
    except ValueError:
        return None
    if not isinstance(letras, list) or len(letras) != len(respostaCorreta):
        return None
    letras = [str(l).strip().upper() for l in letras]
    if any(l not in ("A", "B", "C", "D", "E") for l in letras):
        return None
    return [f"{i + 1}-{l}" for i, l in enumerate(letras)]


def _imagem_debug(folha, linhas):
    """Canvas com as bolhas desenhadas: verde = lida como marcada, cinza = vazia."""
    img = folha.recorte.copy()
    for q, linha in enumerate(linhas):
        letra = linha["resposta_detectada"]
        for a in range(5):
            cx, cy = CENTROS[q * 5 + a]
            marcada = letra == "ABCDE"[a]
            cor = (0, 200, 0) if marcada else (160, 160, 160)
            cv2.circle(img, (int(cx), int(cy)), int(RAIO_ANEL), cor, 3 if marcada else 1)
    img = cv2.resize(img, None, fx=0.6, fy=0.6, interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 75])
    return "data:image/jpeg;base64," + base64.b64encode(buf).decode() if ok else None


@app.route("/corrigir", methods=["POST"])
def corrigir():
    arquivo = request.files.get("foto") or request.files.get("imagem")
    if arquivo is None:
        return {"ok": False, "mensagem": "Nenhuma imagem recebida."}, 400

    gabarito_correto = _ler_gabarito(request.form.get("gabarito"))
    if gabarito_correto is None:
        return {
            "ok": False,
            "mensagem": "Gabarito invalido. Envie uma lista JSON com 10 letras (A-E).",
        }, 400

    bytes_imagem = np.frombuffer(arquivo.read(), dtype=np.uint8)
    imagem = cv2.imdecode(bytes_imagem, cv2.IMREAD_COLOR)

    if imagem is None:
        return {"ok": False, "mensagem": "Nao foi possivel ler a imagem enviada."}, 400

    altura, largura = imagem.shape[:2]
    if max(altura, largura) > LADO_MAX:
        escala = LADO_MAX / float(max(altura, largura))
        imagem = cv2.resize(
            imagem, (int(largura * escala), int(altura * escala)), interpolation=cv2.INTER_AREA
        )

    folha, n_candidatos = exG.localizar_folha(imagem)

    if folha is None:
        return {
            "ok": False,
            "mensagem": (
                "Nao foi possivel localizar a folha. Enquadre a folha INTEIRA, com os 4 "
                "quadrados pretos dos cantos visiveis, bem iluminada e sem reflexo."
            ),
            "diagnostico": {"candidatos_a_marcador": n_candidatos},
        }

    imgTh = exG.binarizar(folha.recorte)
    linhas, resumo = corretor.avaliarRespostas(
        imgTh,
        campos,
        resp,
        gabarito_correto,
        limiar=LIMIAR_PREENCHIMENTO,
        margem_dupla=MARGEM_DUPLA_MARCACAO,
    )

    texto_qr = qr_util.ler_qr(imagem, folha.matriz)
    identificador = qr_util.interpretar_payload(texto_qr)
    qr = {
        "lido": texto_qr is not None,
        "texto": texto_qr,
        "uuid": str(identificador) if identificador else None,
    }

    resposta = {"ok": True, "linhas": linhas, "resumo": resumo, "qr": qr}
    if request.args.get("debug") or request.form.get("debug"):
        resposta["debug_img"] = _imagem_debug(folha, linhas)
        resposta["diagnostico"] = {
            "score_aneis": round(folha.score_aneis, 3),
            "candidatos_a_marcador": n_candidatos,
        }
    return resposta


@app.route("/folha/<identificador>.pdf")
def folha_pdf(identificador):
    """PDF A4 da folha de respostas com o QR da versão (UUID com ou sem hífens)."""
    try:
        uid = gerar_folha.uuid_de_texto(identificador)
    except ValueError:
        return {"ok": False, "mensagem": "Identificador invalido."}, 400
    try:
        pdf = gerar_folha.gerar_pdf_a4(uid)
    except FileNotFoundError:
        return {"ok": False, "mensagem": "folha_template.png nao encontrado no servidor (omr/)."}, 503
    return Response(
        pdf,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'inline; filename="folha-{uid.hex[:8]}.pdf"'},
    )


if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta, debug=False)
