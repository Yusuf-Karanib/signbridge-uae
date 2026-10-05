$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ProjectRoot

$BundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if (Test-Path -LiteralPath $BundledPython) {
    $Python = $BundledPython
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $Python = "py"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $Python = "python"
} else {
    throw "Python 3.12 was not found. Install Python 3.12, then run setup.ps1 again."
}

if (-not (Test-Path -LiteralPath ".venv\Scripts\python.exe")) {
    & $Python -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
& ".\.venv\Scripts\python.exe" scripts\download_model.py

Write-Host ""
Write-Host "Setup complete. Double-click 'Start SignBridge.vbs' to open SignBridge without a terminal window."

