param([switch]$DownloadModels)
$ErrorActionPreference = 'Stop'
$studioRoot = Split-Path $PSScriptRoot -Parent
Set-Location $studioRoot
foreach ($dependency in @('uv', 'git', 'node', 'npm.cmd', 'ffmpeg')) {
    if (-not (Get-Command $dependency -ErrorAction SilentlyContinue)) { throw "Missing prerequisite: $dependency" }
}
if (-not (Test-Path 'vendor/index-tts/pyproject.toml')) {
    git clone https://github.com/index-tts/index-tts.git vendor/index-tts
    if ($LASTEXITCODE -ne 0) { throw 'Upstream clone failed.' }
    git -C vendor/index-tts checkout ee40fa7d6c6b8a2c7f06105f9f1e65775b74868c
    if ($LASTEXITCODE -ne 0) { throw 'Upstream revision checkout failed.' }
}
uv python install 3.11.9
if ($LASTEXITCODE -ne 0) { throw 'Python installation failed.' }
Push-Location vendor/index-tts
try { uv sync --frozen --python 3.11.9; if ($LASTEXITCODE -ne 0) { throw 'IndexTTS dependencies failed.' } } finally { Pop-Location }
$studioPython = Join-Path $studioRoot 'vendor/index-tts/.venv/Scripts/python.exe'
uv pip install --python $studioPython --index-url https://pypi.org/simple -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Studio dependencies failed.' }
Push-Location frontend
try {
    npm.cmd ci
    if ($LASTEXITCODE -ne 0) { throw 'Frontend installation failed.' }
    npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
} finally { Pop-Location }
if ($DownloadModels) {
    & $studioPython scripts/download_models.py
    if ($LASTEXITCODE -ne 0) { throw 'Model download failed. Rerun to resume.' }
}
Write-Host 'Start with .\start.ps1. Model provisioning: .\scripts\install.ps1 -DownloadModels'
