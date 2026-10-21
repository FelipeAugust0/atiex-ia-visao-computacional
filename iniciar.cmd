@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv314\Scripts\python.exe" (
    echo Execute instalar.cmd primeiro.
    pause
    exit /b 1
)
".venv314\Scripts\python.exe" -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 14) else 1)"
if errorlevel 1 (
    echo O ambiente .venv314 precisa usar Python 3.14. Execute instalar.cmd.
    pause
    exit /b 1
)
set "MPLCONFIGDIR=%~dp0.artifacts\matplotlib"
echo Abra http://localhost:8000 no navegador. Ctrl+C encerra o servidor.
".venv314\Scripts\python.exe" -m uvicorn app.server:app --host 127.0.0.1 --port 8000 --ws-max-size 450000 --ws-max-queue 1
if errorlevel 1 (
    pause
    exit /b 1
)
