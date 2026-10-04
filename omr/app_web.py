import json
import os
import pickle
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, request
from flask_cors import CORS

import extrairGabarito as exG
import corretor

PASTA_OMR = Path(__file__).resolve().parent

with open(PASTA_OMR / "campos.pkl", "rb") as arquivo:
    campos = pickle.load(arquivo)

with open(PASTA_OMR / "resp.pkl", "rb") as arquivo:
    resp = pickle.load(arquivo)

respostaCorreta = ["1-A", "2-C", "3-B", "4-D", "5-A", "6-B", "7-C", "8-E", "9-A", "10-D"]

LIMIAR_PREENCHIMENTO = 15
MARGEM_DUPLA_MARCACAO = 8
LARGURA_MAX = 1600

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


@app.route("/corrigir", methods=["POST"])
def corrigir():
    arquivo = request.files.get("foto")
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
    if largura > LARGURA_MAX:
        escala = LARGURA_MAX / float(largura)
        imagem = cv2.resize(
            imagem, (LARGURA_MAX, int(altura * escala)), interpolation=cv2.INTER_AREA
        )

    gabarito, bbox = exG.extrairMaiorCtn(imagem)

    if gabarito is None:
        return {
            "ok": False,
            "mensagem": (
                "Nao foi possivel localizar a folha (4 marcadores dos "
                "cantos). Tente tirar a foto com a folha inteira "
                "visivel, bem iluminada e evitando reflexos."
            ),
        }

    imgGray = cv2.cvtColor(gabarito, cv2.COLOR_BGR2GRAY)
    _, imgTh = cv2.threshold(imgGray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    linhas, resumo = corretor.avaliarRespostas(
        imgTh,
        campos,
        resp,
        gabarito_correto,
        limiar=LIMIAR_PREENCHIMENTO,
        margem_dupla=MARGEM_DUPLA_MARCACAO,
    )

    return {"ok": True, "linhas": linhas, "resumo": resumo}


if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta, debug=False)