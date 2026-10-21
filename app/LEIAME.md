# Exemplos de visão computacional

Consulte o [README principal](../README.md) para instalação Windows, modelos, servidor offline e testes.

A partir da raiz:

```powershell
.\.venv314\Scripts\python.exe -m app.vagas
.\.venv314\Scripts\python.exe -m app.contadorPolichinelos
.\.venv314\Scripts\python.exe -m app.escadas
```

Shopping requer `app/requirements-examples.txt`. Todos aceitam nome de vídeo, caminho absoluto ou índice da webcam e `--headless --max-frames 30`. `q` ou fim do vídeo encerra e libera recursos. Imports não abrem câmera.

A experiência dos visitantes funciona dentro do navegador em http://localhost:8000, sem janelas externas do OpenCV. Os exemplos de terminal continuam disponíveis para estudo.

Vídeos duplicados foram preservados e seus hashes estão no README. Medições dependem do enquadramento e das regiões calibradas, sem garantia para qualquer distância ou cenário.
