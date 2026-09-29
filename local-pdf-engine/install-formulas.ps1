$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { & (Join-Path $Root "install.ps1") }
& $Python -m pip install --prefer-binary -r (Join-Path $Root "requirements-formula.txt")
$CheckpointDir = & $Python -c "import pathlib,pix2tex; print(pathlib.Path(pix2tex.__file__).resolve().parent / 'model' / 'checkpoints')"
$Weights = Join-Path $CheckpointDir "weights.pth"
$Resizer = Join-Path $CheckpointDir "image_resizer.pth"
if (-not (Test-Path $Weights) -or (Get-Item $Weights).Length -lt 90000000) {
  Write-Host "Downloading formula weights with resumable Windows transfer..." -ForegroundColor Cyan
  Start-BitsTransfer -Source "https://github.com/lukas-blecher/LaTeX-OCR/releases/download/v0.0.1/weights.pth" -Destination $Weights
}
if (-not (Test-Path $Resizer)) {
  Start-BitsTransfer -Source "https://github.com/lukas-blecher/LaTeX-OCR/releases/download/v0.0.1/image_resizer.pth" -Destination $Resizer
}
if ((Get-Item $Weights).Length -ne 102113875 -or (Get-FileHash $Weights -Algorithm SHA256).Hash -ne "A63D9141C53D266CB682FB5A8BD83BD5CBE283145E0E78EBDC0F895195A1DFAA") {
  throw "Formula weights failed integrity validation. Run install-formulas.bat again."
}
if ((Get-Item $Resizer).Length -ne 19441973) { throw "Formula image-resizer weights are incomplete." }
& $Python -c "from pix2tex.cli import LatexOCR; LatexOCR(); print('Formula model verified.')"
Write-Host "Enhanced formula recognition is installed and will be reused locally." -ForegroundColor Green
