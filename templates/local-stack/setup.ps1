# AgentArmy local-stack — Windows PowerShell setup.
# Mirror of setup.sh: generate secrets, build, up, doctor.
# Usage:  .\setup.ps1            (build + up)
#         .\setup.ps1 -Down      (compose down — keeps volumes)
#         .\setup.ps1 -Wipe      (compose down --volumes — drops data)

[CmdletBinding()]
param(
    [switch]$Down,
    [switch]$Wipe
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

if ($Down) {
    Write-Host "=== DOWN (keeping volumes — use -Wipe to drop data) ==="
    docker compose down
    return
}
if ($Wipe) {
    Write-Host "=== WIPE (down + drop all volumes — destroys local data) ==="
    docker compose down --volumes
    return
}

New-Item -ItemType Directory -Force -Path .secrets | Out-Null

function New-DevSecret {
    param([string]$Name)
    $path = ".secrets/$Name.txt"
    if (-not (Test-Path $path) -or (Get-Item $path).Length -eq 0) {
        $chars = ([char[]](48..57 + 65..90 + 97..122))
        $value = -join (1..32 | ForEach-Object { Get-Random -InputObject $chars })
        # Write WITHOUT a trailing newline — pg + arcadedb choke on whitespace
        [System.IO.File]::WriteAllText((Resolve-Path .).Path + "\$path", $value)
        Write-Host "  generated $path"
    }
}

Write-Host "=== preparing .secrets/ ==="
New-DevSecret arcadedb_root_password
New-DevSecret arcadedb_password
New-DevSecret postgres_password
New-DevSecret github_webhook_secret
New-DevSecret fuseki_admin_password

Set-Content -Path .secrets/.gitignore -Value @"
*.txt
!README.md
"@

Write-Host ""
Write-Host "=== building all 5 services ==="
docker compose build

Write-Host ""
Write-Host "=== bringing the stack up (compose up -d --wait) ==="
docker compose up -d --wait

Write-Host ""
Write-Host "=== running local-stack doctor ==="
# Doctor is bash; we run it through Git Bash if present, otherwise via docker.
$bash = (Get-Command bash -ErrorAction SilentlyContinue)
if ($bash) {
    & bash "$here/local-stack-doctor.sh"
} else {
    Write-Host "(bash not on PATH — running doctor inside the postgres container instead)"
    docker run --rm --network agentarmy-local-stack_default `
        -v "${here}:/work" -w /work alpine:3.20 `
        sh -c "apk add --no-cache bash curl >/dev/null && bash /work/local-stack-doctor.sh"
}

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "doctor failed — leaving the stack running for poking."
    Write-Host "logs:   docker compose logs --tail=80"
    exit 1
}

Write-Host ""
Write-Host "══════════════════════════════════════════════════════════════════════════"
Write-Host "  AgentArmy local-stack is UP. Endpoints:"
Write-Host ""
Write-Host "    ArcadeDB Studio    http://localhost:2480"
Write-Host "    Postgres (DBOS)    postgresql://dbos@localhost:5432/dbos_system"
Write-Host "    NATS client        nats://localhost:4222   (monitor http://localhost:8222)"
Write-Host "    Event-bridge       http://localhost:8080/healthz"
Write-Host "    Fuseki + SHACL     http://localhost:3030"
Write-Host ""
Write-Host "  Down (keep data):   .\setup.ps1 -Down"
Write-Host "  Wipe (drop data):   .\setup.ps1 -Wipe"
Write-Host "══════════════════════════════════════════════════════════════════════════"
