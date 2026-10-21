# VISÃO — IA na Feira das Profissões

Experiência local para o SENAI São Carlos: home educativa, **polichinelos** e **números com a mão** no navegador. HTML/CSS/JavaScript sem React; FastAPI, OpenCV e MediaPipe no Python. Sem login, banco de dados, CDN ou gravação de visitantes.

## Instalação no Windows PowerShell

Use **Python 3.12 de 64 bits**. Na raiz do repositório, com internet antes da feira:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r app/requirements.txt
.\.venv\Scripts\python.exe -m app.prepare_models
```

Alternativa com uv: `uv venv --python 3.12 .venv` e `uv pip install --python .venv/Scripts/python.exe -r app/requirements.txt`. Não precisa ativar o ambiente. Não use Python 3.14/3.15 com estas versões.

Os três modelos estão em `app/models/`. A preparação preserva modelos existentes e baixa somente modelos MediaPipe ausentes. **O servidor não baixa modelos**: mostra o arquivo ausente na interface. Para substituir um modelo corrompido, mova-o para backup e execute a preparação novamente. Preserve o YOLO original em `app/models/yolo11n.pt`.

## Iniciar com um comando

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.server:app --host 127.0.0.1 --port 8000 --ws-max-size 450000 --ws-max-queue 1
```

Abra **http://localhost:8000**. Alternativa: `./run.ps1`, que também configura cache local para Matplotlib. `Ctrl+C` encerra o servidor.

| URL | Experiência |
|---|---|
| `/` | Como a IA enxerga o mundo? |
| `/polichinelos` | Câmera ou vídeo gravado, contador e meta de 5 |
| `/numeros` | Dedos levantados de uma mão, de 0 a 5 |

As URLs funcionam ao atualizar. A câmera só é solicitada após **Iniciar câmera**. Use localhost; acesso por IP de outro computador geralmente exige HTTPS para getUserMedia. O servidor escuta somente a interface local.

## Operação e execução offline

Após instalar dependências e preparar modelos, desconecte a internet e inicie normalmente. Fontes do sistema, scripts e modelos são locais. Faça o ensaio no computador da feira; copiar o repositório não instala o ambiente Python.

**Polichinelos:** fique de frente com corpo inteiro e espaço seguro. Comece com braços baixos e pés juntos, abra pernas e leve braços acima da cabeça, depois feche. A posição fechada exige dois quadros consecutivos; o pico aberto pode ocupar só um quadro, desde que braços e pernas satisfaçam a geometria juntos. A abertura se adapta à largura dos pés na posição inicial. A regra usa tronco, cotovelos, altura dos punhos e distância dos pés; não depende apenas de mãos próximas. Perda de pose ou baixa visibilidade de pontos essenciais invalida o ciclo em andamento. A mensagem indica qual movimento falta. Pausar mantém a câmera ligada; continuar preserva contagem e exige novo início fechado. Zerar reinicia o desafio. O vídeo gravado começa somente após o detector estar pronto e termina sem repetir automaticamente.

**Números:** mostre uma mão inteira, direita ou esquerda, palma voltada à câmera e dedos separados. Punho fechado é **0**; ausência de mão é **—**. A regra usa ângulos e distâncias normalizadas no plano da imagem, com proporção corrigida; evita depender da profundidade 3D estimada pela webcam. O polegar também precisa se afastar da palma, evitando contá-lo dobrado sobre ela. Mudanças de cada dedo exigem duas observações; o número precisa de 300 ms de estabilidade. Mudanças de gesto limpam o número enquanto estabilizam. Ausência ou duas mãos removem a leitura e reiniciam os filtros. Não reconhece algarismos escritos nem Libras. Mão de lado, dedos sobrepostos, movimentos rápidos e oclusões podem causar erros.

Encerrar, mudar de página ou esconder a aba fecha tracks e WebSocket. Permissão negada, câmera ausente/ocupada e falha do modelo recebem mensagens em português. Conexão inativa por 45 segundos é encerrada; após pausa longa, inicie novamente. Não há serviço externo de inferência nem persistência de quadros, apenas processamento temporário em memória.

## Exemplos de terminal preservados

