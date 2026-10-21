# Visão computacional – 3 cases

Os scripts ficam na raiz e os vídeos na pasta **`assets/`** (não precisa de caminho `C:\Users\...`).
Ao passar outro vídeo pelo nome, ele é procurado em `assets/`.

```
projeto_visao_computacional/
├── vagas.py
├── contadorPolichinelos.py
├── escadas.py
├── LEIAME.md
├── requirements.txt
├── models/   (yolo11n.pt e pose_landmarker_full.task)
└── assets/   (vídeos .mp4)
```

```
pip install -r requirements.txt
```

| Script | Vídeo padrão | Técnica | Como rodar com outro vídeo |
|---|---|---|---|
| `vagas.py` | `video.mp4` | Visão clássica (limiarização adaptativa + contagem de pixels) | `python vagas.py "video - Copia.mp4"` |
| `contadorPolichinelos.py` | `polichinelos.mp4` | Estimativa de pose (MediaPipe, 33 pontos do corpo) | `python contadorPolichinelos.py "polichinelos 1.mp4"` ou `0` para webcam |
| `escadas.py` | `escadas.mp4` | Detecção + rastreamento de pessoas (YOLO11) | `python escadas.py outro.mp4` ou `0` para webcam |

Tecla **q** fecha a janela. Os vídeos repetem em loop (bom para deixar rodando na apresentação).

## Observações
- **MediaPipe:** o contador funciona com a versão antiga (`mp.solutions`, testado na 0.10.14) e com as versões novas (0.10.30+ / 1.x), que removeram `mp.solutions`; nessas o modelo `models/pose_landmarker_full.task` é baixado sozinho na primeira execução (precisa de internet uma vez).
  Opção mais garantida: Python 3.11 ou 3.12 + `pip install mediapipe==0.10.14`.
- **YOLO:** o modelo `models/yolo11n.pt` já vem no pacote (se faltar, é baixado sozinho). Roda em CPU (~10 quadros/s em 1080p).
- **Limites:** vagas usa porcentagem da área (12%) e o polichinelo usa distâncias proporcionais ao tronco da pessoa, por isso funcionam em qualquer resolução.
- `video - Copia.mp4` é idêntico a `video.mp4`, e `polichinelos 1.mp4` é idêntico a `polichinelos.mp4`.
