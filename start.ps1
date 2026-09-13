param([switch]$Dev, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$studioRoot = $PSScriptRoot
Set-Location $studioRoot
$studioPython = Join-Path $studioRoot 'vendor/index-tts/.venv/Scripts/python.exe'
if (-not (Test-Path $studioPython)) { throw 'Run scripts/install.ps1 first.' }
if (-not $Dev -and -not (Test-Path 'frontend/dist/index.html')) { throw 'Build the frontend with npm run build in frontend, or use -Dev.' }
New-Item -ItemType Directory -Force logs | Out-Null
$existingListener = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($existingListener) { throw 'Port 8000 is already in use. Close the existing studio or service first.' }
$studioProcess = Start-Process -FilePath $studioPython -ArgumentList @('-m','uvicorn','backend.main:app','--host','127.0.0.1','--port','8000') -WorkingDirectory $studioRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput 'logs/server.log' -RedirectStandardError 'logs/server-error.log'
$studioUrl = 'http://127.0.0.1:8000'
if ($Dev) {
    $npmFile = (Get-Command npm.cmd).Source
    Start-Process -FilePath $npmFile -ArgumentList @('run','dev') -WorkingDirectory (Join-Path $studioRoot 'frontend') -WindowStyle Hidden
    $studioUrl = 'http://localhost:5173'
}
for ($attempt = 0; $attempt -lt 60; $attempt++) {
    if ($studioProcess.HasExited) { throw 'Server failed. See logs/server-error.log.' }
    try { $null = Invoke-RestMethod 'http://127.0.0.1:8000/api/system/model'; break } catch { Start-Sleep -Milliseconds 500 }
}
if (-not $NoBrowser) { Start-Process $studioUrl }
Write-Host "Local Voice Studio: $studioUrl (server process $($studioProcess.Id))"
