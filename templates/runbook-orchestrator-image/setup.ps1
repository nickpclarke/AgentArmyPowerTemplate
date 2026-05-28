#!/usr/bin/env pwsh
# One-shot setup for the runbook-orchestrator image (Windows PowerShell / pwsh).
# Needs `sh` on PATH (Git Bash / WSL) for the shared doctor script.
param([switch]$Down)
$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

$compose = "docker compose -f examples/compose.runbook.example.yml"

if ($Down) {
  Invoke-Expression "$compose down -v"
  Write-Host "stack down"
  exit 0
}

Invoke-Expression "$compose up -d --build"
Write-Host "running the runbook-orchestrator doctor..."
# Host 8088 (8080 is taken by the platform event-bridge); doctor honors ORCH_URL.
$env:ORCH_URL = "http://localhost:8088"
sh scripts/runbook-doctor.sh
Write-Host ""
Write-Host "orchestrator ready: control API -> http://localhost:8088  ·  NATS internal-only (compose net)"
Write-Host "  GET /runbooks  ·  POST /runbooks/{id}/trigger"
Write-Host "tear down with: .\setup.ps1 -Down"
