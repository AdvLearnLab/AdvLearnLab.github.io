$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { & (Join-Path $Root "install.ps1") }
& $Python -m pip install --prefer-binary -r (Join-Path $Root "requirements-formula.txt")
Write-Host "Enhanced formula recognition is installed and will be reused locally." -ForegroundColor Green
