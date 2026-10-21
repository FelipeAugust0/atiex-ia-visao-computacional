"""
CASE 3 - Fluxo de pessoas na escada rolante (deteccao de objetos com YOLO)

Como rodar:
    python escadas.py                -> usa assets/escadas.mp4
    python escadas.py outro.mp4
    python escadas.py 0              -> usa a webcam

Tecla 'q' encerra.

Na primeira execucao o modelo models/yolo11n.pt (~5 MB) e baixado automaticamente.

O que ele mostra:
  - quantas pessoas estao na cena agora
  - quantas estao na area da escada rolante agora
  - quantas pessoas diferentes ja usaram a escada (cada pessoa recebe um ID
    pelo rastreamento, entao a mesma pessoa nao e contada duas vezes)
"""
import os
import sys

import cv2
from ultralytics import YOLO

PASTA = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(PASTA, 'assets')
MODELO = os.path.join(PASTA, 'models', 'yolo11n.pt')
VIDEO_PADRAO = os.path.join(ASSETS, 'escadas.mp4')

# Area da escada rolante [x1, y1, x2, y2], marcada num video de 1920x1080.
# Se o video tiver outra resolucao, a area e reescalada automaticamente.
LARGURA_BASE, ALTURA_BASE = 1920, 1080
AREA_ESCADA_BASE = [0, 280, 880, 880]

PESSOA = 0          # no YOLO (dataset COCO), a classe 0 e "person"
CONFIANCA = 0.3

origem = sys.argv[1] if len(sys.argv) > 1 else VIDEO_PADRAO
eh_arquivo = not origem.isdigit()
if eh_arquivo:
    if not os.path.isabs(origem) and not os.path.exists(origem):
        origem = os.path.join(ASSETS, origem)
    if not os.path.exists(origem):
        sys.exit(f'Video nao encontrado: {origem}')
    video = cv2.VideoCapture(origem)
else:
    video = cv2.VideoCapture(int(origem))

largura = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
altura = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
sx, sy = largura / LARGURA_BASE, altura / ALTURA_BASE
ex1, ey1, ex2, ey2 = [int(v * s) for v, s in zip(AREA_ESCADA_BASE, (sx, sy, sx, sy))]
fator = largura / LARGURA_BASE   # fator para o tamanho dos textos

modelo = YOLO(MODELO)   # baixa sozinho se nao existir

# Mostra a imagem num tamanho que cabe na tela
escala_tela = min(1.0, 1280 / largura)

ids_escada = set()   # IDs de quem ja passou pela escada

while True:
    success, img = video.read()

    if not success or img is None:
        if eh_arquivo:                               # fim do video: recomeca do zero
            video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ids_escada.clear()
            modelo = YOLO(MODELO)   # reinicia o rastreador
            continue
        break

    # Deteccao + rastreamento (cada pessoa ganha um ID que se mantem entre os frames)
    resultado = modelo.track(img, classes=[PESSOA], conf=CONFIANCA, persist=True, verbose=False)[0]

    na_cena = 0
    na_escada = 0
    if resultado.boxes.id is not None:
        caixas = resultado.boxes.xyxy.int().tolist()
        ids = resultado.boxes.id.int().tolist()
        for (x1, y1, x2, y2), pid in zip(caixas, ids):
            na_cena += 1
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2      # centro da pessoa
            dentro = ex1 <= cx <= ex2 and ey1 <= cy <= ey2
            if dentro:
                na_escada += 1
                ids_escada.add(pid)
            cor = (0, 165, 255) if dentro else (0, 255, 0)  # laranja = na escada
            cv2.rectangle(img, (x1, y1), (x2, y2), cor, 3)
            cv2.putText(img, f'ID {pid}', (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor, 2)
            cv2.circle(img, (cx, cy), 5, cor, -1)

    # Area da escada rolante
    cv2.rectangle(img, (ex1, ey1), (ex2, ey2), (255, 0, 0), 3)
    cv2.putText(img, 'ESCADA ROLANTE', (ex1 + 10, ey1 + int(40 * fator)), cv2.FONT_HERSHEY_SIMPLEX, 1.2 * fator, (255, 0, 0), 3)

    # Painel com os numeros (canto inferior direito, onde so tem piso)
    topo = altura - int(190 * fator)
    cv2.rectangle(img, (largura - int(620 * fator), topo), (largura, altura), (255, 0, 0), -1)
    textos = [f'NA CENA: {na_cena}', f'NA ESCADA AGORA: {na_escada}', f'USARAM A ESCADA: {len(ids_escada)}']
    for i, t in enumerate(textos):
        cv2.putText(img, t, (largura - int(600 * fator), topo + int((55 + i * 55) * fator)),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.4 * fator, (255, 255, 255), max(1, int(4 * fator)))

    if escala_tela < 1:
        img = cv2.resize(img, None, fx=escala_tela, fy=escala_tela)
    cv2.imshow('Escada rolante', img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video.release()
cv2.destroyAllWindows()
