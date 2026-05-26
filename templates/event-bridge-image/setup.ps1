#!/usr/bin/env pwsh
# One-shot setup for the event-bridge image (Windows PowerShell / pwsh).
# Needs `sh` on PATH (Git Bash / WSL) for the shared scripts.
param([switch]$Down)
$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

$compose = "docker compose -f examples/compose.event-bridge.example.yml"
$pwFile  = "examples/.secrets/github_webhook_secret.txt"

if ($Down) {
  Invoke-Expression "$compose down -v"
  Write-Host "stack down (secret kept under examples/.secrets/)"
  exit 0
}

New-Item -ItemType Directory -Force -Path (Split-Path $pwFile) | Out-Null
if (-not (Test-Path $pwFile) -or ((Get-Item $pwFile).Length -eq 0)) {
  $chars = ([char[]]('a'..'z') + [char[]]('A'..'Z') + [char[]]('0'..'9'))
  $pw = -join (1..48 | ForEach-Object { Get-Random -InputObject $chars })
  [System.IO.File]::WriteAllText((Resolve-Path -LiteralPath (Split-Path $pwFile)).Path + '/' + (Split-Path $pwFile -Leaf), $pw)
  Write-Host "generated $pwFile"
}

Invoke-Expression "$compose up -d --build"
Write-Host "running the event-bridge doctor..."
sh scripts/event-bus-doctor.sh
Write-Host ""
Write-Host "bridge ready: http://localhost:8080/webhooks/github  ·  NATS :4222 / monitor :8222"
Write-Host "tear down with: .\setup.ps1 -Down"
