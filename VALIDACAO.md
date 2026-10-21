# Validação e roteiro para a feira

Este relatório distingue testes automatizados, vídeo real e testes manuais pendentes. As seções históricas abaixo foram registradas em Windows com Python 3.12.15.

## Migração para Python 3.14 — 21/10/2026

- Ambiente isolado criado com CPython **3.14.8**, Linux x86-64. Instalação efetiva das versões fixadas no novo `app/requirements.txt` concluída; `uv pip check` não encontrou incompatibilidades.
- **43 testes passaram**, incluindo criação dos detectores reais de mãos e pose, inferência de imagens vazias via WebSocket, separação de sessões, rejeição de mensagens inválidas, fechamento dos detectores, páginas, vídeo e regras geométricas. Não foram substituídos os modelos por mocks para fazer a suíte passar.
- Vídeo original de polichinelos: **172 quadros lidos, 57 amostras com pose detectada e 7 ciclos reconhecidos**. Esse resultado é a saída do detector; não é uma anotação humana de referência.
- A resolução de dependências com `uv pip compile --python-version 3.14 --python-platform windows --only-binary=:all:` passou tanto para `app/requirements.txt` quanto para `app/requirements-examples.txt`. Isso confirma a disponibilidade de pacotes para Windows x64/Python 3.14; não equivale à execução no Windows.
- MediaPipe passou de 0.10.21 para **0.10.35**, OpenCV para **4.14.0.94**, NumPy para **2.5.4**, Pillow para **12.3.0** e Pytest para **9.1.1**. LAP opcional passou para **0.5.13**, porque a versão 0.5.12 não possuía pacote binário utilizável no alvo Windows/Python 3.14. As APIs Tasks usadas em `app/vision.py` continuaram funcionando, sem alteração das regras de contagem.
- A infraestrutura Linux precisou de `libGLESv2.so.2` para carregar o MediaPipe. A biblioteca foi extraída de `libgles2` do Ubuntu e usada apenas no ambiente de teste, sem acrescentar arquivos de sistema ao aplicativo.
- Foram preparados `instalar.cmd` e `iniciar.cmd`, que usam `.venv314` e preservam a `.venv` anterior. Os scripts CMD e `run.ps1` ainda precisam ser executados no Windows. O workflow `Python 3.14 no Windows` verifica automaticamente a suíte e o vídeo quando executado pelo GitHub Actions; consulte o resultado da execução antes de considerar o Windows validado.
- **Pendentes:** webcam física, interação visual no navegador, execução dos iniciadores no Windows e inferência YOLO do shopping com as novas dependências. O shopping foi verificado quanto à resolução dos pacotes, sem reinstalar/executar PyTorch neste ambiente. Os avisos de depreciação de FastAPI/Starlette não impediram os testes.

Os resultados seguintes ficam preservados como histórico da versão anterior.

## Revisão da leitura após teste do usuário

O usuário relatou contador preso em zero e números incorretos na webcam. Foram corrigidas duas restrições: exigência de duas amostras no pico aberto em baixa frequência, e uso de ângulos 3D muito rígidos na mão. A nova regra adapta a largura inicial dos pés, exige confirmação no fechamento e mantém o ciclo completo. Articulações intermediárias com menor visibilidade não reiniciam sozinhas a contagem. As mensagens orientam o próximo movimento.

A mão usa coordenadas no plano da imagem com proporção corrigida, extensão a partir da articulação e abertura do polegar em relação à palma. Há filtro por dedo antes da estabilização do número. O envio subiu de 8 para menos de 12 quadros/s e JPEG de 72% para 85%, ainda com um quadro em voo. O vídeo gravado não começa a avançar antes de o modelo ficar pronto.

