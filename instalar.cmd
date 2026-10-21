@echo off
setlocal
cd /d "%~dp0"
py -3.14 -c "import struct, sys; sys.exit(0 if sys.version_info[:2] == (3, 14) and struct.calcsize('P') == 8 else 1)"
if errorlevel 1 (
    echo Instale o Python 3.14 de 64 bits e tente novamente.
    pause
    exit /b 1
)
py -3.14 -m venv .venv314
if errorlevel 1 goto erro
".venv314\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto erro
".venv314\Scripts\python.exe" -m pip install --only-binary=:all: -r app\requirements.txt
if errorlevel 1 goto erro
".venv314\Scripts\python.exe" -m app.prepare_models
if errorlevel 1 goto erro
echo Instalacao concluida. Abra iniciar.cmd para usar o aplicativo.
pause
exit /b 0
:erro
echo A instalacao falhou. Confira o erro acima antes de iniciar o aplicativo.
pause
exit /b 1
