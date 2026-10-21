"""
CASE 2 - Contador de polichinelos (estimativa de pose com MediaPipe)

Como rodar:
    python contadorPolichinelos.py                    -> usa assets/polichinelos.mp4
    python contadorPolichinelos.py "polichinelos 1.mp4"
    python contadorPolichinelos.py 0                  -> usa a webcam

Tecla 'q' encerra.

Funciona com qualquer versao do MediaPipe:
  - versoes antigas (ate 0.10.2x) usam mp.solutions.pose
  - versoes novas (0.10.30+ / 1.x) usam a API "Tasks"; o modelo
    models/pose_landmarker_full.task e baixado automaticamente na primeira execucao.
"""
import os
import sys
import math
import urllib.request

import cv2
import mediapipe as mp

PASTA = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(PASTA, 'assets')
VIDEO_PADRAO = os.path.join(ASSETS, 'polichinelos.mp4')

# Os limites sao proporcionais ao tamanho do tronco da pessoa (ombro -> quadril).
# Assim o contador funciona em qualquer resolucao e a qualquer distancia da camera.
LIMITE_MAOS = 1.0   # maos juntas (em cima)  -> distancia entre maos <= 1.0 x tronco
LIMITE_PES = 1.0    # pernas abertas         -> distancia entre pes   >= 1.0 x tronco

# Indices dos pontos do corpo (iguais nas duas APIs do MediaPipe)
OMBRO_E, OMBRO_D = 11, 12
MAO_E, MAO_D = 19, 20          # LEFT_INDEX / RIGHT_INDEX (ponta do indicador)
QUADRIL_E, QUADRIL_D = 23, 24
PE_E, PE_D = 31, 32            # LEFT_FOOT_INDEX / RIGHT_FOOT_INDEX

# Ligacoes usadas para desenhar o "esqueleto"
LIGACOES = [(11, 12), (11, 13), (13, 15), (15, 19), (12, 14), (14, 16), (16, 20),
            (11, 23), (12, 24), (23, 24), (23, 25), (25, 27), (27, 31),
            (24, 26), (26, 28), (28, 32)]


def abrir_video():
    origem = sys.argv[1] if len(sys.argv) > 1 else VIDEO_PADRAO
    if origem.isdigit():                       # "0", "1"... = webcam
        return cv2.VideoCapture(int(origem)), False
    if not os.path.isabs(origem) and not os.path.exists(origem):
        origem = os.path.join(ASSETS, origem)
    if not os.path.exists(origem):
        sys.exit(f'Video nao encontrado: {origem}')
    return cv2.VideoCapture(origem), True


def criar_detector():
    """Devolve uma funcao detectar(imgRGB, tempo_ms) -> lista de (x, y) normalizados ou None."""
    if hasattr(mp, 'solutions'):               # MediaPipe antigo
        pose = mp.solutions.pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

        def detectar(imgRGB, tempo_ms):
            res = pose.process(imgRGB)
            if not res.pose_landmarks:
                return None
            return [(p.x, p.y) for p in res.pose_landmarks.landmark]
        return detectar

    # MediaPipe novo (API Tasks)
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision

    modelo = os.path.join(PASTA, 'models', 'pose_landmarker_full.task')
    if not os.path.exists(modelo):
        os.makedirs(os.path.dirname(modelo), exist_ok=True)
        url = ('https://storage.googleapis.com/mediapipe-models/pose_landmarker/'
               'pose_landmarker_full/float16/latest/pose_landmarker_full.task')
        print('Baixando modelo de pose (so na primeira vez)...')
        urllib.request.urlretrieve(url, modelo)

    opcoes = vision.PoseLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=modelo),
        running_mode=vision.RunningMode.VIDEO,
        min_pose_detection_confidence=0.5,
        min_tracking_confidence=0.5)
    landmarker = vision.PoseLandmarker.create_from_options(opcoes)

    def detectar(imgRGB, tempo_ms):
        imagem = mp.Image(image_format=mp.ImageFormat.SRGB, data=imgRGB)
        res = landmarker.detect_for_video(imagem, tempo_ms)
        if not res.pose_landmarks:
            return None
        return [(p.x, p.y) for p in res.pose_landmarks[0]]
    return detectar


video, eh_arquivo = abrir_video()
detectar = criar_detector()
fps = video.get(cv2.CAP_PROP_FPS) or 30
espera = max(1, int(1000 / fps))

contador = 0
check = True
tempo_ms = 0

while True:
    success, img = video.read()

    # Fim do video: volta ao inicio e zera o contador
    if not success or img is None:
        if eh_arquivo:
            video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            contador, check = 0, True
            continue
        break

    h, w, _ = img.shape
    tempo_ms += espera
    pontos = detectar(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), tempo_ms)

    if pontos:
        px = [(int(x * w), int(y * h)) for x, y in pontos]

        # desenha o esqueleto
        for a, b in LIGACOES:
            cv2.line(img, px[a], px[b], (255, 255, 255), 2)
        for i in set(sum(LIGACOES, ())):
            cv2.circle(img, px[i], 4, (0, 0, 255), -1)

        distMO = math.dist(px[MAO_D], px[MAO_E])
        distPE = math.dist(px[PE_D], px[PE_E])
        tronco = (math.dist(px[OMBRO_E], px[QUADRIL_E]) + math.dist(px[OMBRO_D], px[QUADRIL_D])) / 2
        tronco = max(tronco, 1)

        maos_juntas = distMO <= LIMITE_MAOS * tronco
        pes_abertos = distPE >= LIMITE_PES * tronco

        # Conta 1 quando chega na posicao "aberta" (maos em cima e pernas abertas)
        if check and maos_juntas and pes_abertos:
            contador += 1
            check = False
        # Libera a proxima contagem quando volta para a posicao "fechada"
        if not maos_juntas and not pes_abertos:
            check = True

    cv2.rectangle(img, (20, 120), (330, 240), (255, 0, 0), -1)
    cv2.putText(img, f'QTD {contador}', (40, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 5)

    cv2.imshow('Resultado', img)
    if cv2.waitKey(espera) & 0xFF == ord('q'):
        break

video.release()
cv2.destroyAllWindows()