- Vídeo direto, mesmos 57 quadros amostrados: **7 ciclos reconhecidos**, antes 5.
- Pelo WebSocket: **7 ciclos** no protocolo anterior (JPEG 72%, intervalo de 125 ms), antes 4; **6 ciclos** com JPEG 85% e intervalo de 85 ms. Em ambos, 57 respostas com IDs corretos. A estimativa ainda varia com a imagem comprimida; não há garantia de contagem perfeita.
- Suíte da revisão: **43 testes passaram**, incluindo abertura rápida, postura inicial mais natural, baixa visibilidade de articulações intermediárias, pernas sem abertura, filtro por dedo e landmarks reais.
- Imagem real do [exemplo oficial MediaPipe](https://github.com/google-ai-edge/mediapipe-samples/blob/main/examples/hand_landmarker/python/hand_landmarker.ipynb): mão aberta reconhecida como **5**, mão com polegar flexionado como **4**; antes a regra retornava 1 para cada. Recortes individuais passaram pelo detector completo e estabilização. Imagem vazia após os recortes limpou o resultado.
- Os landmarks reais extraídos estão em `tests/fixtures/hands_reference.json`, com regressão inclusive espelhada. A foto não é redistribuída no repositório.

Para repetir a inferência na referência pública, prepare explicitamente a imagem antes (não é usada na aplicação):

```powershell
New-Item -ItemType Directory -Force .artifacts
Invoke-WebRequest 'https://storage.googleapis.com/mediapipe-tasks/hand_landmarker/woman_hands.jpg' -OutFile '.artifacts/hand-reference.jpg'
.\.venv\Scripts\python.exe -m tests.validate_hands
```

Esses resultados não substituem testar sua webcam e gestos de 0 a 5. Os registros abaixo são da implementação anterior e ficam como histórico comparativo.

## Verificações da implementação inicial

Suíte final: **35 testes passaram**, com três avisos de depreciação.

- Ambiente Python criado; dependências de `requirements.txt` e `requirements-examples.txt` instaladas. Imports de FastAPI, OpenCV, MediaPipe, YOLO e inicialização dos três modelos bem-sucedidos.
- Servidor Uvicorn inicializado em 127.0.0.1:8000. GET real nas três páginas retornou 200. TestClient também verificou estáticos e vídeo gravado.
- WebSocket real via rede: handshake com origem local, inicialização de mãos, JPEG enviado, resposta com ID correspondente, pontos vazios e número `null` para imagem sem mão.
- Vídeo real transmitido ao Uvicorn como JPEG 640 × 360, qualidade 72, um quadro por resposta: **57 respostas**, IDs correspondentes até 171 e **4 ciclos reconhecidos**. A diferença em relação aos 5 do teste direto demonstra a sensibilidade à compressão/estimativa e não é apresentada como contagem humana de referência. Reproduza com `python -m tests.validate_transport`, com servidor ativo.
- Testes automatizados cobrem ciclo completo, abertura mantida, início aberto, movimento incompleto, braços baixos, baixa confiança, perda de pessoa, estabilização, limpeza por ausência de mão, números de 0 a 5 e invariância geométrica por rotação/espelhamento.
- Integração com modelos reais: imagens vazias nas duas experiências, estado separado entre conexões, mensagens inválidas, imagem acima da resolução, mensagem acima do limite, modelo ausente, origem externa recusada e fechamento do detector.
- Vídeo de polichinelos inteiro lido: **172 quadros**, inferência a cada três quadros, **57 quadros com pose detectada e 5 ciclos completos**. Contagem é saída observada da aplicação, não medição de precisão nem anotação humana de referência. Nenhuma webcam foi usada neste teste.
- Exemplo vagas: 30 quadros reais processados sem janela. Teste automatizado também verifica alteração visual no primeiro quadro.
- Exemplo polichinelos: 30 quadros reais processados pela entrada de terminal antiga, sem janela.
- Exemplo shopping: 20 quadros reais processados com YOLO/rastreamento sem janela. O código usa o centro da caixa para acumular IDs na região e mantém o conjunto por execução. Não conta pessoas com identidade garantida nem determina direção de passagem.
- Compilação dos módulos e validação da sintaxe JavaScript com `vm.Script` do Node concluídas. São verificações estáticas, não execução da interface.
- SHA-256 dos dois pares de vídeos duplicados conferidos. Todos os originais preservados.

## Pendências explícitas

A ferramenta de navegador retornou inventário vazio e “Browser is not available: iab”. Não foi possível renderizar a interface ou exercitar getUserMedia neste ambiente. Portanto **layout, responsividade, navegação por teclado, câmera negada/ocupada, fechamento das tracks e demonstração dentro de um navegador real ainda precisam de teste manual**. Os caminhos foram implementados e revisados, mas não são declarados aprovados por teste de UI.

Não houve teste físico com webcam, diversidade de participantes, latência no computador da feira ou ensaio offline completo de ponta a ponta. A revisão acrescentou inferência em foto pública de mãos reais (5 e 4), mas ainda não validou todos os gestos de 0 a 5 em webcam. Testes geométricos e essa referência não substituem o ensaio no equipamento real.

Há avisos de depreciação em Starlette/AnyIO e Protobuf no Python 3.12; não impediram os testes. MediaPipe também emite avisos internos de feedback/projeção; os resultados observados estão registrados acima. Use a versão Python documentada.

## Roteiro manual obrigatório antes da feira

1. Instale tudo, inicie o servidor e visite `/`, `/polichinelos` e `/numeros`. Atualize cada URL diretamente. Confira home em 1440 × 900, notebook 1366 × 768 e celular 390 × 844, sem rolagem horizontal ou controles cortados. Navegue com Tab/Enter e confira foco e opção de movimento reduzido do sistema.
2. Na home, confirme que o canvas é identificado como ilustração. Entre em polichinelos e confira que a câmera ainda está desligada.
3. Use “Vídeo gravado”; confira a identificação, imagem com pontos alinhados, contagem, progresso e encerramento ao fim. Pause/continue, oculte pontos, zere e reinicie a demonstração. A contagem ao vivo pode variar com a amostragem e a velocidade do equipamento.
4. Inicie webcam; primeiro negue a permissão e confira a mensagem. Depois permita. Teste câmera ausente e câmera ocupada por outro aplicativo. Confira mensagem útil sem recarregamento obrigatório.
5. Com corpo inteiro, faça cinco ciclos completos. Faça movimentos parciais, mantenha posição aberta e saia da imagem no meio de um ciclo. Não deve aumentar a contagem nesses casos. Pause e continue: a contagem anterior deve permanecer, mas o ciclo interrompido deve ser descartado.
6. Em números, mostre cada gesto de 0 a 5 com mãos direita e esquerda, palma à câmera. Confira polegar isolado e recolhido, indicadores coloridos e estabilização. Saia da imagem: o número deve virar `—`; duas mãos devem pedir apenas uma mão. Compare resultado com contagem humana e registre falhas.
7. Encerre e veja se o indicador de câmera do navegador apaga. Repita trocando de página e de aba. Abra duas sessões e confira que contagens não se misturam. Feche uma e continue na outra.
8. Pare o servidor enquanto a câmera estiver ativa: a interface deve desligar a câmera e explicar perda de conexão. Reinicie e reconecte. Em uma cópia de teste, renomeie temporariamente um modelo, confira a mensagem e restaure o arquivo.
9. Desconecte a internet, reinicie o sistema e execute as duas experiências e o vídeo gravado. Confira que não há download ou dependência de CDN. Faça um ensaio no equipamento e iluminação reais do evento.

Não use o resultado como avaliação física, identificação pessoal ou reconhecimento de Libras. São experiências educativas sob condições de posicionamento indicadas.