```powershell
.\.venv\Scripts\python.exe -m app.vagas
.\.venv\Scripts\python.exe -m app.contadorPolichinelos
.\.venv\Scripts\python.exe -m app.contadorPolichinelos 0
```

Shopping tem dependências opcionais mais pesadas:

```powershell
.\.venv\Scripts\python.exe -m pip install -r app/requirements-examples.txt
.\.venv\Scripts\python.exe -m app.escadas
```

O exemplo shopping força modo offline, desliga instalação automática e sincronização do Ultralytics, e usa configuração local em `.artifacts/ultralytics`.

As entradas antigas, como `python app/vagas.py`, continuam disponíveis. Um nome de vídeo é procurado em `app/assets/`; também aceitam caminho absoluto ou número de webcam. `q` encerra a janela. Ao fim do arquivo, encerram em vez de repetir indefinidamente em caso de erro. Todos aceitam `--headless --max-frames 30`. Recursos são liberados em `finally`. Imports não abrem câmera nem executam inferência.

Vagas estima textura em oito regiões calibradas; não detecta carros genericamente. Shopping rastreia pessoas e acumula IDs cujo **centro da caixa entra na região**. Não determina sentido de passagem nem identifica pessoas: oclusões e troca de IDs podem alterar o total. Trocar a cena exige recalibrar regiões.

## Arquitetura

- `app/server.py`: páginas, estáticos, vídeo e `/ws/pose` / `/ws/hand` na mesma origem.
- `app/vision.py`: MediaPipe Tasks VIDEO, modelo e estado por conexão, timestamps monotônicos e fechamento explícito.
- `app/logic.py`: ciclo fechado → aberto → fechado e estabilização dos dedos, independentes de câmera.
- `app/static/`: captura, interface e sobreposição; canvas da home é uma ilustração identificada.
- `app/cli.py`: execução finita e liberação dos recursos dos exemplos.

O navegador envia JPEG de até **640 × 480**, qualidade 85%, com intervalo de 85 ms após cada resposta: menos de 12 envios/s, reduzido pelo tempo de inferência. Existe apenas **um quadro em voo**; quadros intermediários da câmera são descartados. Resultado e imagem compartilham ID. Pontos são desenhados sobre a captura correspondente, evitando atrasos sobre o vídeo novo.

O servidor valida tamanho da mensagem, ID, frequência, origem e dimensões JPEG antes de decodificar. As opções Uvicorn acima limitam transporte e fila. Inferência roda fora do event loop. Cada conexão tem detector e contagem independentes. Não há gravação por padrão.

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m tests.validate_video
.\.venv\Scripts\python.exe -m app.vagas --headless --max-frames 30
.\.venv\Scripts\python.exe -m app.escadas --headless --max-frames 20
```

Leia [VALIDACAO.md](VALIDACAO.md) para evidências e roteiro manual. Geometria sintética não mede precisão do modelo em visitantes reais. Compilação não equivale a teste de webcam.

Versões instaladas e testadas: Python 3.12.15, FastAPI 0.115.12, Uvicorn 0.34.2, MediaPipe 0.10.21, NumPy 1.26.4 e OpenCV 4.11.0. Exemplo opcional: Ultralytics 8.3.40, Torch 2.14.1, Torchvision 0.29.1 e LAP 0.5.12. Dependências diretas estão fixadas; transitivas podem variar. MediaPipe requer o pacote OpenCV contrib; o exemplo YOLO também declara opencv-python, fixado na mesma versão para manter os binários compatíveis. Evite atualizar apenas um deles isoladamente.

## Arquivos preservados e duplicados

Nenhum vídeo, documento ou modelo original foi removido. SHA-256 confirmou:

- `video.mp4` e `video - Copia.mp4`: `84BD389854D39E1D9EDCFBA848B9D0E09F527B4E8364EAC86D172DA8578156CB`.
- `polichinelos.mp4` e `polichinelos 1.mp4`: `CF520E19C2E622CE81239AC6EE8FE79610A6C24F344FF37E2AC8012E238615FC`.

## Documentação oficial consultada

- [FastAPI: WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [MediaPipe: Pose Landmarker em Python](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/python)
- [MediaPipe: Hand Landmarker em Python](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/python)
