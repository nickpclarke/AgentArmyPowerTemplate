#!/usr/bin/env pwsh
# One-shot setup for the AgentArmy Fuseki super-image (Windows PowerShell / pwsh).
# Mirrors setup.sh. Needs `sh` on PATH (Git Bash / WSL) for the shared scripts.
#
# Usage:  .\setup.ps1          # bring up + prove
#         .\setup.ps1 -Down    # tear down (keeps the secret), then exit
param([switch]$Down)
$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

$compose = "docker compose -f examples/compose.fuseki.example.yml"
$pwFile  = "examples/.secrets/fuseki_admin_password.txt"

if ($Down) {
  Invoke-Expression "$compose down -v"
  Write-Host "stack down (secret kept under examples/.secrets/)"
  exit 0
}

# 1. Secret (32-char alphanumeric).
New-Item -ItemType Directory -Force -Path (Split-Path $pwFile) | Out-Null
if (-not (Test-Path $pwFile) -or ((Get-Item $pwFile).Length -eq 0)) {
  $chars = ([char[]]('a'..'z') + [char[]]('A'..'Z') + [char[]]('0'..'9'))
  $pw = -join (1..32 | ForEach-Object { Get-Random -InputObject $chars })
  [System.IO.File]::WriteAllText((Resolve-Path -LiteralPath (Split-Path $pwFile)).Path + '/' + (Split-Path $pwFile -Leaf), $pw)
  Write-Host "generated $pwFile"
}

# 2. Build + start.
Invoke-Expression "$compose up -d --build"

# 3. Doctor.
Write-Host "running the Fuseki super-image doctor..."
sh scripts/fuseki-doctor.sh

Write-Host ""
Write-Host "Fuseki ready: SPARQL/Studio on http://localhost:3030  (dataset: knowledge)"
Write-Host "Tear down with:  .\setup.ps1 -Down"
