import sys, glob, random
sys.path.insert(0,'/home/claude/work/back/FlyLearn_Backend-main/omr')
import cv2, numpy as np
import omr_config as C, extrairGabarito as exG, corretor, qr_util
from omr_config import campos, LAYOUTS

def preencher(img_bgr, n, resp, dpi, forca=1.0):
    """Pinta bolhas na folha rasterizada (img em dpi). resp: lista de índices 0-4 ou None."""
    out=img_bgr.copy(); mm=dpi/25.4
    lay=LAYOUTS[n]; dn=C.DIAMETRO_BOLHA[n]
    for q,a in enumerate(resp):
        if a is None: continue
        als=a if isinstance(a,(list,tuple)) else [a]
        for al in als:
            x_mm=C.X0_COLUNAS[1 if q>=n//2 else 0]+C.X_PRIMEIRA_BOLHA+C.PASSO_BOLHA*al
            y_mm=C.TOPO_LINHAS+(q%(n//2))*C.PASSO_LINHA[n]+C.PASSO_LINHA[n]/2-1
            cv2.circle(out,(int(x_mm*mm),int(y_mm*mm)),int(dn/2*mm*0.85),(int(40*(2-forca)),)*3,-1)
    return out

def rodar(path, n, dpi, resp, rot=0, persp=False, blur=0):
    img=cv2.imread(path); img=preencher(img,n,resp,dpi)
    if rot: img=cv2.rotate(img,{90:cv2.ROTATE_90_CLOCKWISE,180:cv2.ROTATE_180,270:cv2.ROTATE_90_COUNTERCLOCKWISE}[rot])
    if persp:
        h,w=img.shape[:2]; src=np.float32([[0,0],[w,0],[w,h],[0,h]])
        dst=np.float32([[w*.04,h*.03],[w*.95,h*.0],[w*.98,h*.97],[w*.02,h*.99]])
        img=cv2.warpPerspective(img,cv2.getPerspectiveTransform(src,dst),(w,h),borderValue=(90,90,90))
    if blur: img=cv2.GaussianBlur(img,(0,0),blur)
    folha,nc=exG.localizar_folha(img)
    if folha is None: return None
    th=exG.binarizar(folha.recorte)
    gab=[f"{i+1}-A" for i in range(folha.n_questoes)]
    linhas,res=corretor.avaliarRespostas(th,campos(folha.n_questoes),None,gab,limiar=20,margem_dupla=15)
    return folha,linhas,res,qr_util.ler_qr(img,folha.matriz)

if __name__=='__main__':
    random.seed(1)
    for path,n in [('img/f20-1.png',20),('img/f10-1.png',10)]:
        resp=[random.randint(0,4) for _ in range(n)]
        resp[3]=None; resp[5]=[1,2]
        for kw in [dict(),dict(rot=90),dict(persp=True),dict(persp=True,blur=1.5)]:
            r=rodar('/home/claude/work/'+path,n,150,resp,**kw)
            if r is None: print(path,kw,'FOLHA NAO ACHADA'); continue
            folha,linhas,res,qr=r
            lido=[l['resposta_detectada'] for l in linhas]
            esp=['-' if (a is None or isinstance(a,list)) else 'ABCDE'[a] for a in resp]
            ok=sum(1 for a,b in zip(lido,esp) if a==b)
            print(path,kw,'n=',folha.n_questoes,'score=%.2f'%folha.score_aneis,'ok=%d/%d'%(ok,n),'qr=',qr)
            if ok<n: print('  esperado',''.join(esp),'\n  lido    ',''.join(lido))
