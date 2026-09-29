$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
  Write-Host "Local environment is missing. Starting one-time installation..." -ForegroundColor Yellow
  & (Join-Path $Root "install.ps1")
}
if (-not (Test-Path $Python)) { throw "Installation did not create the Python environment." }
& $Python -c "import fitz, docx, fastapi, uvicorn, multipart" 2>$null
if ($LASTEXITCODE -ne 0) { throw "Dependencies are incomplete. Run install.bat again." }
Write-Host "PDF engine is ready at http://127.0.0.1:8765" -ForegroundColor Green
Write-Host "Keep this window open while converting. Press Ctrl+C to stop." -ForegroundColor DarkGray
& $Python (Join-Path $Root "server.py")
