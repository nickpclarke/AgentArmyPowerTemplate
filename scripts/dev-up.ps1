# scripts/dev-up.ps1
# One-shot fleet boot for local dev (Windows / PowerShell).
# Brings up: hub local-stack -> backend-core -> middle-core agent_runtime
# Frontend-core is left for you to start with `npm run dev` from its repo,
# so it stays in the foreground for fast HMR feedback.
#
# Secrets are NEVER read from .env on disk. Every secret is pulled from Azure
# Key Vault (akv01-agentarmy) into the *current process env* at boot, so the
# spawned backend/middle processes inherit them. After this script exits, the
# secrets persist in this PowerShell session only — close the shell to clear.
#
# Requires: docker, az (logged in), python on PATH, the repo checked out at
# the standard fleet layout: C:\Dev\AgentArmy, C:\Dev\backend-core,
# C:\Dev\middle-core (parallel sibling clones).

[CmdletBinding()]
param(
    [switch]$SkipLocalStack,
    [switch]$SkipBackend,
    [switch]$SkipMiddle,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$KV = "akv01-agentarmy"

function Ensure-AzLogin {
    # Both you and Claude Code share the same Azure principal — `~/.azure/` cached
    # creds are the only ambient auth. If they've expired (default ~24h), all KV
    # reads silently return nothing. Detect early and re-prompt.
    $acct = az account show --query "user.name" -o tsv 2>$null
    if (-not $acct) {
        Write-Host "  [auth] no active az session — running 'az login'" -ForegroundColor Yellow
        az login --only-show-errors 1>$null
        $acct = az account show --query "user.name" -o tsv 2>$null
        if (-not $acct) { throw "az login failed — re-run dev-up after fixing auth" }
    }
    Write-Host "  [auth] az: $acct" -ForegroundColor DarkGray

    # Probe KV access so we fail fast with a clear message instead of N silent skips.
    $probe = az keyvault secret list --vault-name $KV --query "[0].name" -o tsv 2>$null
    if (-not $probe) {
        throw "KV access check failed: '$acct' cannot list $KV. Verify access policy (Get/List on Secrets) or RBAC role assignment."
    }
}

function Get-Kv-Secret([string]$name) {
    $val = az keyvault secret show --vault-name $KV --name $name --query value -o tsv 2>$null
    if (-not $val) { throw "KV: failed to read '$name' from $KV (secret missing or no get permission)" }
    return $val
}

function Step([string]$msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function OK([string]$msg)   { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Skip([string]$msg) { Write-Host "  [SKIP] $msg" -ForegroundColor Yellow }

$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName  # C:\Dev\AgentArmy
$siblingRoot = (Get-Item $repoRoot).Parent.FullName   # C:\Dev

# --- 1. Hub local-stack (ArcadeDB + Postgres + NATS + event-bridge + Fuseki) ---
if (-not $SkipLocalStack) {
    Step "Hub local-stack (ArcadeDB + Postgres + NATS + event-bridge + Fuseki)"
    $stackDir = Join-Path $repoRoot "templates\local-stack"
    if ($DryRun) {
        Skip "(dry-run) docker compose -f $stackDir\docker-compose.yml up -d"
    } else {
        docker compose -f (Join-Path $stackDir "docker-compose.yml") up -d
        OK "local-stack up"
    }
} else { Skip "local-stack (--SkipLocalStack)" }

# --- 2. Secret hydration from KV ----------------------------------------------
Step "Verify az auth + KV access"
if (-not $DryRun) { Ensure-AzLogin }
Step "Hydrate secrets from KV $KV into this process env"
$secretMap = @{
    "TAVILY_API_KEY"        = "tavily-api"
    "AZURE_EMBED_API_KEY"   = "embed-v-4-0"
    "ARCADEDB_PASSWORD"     = "arcadedb-root-password"
    "CEREBRAS_API_KEY"      = "cerebras-api"
    "ANTHROPIC_API_KEY"     = "claude-code-oauth-token"   # adjust if a dedicated secret exists
    "OPENAI_API_KEY"        = "openai-api"
}
foreach ($k in $secretMap.Keys) {
    if ($DryRun) {
        Skip "(dry-run) would resolve $k from $KV/$($secretMap[$k])"
        continue
    }
    try {
        $v = Get-Kv-Secret $secretMap[$k]
        [Environment]::SetEnvironmentVariable($k, $v, "Process")
        OK ("{0} <- akv:{1} (len={2})" -f $k, $secretMap[$k], $v.Length)
    } catch {
        Write-Host "  [WARN] $k <- akv:$($secretMap[$k]) — not found in KV (skipping)" -ForegroundColor DarkYellow
    }
}

# --- 3. backend-core (FastAPI on :8000) ---------------------------------------
if (-not $SkipBackend) {
    Step "backend-core (uvicorn :8000)"
    $bcDir = Join-Path $siblingRoot "backend-core"
    if (-not (Test-Path $bcDir)) {
        Write-Host "  [WARN] $bcDir not found — clone it next to AgentArmy or use --SkipBackend" -ForegroundColor DarkYellow
    } elseif ($DryRun) {
        Skip "(dry-run) uvicorn app.main:app --reload --port 8000 (cwd=$bcDir)"
    } else {
        # Run in a new PowerShell window so the parent shell stays free for you to start frontend etc.
        Start-Process powershell -ArgumentList "-NoExit","-Command","Set-Location '$bcDir'; uvicorn app.main:app --reload --port 8000"
        OK "backend-core launched in new window (Ctrl+C to stop)"
    }
} else { Skip "backend-core (--SkipBackend)" }

# --- 4. middle-core agent_runtime (Python, FastAPI on :8001) ------------------
if (-not $SkipMiddle) {
    Step "middle-core agent_runtime (uvicorn :8001)"
    $mcDir = Join-Path $siblingRoot "middle-core"
    if (-not (Test-Path $mcDir)) {
        Write-Host "  [WARN] $mcDir not found — clone it next to AgentArmy or use --SkipMiddle" -ForegroundColor DarkYellow
    } elseif ($DryRun) {
        Skip "(dry-run) uvicorn agent_runtime.app:create_app --factory --port 8001 (cwd=$mcDir)"
    } else {
        Start-Process powershell -ArgumentList "-NoExit","-Command","Set-Location '$mcDir'; uvicorn agent_runtime.app:create_app --factory --port 8001"
        OK "middle-core agent_runtime launched in new window"
    }
} else { Skip "middle-core (--SkipMiddle)" }

# --- 5. Health check ----------------------------------------------------------
Step "Health summary"
Write-Host "  local-stack    -> bash $repoRoot\templates\local-stack\local-stack-doctor.sh"
Write-Host "  backend-core   -> http://localhost:8000/health/ready"
Write-Host "  middle-core    -> http://localhost:8001/health"
Write-Host "  frontend-core  -> start manually: cd C:\Dev\frontend-core; npm run dev"
Write-Host ""
Write-Host "Tip: keep this PowerShell session open — the KV-loaded secrets live in this process env." -ForegroundColor DarkGray
