param([switch]$Dev, [switch]$NoBrowser)
& (Join-Path (Split-Path $PSScriptRoot -Parent) 'start.ps1') -Dev:$Dev -NoBrowser:$NoBrowser
