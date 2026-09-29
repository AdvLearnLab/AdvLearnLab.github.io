$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Venv = Join-Path $Root ".venv"

function Find-Python {
  $commands = @("py", "python", "python3")
  foreach ($command in $commands) {
    $found = Get-Command $command -ErrorAction SilentlyContinue
    if ($found -and $found.Source -notlike "*\Microsoft\WindowsApps\*") {
      & $found.Source --version *> $null
      if ($LASTEXITCODE -eq 0) { return $found.Source }
    }
  }
  $bundled = Get-ChildItem "$env:USERPROFILE\.cache\codex-runtimes\*\dependencies\python\python.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($bundled) { return $bundled.FullName }
  return $null
}

$PythonCommand = Find-Python
if (-not $PythonCommand) {
  Write-Host "Python was not found. Install Python 3.10+ from https://www.python.org/downloads/ and enable Add Python to PATH." -ForegroundColor Red
  exit 1
}

Write-Host "Using Python: $PythonCommand" -ForegroundColor Cyan
if (-not (Test-Path $Venv)) { & $PythonCommand -m venv $Venv }
& "$Venv\Scripts\python.exe" -m pip install --upgrade pip
& "$Venv\Scripts\python.exe" -m pip install --prefer-binary -r (Join-Path $Root "requirements.txt")
Write-Host "Installation complete. You can now double-click start.bat." -ForegroundColor Green
