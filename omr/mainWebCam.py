import cv2
import extrairGabarito as exG
import corretor
from pathlib import Path

PASTA_OMR = Path(__file__).resolve().parent

from omr_config import campos as campos_de

PADRAO_TESTE = ["A", "C", "B", "D", "A", "B", "C", "E", "A", "D"]   # gabarito de teste (repete p/ 20 questoes)

LIMIAR_PREENCHIMENTO = 15
MARGEM_DUPLA_MARCACAO = 8

video = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not video.isOpened():
    print("ERRO: nao foi possivel abrir a webcam (indice 0).")
    print("Possiveis causas:")
    print("  - Outro programa (Zoom, Teams, Camera do Windows) esta usando a webcam.")
    print("  - Permissao de camera bloqueada: Configuracoes do Windows > Privacidade > Camera.")
    print("  - Indice de camera errado: tente trocar VideoCapture(0, ...) por VideoCapture(1, ...).")
    raise SystemExit(1)


ultimo_resumo_impresso = None

while True:
    ret, imagem = video.read()

    if not ret or imagem is None:
        continue

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

    folha_lida, _ = exG.localizar_folha(imagem)
    gabarito, bbox = (None, None)
    if folha_lida is not None:
        x, y, w_, h_ = cv2.boundingRect(folha_lida.pontos.astype("int32"))
        gabarito, bbox = folha_lida.recorte, [x, y, w_, h_]

    if gabarito is None or bbox is None:
        cv2.putText(imagem, "PROCURANDO FOLHA...", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow("img", imagem)
        continue

    n = folha_lida.n_questoes                       # 10 ou 20, detectado pela foto
    campos = campos_de(n)
    resp = [f"{q}-{a}" for q in range(1, n + 1) for a in "ABCDE"]
    respostaCorreta = [f"{i + 1}-{PADRAO_TESTE[i % 10]}" for i in range(n)]

    imgGray = cv2.cvtColor(gabarito, cv2.COLOR_BGR2GRAY)
    ret, imgTh = cv2.threshold(imgGray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    cv2.rectangle(imagem, (bbox[0], bbox[1]), (bbox[0] + bbox[2], bbox[1] + bbox[3]), (0, 255, 0), 3)

    for (x, y, w, h) in campos:
        cv2.rectangle(gabarito, (x, y), (x + w, y + h), (0, 0, 255), 2)

    linhas, resumo = corretor.avaliarRespostas(
        imgTh,
        campos,
        resp,
        respostaCorreta,
        limiar=LIMIAR_PREENCHIMENTO,
        margem_dupla=MARGEM_DUPLA_MARCACAO,
    )

    cv2.putText(imagem, f"ACERTOS: {resumo['acertos']}/{resumo['total']}  NOTA: {resumo['nota']}", (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3,)
    cv2.putText(imagem, f"Brancos: {resumo['brancos']}  Anuladas: {resumo['anuladas']}", (30, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2,)

    assinatura = tuple(l["resposta_detectada"] for l in linhas)
    if assinatura != ultimo_resumo_impresso:
        ultimo_resumo_impresso = assinatura
        print("\nQuestao | Detectada | Correta | Situacao")
        for l in linhas:
            print(f"{l['questao']:^7} | {l['resposta_detectada']:^9} | {l['resposta_correta']:^7} | {l['situacao']}")
        print(
            f"Acertos: {resumo['acertos']}/{resumo['total']}  "
            f"Erros: {resumo['erros']}  Brancos: {resumo['brancos']}  "
            f"Anuladas: {resumo['anuladas']}  Nota: {resumo['nota']}"
        )

    cv2.imshow("img", imagem)
    cv2.imshow("Gabarito", gabarito)
    cv2.imshow("IMG TH", imgTh)

video.release()
cv2.destroyAllWindows()