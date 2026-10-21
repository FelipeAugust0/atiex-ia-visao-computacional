# Modelos locais

Os três arquivos são usados diretamente do disco; não há download no servidor.

| Arquivo | Origem | SHA-256 observado |
|---|---|---|
| `pose_landmarker_full.task` | Original do repositório, MediaPipe Pose Full | `4EAA5EB7A98365221087693FCC286334CF0858E2EB6E15B506AA4A7ECDCEC4AD` |
| `yolo11n.pt` | Original do repositório, YOLO11n | `0EBBC80D4A7680D14987A577CD21342B65ECFD94632BD9A8DA63AE6417644EE1` |
| `hand_landmarker.task` | Modelo oficial MediaPipe, versão de recurso 1, preparado nesta implementação | `FBC2A30080C3C557093B5DDFC334698132EB341044CCEE322CCF8BCF3607CDE1` |

Download de preparação de mãos: https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task

Preparação explícita: `python -m app.prepare_models` na raiz. Não substitui arquivos existentes. Para modelo corrompido, mova o original para backup antes de preparar novamente. Os hashes acima documentam os arquivos testados, sem constituir uma verificação contra uma assinatura do fornecedor.
