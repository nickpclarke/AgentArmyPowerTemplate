<#
.SYNOPSIS
  One-shot setup for the AgentArmy ArcadeDB image (Windows PowerShell / pwsh).
.DESCRIPTION
  1. generate local secrets (if missing)
  2. build + start the container (docker compose)
  3. wait until healthy
  4. prove it with agentarmy-doctor (if node is available)
  5. emit MCP client wiring to a gitignored env file
.EXAMPLE
  .\setup.ps1
.EXAMPLE
  .\setup.ps1 -Down
#>
[CmdletBinding()]
param([switch]$Down)

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

$Compose    = 'examples/compose.arcadedb-server.example.yml'
$Secrets    = 'examples/.secrets'
$RootFile   = Join-Path $Secrets 'arcadedb_root_password.txt'
$ReaderFile = Join-Path $Secrets 'arcadedb_password.txt'
$McpEnv     = Join-Path $Secrets 'mcp-client.env'

if ($Down) {
  docker compose -f $Compose down -v
  Write-Host "stack down (secrets kept under $Secrets/)"
  return
}

# 1. Secrets. Alnum only — avoids the defaultDatabases delimiters : [ ] { }.
function New-Password {
  -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object { [char]$_ })
}
New-Item -ItemType Directory -Force -Path $Secrets | Out-Null
foreach ($f in @($RootFile, $ReaderFile)) {
  if (-not (Test-Path $f) -or (Get-Item $f).Length -eq 0) {
    # -NoNewline so the file holds exactly the password (entrypoint trims, but be exact).
    [IO.File]::WriteAllText((Resolve-Path -LiteralPath (New-Item -ItemType File -Force -Path $f)).Path, (New-Password))
    Write-Host "generated $f"
  }
}

# 2. Build + start.
docker compose -f $Compose up -d --build

# 3. Wait for healthy.
$cid = (docker compose -f $Compose ps -q arcadedb).Trim()
Write-Host -NoNewline 'waiting for healthy'
$status = 'starting'
for ($i = 0; $i -lt 60; $i++) {
  $status = (docker inspect --format '{{.State.Health.Status}}' $cid 2>$null)
  if ($status -eq 'healthy') { Write-Host ' ok'; break }
  Write-Host -NoNewline '.'; Start-Sleep -Seconds 2
}
if ($status -ne 'healthy') {
  Write-Host ' FAILED'
  docker compose -f $Compose logs --tail=40 arcadedb
  exit 1
}

# 4. Prove it (best-effort).
if (Get-Command node -ErrorAction SilentlyContinue) {
  Write-Host 'running agentarmy-doctor arcadedb...'
  $env:ARCADEDB_URL = 'http://localhost:2480'
  $env:ARCADEDB_DATABASE = 'knowledge'
  $env:ARCADEDB_USER = 'platform_reader'
  $env:ARCADEDB_PASSWORD_FILE = (Resolve-Path -LiteralPath $ReaderFile).Path
  try { node ../../tools/agentarmy-doctor.mjs arcadedb } catch { }
}

# 5. Emit MCP client wiring (Basic = turnkey; Bearer = optional, hardened).
$readerPw = (Get-Content -Raw -LiteralPath $ReaderFile).Trim()
$basic = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("platform_reader:$readerPw"))
@(
  '# MCP client wiring for the AgentArmy ArcadeDB image (gitignored).'
  'ARCADEDB_MCP_URL=http://localhost:2480/api/v1/mcp'
  '# Turnkey: Basic auth as the read-only platform_reader user.'
  "ARCADEDB_MCP_BASIC=$basic"
  '# Hardened alt: create a token in ArcadeDB Studio -> Security, then:'
  '# ARCADEDB_MCP_TOKEN='
) | Set-Content -LiteralPath $McpEnv -Encoding utf8

Write-Host ''
Write-Host 'ArcadeDB + MCP ready at http://localhost:2480/api/v1/mcp'
Write-Host "MCP client env written to $McpEnv (gitignored)."
Write-Host 'Load it, then point .mcp.json at:  "Authorization": "Basic ${ARCADEDB_MCP_BASIC}"'
Write-Host 'Tear down with:  .\setup.ps1 -Down'
