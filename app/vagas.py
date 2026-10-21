"""
CASE 1 - Detector de vagas livres (visao computacional classica com OpenCV)

Como rodar:
    python vagas.py                       -> usa assets/video.mp4
    python vagas.py "video - Copia.mp4"

Tecla 'q' encerra.
"""
import os
import sys

import cv2
import numpy as np

PASTA = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(PASTA, 'assets')
VIDEO_PADRAO = os.path.join(ASSETS, 'video.mp4')

# Coordenadas das vagas [x, y, largura, altura], marcadas num video de 1280x720.
# Se o video tiver outra resolucao, as caixas sao reescaladas automaticamente.
LARGURA_BASE, ALTURA_BASE = 1280, 720
vagas_base = [
    [1, 89, 108, 213],
    [115, 87, 152, 211],
    [289, 89, 138, 212],
    [439, 87, 135, 212],
    [591, 90, 132, 206],
    [738, 93, 139, 204],
    [881, 93, 138, 201],
    [1027, 94, 147, 202],
]

# A vaga e considerada OCUPADA quando mais de 12% dos pixels do recorte sao "brancos"
# (bordas/texturas de um carro). Usar porcentagem em vez de um numero fixo (3000)
# faz o limite valer para vagas de tamanhos diferentes e qualquer resolucao.
LIMITE_OCUPACAO = 0.12

origem = sys.argv[1] if len(sys.argv) > 1 else VIDEO_PADRAO
if not os.path.isabs(origem) and not os.path.exists(origem):
    origem = os.path.join(ASSETS, origem)
if not os.path.exists(origem):
    sys.exit(f'Video nao encontrado: {origem}')

video = cv2.VideoCapture(origem)
largura = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
altura = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
sx, sy = largura / LARGURA_BASE, altura / ALTURA_BASE
vagas = [[int(x * sx), int(y * sy), int(w * sx), int(h * sy)] for x, y, w, h in vagas_base]
total = len(vagas)

kernel = np.ones((3, 3), np.uint8)

while True:
    success, img = video.read()

    # Se o video acabar, rebobina para o inicio
    if not success or img is None:
        video.set(cv2.CAP_PROP_POS_FRAMES, 0)
        continue

    imgCinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgTh = cv2.adaptiveThreshold(imgCinza, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                  cv2.THRESH_BINARY_INV, 25, 16)
    imgBlur = cv2.medianBlur(imgTh, 5)
    imgDil = cv2.dilate(imgBlur, kernel)

    qtVagasAbertas = 0
    for x, y, w, h in vagas:
        recorte = imgDil[y:y + h, x:x + w]
        qtPxBranco = cv2.countNonZero(recorte)
        ocupacao = qtPxBranco / (w * h)
        cv2.putText(img, f'{ocupacao:.0%}', (x + 5, y + h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        if ocupacao > LIMITE_OCUPACAO:
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 3)   # vermelho = ocupada
        else:
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 3)   # verde = livre
            qtVagasAbertas += 1

    cv2.rectangle(img, (90, 0), (415, 60), (255, 0, 0), -1)
    cv2.putText(img, f'LIVRE: {qtVagasAbertas}/{total}', (95, 45),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 5)

    cv2.imshow('video', img)
    cv2.imshow('video TH', imgDil)

    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

video.release()
cv2.destroyAllWindows()
