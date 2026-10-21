$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    throw 'Ambiente ausente. Siga a instalação no README.md primeiro.'
}
$env:MPLCONFIGDIR = Join-Path $PSScriptRoot '.artifacts/matplotlib'
Write-Host 'VISÃO / Abra http://localhost:8000. Ctrl+C encerra o servidor.'
& .venv/Scripts/python.exe -m uvicorn app.server:app --host 127.0.0.1 --port 8000 --ws-max-size 450000 --ws-max-queue 1
