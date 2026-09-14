param([switch]$Dev, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$studioRoot = $PSScriptRoot
Set-Location $studioRoot
$isWindows = $env:OS -eq 'Windows_NT'
$studioPython = if ($isWindows) {
    Join-Path $studioRoot 'vendor/index-tts/.venv/Scripts/python.exe'
} else {
    Join-Path $studioRoot 'vendor/index-tts/.venv/bin/python'
}
if (-not (Test-Path $studioPython)) { throw 'Run scripts/install.ps1 or ./scripts/install.sh first.' }
if (-not $Dev -and -not (Test-Path 'frontend/dist/index.html')) { throw 'Build the frontend with npm run build in frontend, or use -Dev.' }
New-Item -ItemType Directory -Force logs | Out-Null
$listenerPids = @()
if (Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue) {
    $listenerPids = @(Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique)
} elseif (Get-Command lsof -ErrorAction SilentlyContinue) {
    $listenerPids = @((lsof -nP -iTCP:8000 -sTCP:LISTEN -t 2>$null) | Where-Object { $_ })
}
foreach ($listenerPid in $listenerPids) {
    Write-Host "Stopping the existing process on port 8000: $listenerPid"
    Stop-Process -Id $listenerPid -Force -ErrorAction SilentlyContinue
}
if ($listenerPids.Count -gt 0) {
    Start-Sleep -Milliseconds 400
}
$env:PYTORCH_ENABLE_MPS_FALLBACK = '1'
if ($isWindows) {
    $studioProcess = Start-Process -FilePath $studioPython -ArgumentList @('-m','uvicorn','backend.main:app','--host','127.0.0.1','--port','8000') -WorkingDirectory $studioRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput 'logs/server.log' -RedirectStandardError 'logs/server-error.log'
} else {
    $studioProcess = Start-Process -FilePath $studioPython -ArgumentList @('-m','uvicorn','backend.main:app','--host','127.0.0.1','--port','8000') -WorkingDirectory $studioRoot -PassThru -RedirectStandardOutput 'logs/server.log' -RedirectStandardError 'logs/server-error.log'
}
$studioUrl = 'http://127.0.0.1:8000'
if ($Dev) {
    $npmName = if ($isWindows) { 'npm.cmd' } else { 'npm' }
    $npmFile = (Get-Command $npmName).Source
    if ($isWindows) {
        Start-Process -FilePath $npmFile -ArgumentList @('run','dev') -WorkingDirectory (Join-Path $studioRoot 'frontend') -WindowStyle Hidden
    } else {
        Start-Process -FilePath $npmFile -ArgumentList @('run','dev') -WorkingDirectory (Join-Path $studioRoot 'frontend')
    }
    $studioUrl = 'http://localhost:5173'
}
for ($attempt = 0; $attempt -lt 60; $attempt++) {
    if ($studioProcess.HasExited) { throw 'Server failed. See logs/server-error.log.' }
    try { $null = Invoke-RestMethod 'http://127.0.0.1:8000/api/system/model'; break } catch { Start-Sleep -Milliseconds 500 }
}
if (-not $NoBrowser) {
    if ($isWindows) {
        Start-Process $studioUrl
    } elseif (Test-Path '/usr/bin/open') {
        & /usr/bin/open $studioUrl
    } elseif (Get-Command xdg-open -ErrorAction SilentlyContinue) {
        & xdg-open $studioUrl
    }
}
Write-Host "Local Voice Studio: $studioUrl (server process $($studioProcess.Id))"
