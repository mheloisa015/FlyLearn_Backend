import base64
import json
import os
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, Response, request
from flask_cors import CORS

import corretor
import extrairGabarito as exG
import gerar_folha
import qr_util
from omr_config import LAYOUTS, QUANTIDADES, campos as campos_de

PASTA_OMR = Path(__file__).resolve().parent

# campos de leitura e rótulos de cada modelo de folha (10 e 20 questões), calculados do omr_config.py
CAMPOS = {n: campos_de(n) for n in QUANTIDADES}
RESP = {n: [f"{q}-{a}" for q in range(1, n + 1) for a in "ABCDE"] for n in QUANTIDADES}

# gabarito de teste: usado só quando o front não manda o gabarito (repete o padrão até completar n questões)
_PADRAO_TESTE = ["A", "C", "B", "D", "A", "B", "C", "E", "A", "D"]


def gabarito_teste(n):
    return [f"{i + 1}-{_PADRAO_TESTE[i % len(_PADRAO_TESTE)]}" for i in range(n)]


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
    """Converte '["A","C",...]' em ['1-A','2-C',...]. Retorna (gabarito, n) ou (None, None) se inválido.
    Sem gabarito no pedido devolve (None, 0): aí vale o gabarito de teste do modelo de folha detectado."""
    if not bruto:
        return None, 0
    try:
        letras = json.loads(bruto)
    except ValueError:
        return None, None
    if not isinstance(letras, list) or len(letras) not in QUANTIDADES:
        return None, None
    letras = [str(l).strip().upper() for l in letras]
    if any(l not in ("A", "B", "C", "D", "E") for l in letras):
        return None, None
    return [f"{i + 1}-{l}" for i, l in enumerate(letras)], len(letras)


def _imagem_debug(folha, linhas):
    """Canvas com as bolhas desenhadas: verde = lida como marcada, cinza = vazia."""
    img = folha.recorte.copy()
    lay = LAYOUTS[folha.n_questoes]
    centros = lay.centros
    for q, linha in enumerate(linhas):
        letra = linha["resposta_detectada"]
        for a in range(5):
            cx, cy = centros[q * 5 + a]
            marcada = letra == "ABCDE"[a]
            cor = (0, 200, 0) if marcada else (160, 160, 160)
            cv2.circle(img, (int(cx), int(cy)), int(lay.raio_anel), cor, 3 if marcada else 1)
    img = cv2.resize(img, None, fx=0.6, fy=0.6, interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 75])
    return "data:image/jpeg;base64," + base64.b64encode(buf).decode() if ok else None


@app.route("/corrigir", methods=["POST"])
def corrigir():
    arquivo = request.files.get("foto") or request.files.get("imagem")
    if arquivo is None:
        return {"ok": False, "mensagem": "Nenhuma imagem recebida."}, 400

    gabarito_correto, n_gabarito = _ler_gabarito(request.form.get("gabarito"))
    if n_gabarito is None:
        return {
            "ok": False,
            "mensagem": "Gabarito invalido. Envie uma lista JSON com 10 ou 20 letras (A-E).",
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

    folha, n_candidatos = exG.localizar_folha(imagem)   # detecta sozinho: folha de 10 ou de 20 questões

    if folha is None:
        return {
            "ok": False,
            "mensagem": (
                "Nao foi possivel localizar a folha. Enquadre a folha INTEIRA, com os 4 "
                "quadrados pretos dos cantos visiveis, bem iluminada e sem reflexo."
            ),
            "diagnostico": {"candidatos_a_marcador": n_candidatos},
        }

    n = folha.n_questoes                      # 10 ou 20: modelo de folha que foi reconhecido na foto

    # gabarito do pedido de outro tamanho (ex.: aluno de uma prova de 10, foto de folha de 20): o front
    # recalcula a nota com o gabarito da versão lida no QR; aqui usamos o de teste só para ler as marcações
    gabarito_compativel = gabarito_correto is not None and len(gabarito_correto) == n
    if not gabarito_compativel:
        gabarito_correto = gabarito_teste(n)

    imgTh = exG.binarizar(folha.recorte)
    linhas, resumo = corretor.avaliarRespostas(
        imgTh,
        CAMPOS[n],
        RESP[n],
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

    resposta = {"ok": True, "linhas": linhas, "resumo": resumo, "qr": qr,
                "n_questoes": n, "gabarito_compativel": gabarito_compativel}
    if request.args.get("debug") or request.form.get("debug"):
        resposta["debug_img"] = _imagem_debug(folha, linhas)
        resposta["diagnostico"] = {
            "score_aneis": round(folha.score_aneis, 3),
            "candidatos_a_marcador": n_candidatos,
        }
    return resposta


@app.route("/folha/<identificador>.pdf")
def folha_pdf(identificador):
    """PDF A4 da folha de respostas com o QR da versão (UUID com ou sem hífens). Use ?n=10 ou ?n=20."""
    try:
        uid = gerar_folha.uuid_de_texto(identificador)
    except ValueError:
        return {"ok": False, "mensagem": "Identificador invalido."}, 400
    try:
        n = int(request.args.get("n", 10))
    except ValueError:
        n = 0
    if n not in QUANTIDADES:
        return {"ok": False, "mensagem": "Use ?n=10 ou ?n=20 (quantidade de questoes da prova)."}, 400
    try:
        pdf = gerar_folha.gerar_pdf_a4(uid, n)
    except FileNotFoundError:
        return {"ok": False, "mensagem": f"folha_template_{n}.png nao encontrado no servidor (omr/)."}, 503
    return Response(
        pdf,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'inline; filename="folha-{uid.hex[:8]}.pdf"'},
    )


if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta, debug=False)