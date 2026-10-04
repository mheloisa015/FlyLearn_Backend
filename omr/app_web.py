import pickle
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, request, render_template_string

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

app = Flask(__name__)

PAGINA_CAPTURA = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Correcao OMR - Celular</title>
<style>
  body { font-family: Arial, sans-serif; text-align: center; background:#111; color:#eee; margin:0; padding:16px; }
  video, img { width: 100%; max-width: 420px; border-radius: 8px; }
  button { font-size: 1.1em; padding: 12px 24px; margin-top: 12px; border-radius: 8px; border: none; background:#2b7; color:#fff; }
  button:disabled { background:#555; }
  #resultado { text-align: left; max-width: 420px; margin: 16px auto; background:#222; padding: 12px; border-radius: 8px; }
  table { width: 100%; border-collapse: collapse; margin-top: 8px; }
  td, th { border-bottom: 1px solid #444; padding: 4px 6px; font-size: 0.9em; }
  .CORRETA { color: #4f4; }
  .INCORRETA { color: #f66; }
  .BRANCO { color: #aaa; }
  .ANULADA { color: #fa4; }
</style>
</head>
<body>
  <h2>Correcao automatica da folha</h2>
  <video id="video" autoplay playsinline></video>
  <canvas id="canvas" style="display:none;"></canvas>
  <br>
  <button id="btnFoto">Tirar foto e corrigir</button>
  <div id="resultado"></div>

<script>
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const btn = document.getElementById('btnFoto');
const resultadoDiv = document.getElementById('resultado');

if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
  resultadoDiv.innerHTML = "<p><b>O navegador bloqueou o acesso a camera.</b><br>" +
    "Isso normalmente acontece porque a pagina esta em http:// (nao https://) " +
    "e o navegador so libera a camera em conexoes seguras. " +
    "Confira se voce acessou usando https:// no endereco.</p>";
} else {
  navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
    .then(stream => { video.srcObject = stream; })
    .catch(err => {
      resultadoDiv.innerHTML = "<p>Nao foi possivel acessar a camera: " + err + "</p>";
    });
}

btn.addEventListener('click', () => {
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);

  btn.disabled = true;
  btn.textContent = "Processando...";

  canvas.toBlob(blob => {
    const dados = new FormData();
    dados.append('foto', blob, 'foto.jpg');

    fetch('/corrigir', { method: 'POST', body: dados })
      .then(r => r.json())
      .then(mostrarResultado)
      .catch(err => {
        resultadoDiv.innerHTML = "<p>Erro ao enviar: " + err + "</p>";
      })
      .finally(() => {
        btn.disabled = false;
        btn.textContent = "Tirar foto e corrigir";
      });
  }, 'image/jpeg', 0.92);
});

function mostrarResultado(dados) {
  if (!dados.ok) {
    resultadoDiv.innerHTML = "<p>" + dados.mensagem + "</p>";
    return;
  }
  let linhas = dados.linhas.map(l =>
    `<tr class="${l.situacao}">
       <td>${l.questao}</td><td>${l.resposta_detectada}</td>
       <td>${l.resposta_correta}</td><td>${l.situacao}</td>
     </tr>`
  ).join('');

  resultadoDiv.innerHTML = `
    <table>
      <tr><th>Questao</th><th>Marcada</th><th>Correta</th><th>Situacao</th></tr>
      ${linhas}
    </table>
    <p><b>Acertos:</b> ${dados.resumo.acertos}/${dados.resumo.total} &nbsp;
       <b>Erros:</b> ${dados.resumo.erros} &nbsp;
       <b>Brancos:</b> ${dados.resumo.brancos} &nbsp;
       <b>Anuladas:</b> ${dados.resumo.anuladas}</p>
    <p><b>Nota:</b> ${dados.resumo.nota}</p>
  `;
}
</script>
</body>
</html>
"""

@app.route("/")
def pagina_inicial():
    return render_template_string(PAGINA_CAPTURA)


@app.route("/corrigir", methods=["POST"])
def corrigir():
    arquivo = request.files.get("foto")
    if arquivo is None:
        return {"ok": False, "mensagem": "Nenhuma imagem recebida."}

    bytes_imagem = np.frombuffer(arquivo.read(), dtype=np.uint8)
    imagem = cv2.imdecode(bytes_imagem, cv2.IMREAD_COLOR)

    if imagem is None:
        return {"ok": False, "mensagem": "Nao foi possivel ler a imagem enviada."}

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
        respostaCorreta,
        limiar=LIMIAR_PREENCHIMENTO,
        margem_dupla=MARGEM_DUPLA_MARCACAO,
    )

    return {"ok": True, "linhas": linhas, "resumo": resumo}


if __name__ == "__main__":
    # ALTERADO: ssl_context="adhoc" faz o Flask gerar um certificado
    # HTTPS autoassinado na hora e servir a pagina em https://.
    #
    # POR QUE ISSO E NECESSARIO: navegadores de celular (Chrome, Safari)
    # so liberam o acesso a camera (getUserMedia) em paginas https://,
    # ou em http://localhost. Como o celular acessa pelo IP da rede
    # (ex.: http://192.168.0.15:5000), o navegador bloqueia a camera em
    # silencio -- a pagina abre, o botao aparece, mas o video nunca
    # inicia. Servindo em https:// isso passa a funcionar.
    #
    # Requer o pacote pyOpenSSL:
    #   pip install pyopenssl
    #
    # O navegador do celular vai mostrar um aviso de "conexao nao
    # segura" / "certificado invalido" (porque o certificado e
    # autoassinado, nao emitido por uma autoridade reconhecida). Isso e
    # esperado para uso local de teste: toque em "Avancado" ->
    # "Continuar mesmo assim" (o texto exato varia por navegador).
    app.run(host="0.0.0.0", port=5000, debug=True, ssl_context="adhoc")