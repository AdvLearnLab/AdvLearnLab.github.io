$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Venv = Join-Path $Root ".venv"

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
  Write-Host "Python 3.10 or 3.11 is required. Install it from https://www.python.org/downloads/" -ForegroundColor Red
  Read-Host "Press Enter to exit"
  exit 1
}

if (-not (Test-Path $Venv)) { py -3 -m venv $Venv }
& "$Venv\Scripts\python.exe" -m pip install --upgrade pip
& "$Venv\Scripts\pip.exe" install -r (Join-Path $Root "requirements.txt")
Write-Host "Installation complete. Run start.ps1 when using the PDF converter." -ForegroundColor Green
Read-Host "Press Enter to exit"

