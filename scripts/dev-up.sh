#!/usr/bin/env bash
# scripts/dev-up.sh
# One-shot fleet boot for local dev (Linux / macOS / Git-Bash on Windows).
# See dev-up.ps1 for the canonical version with full comments.
#
# Brings up: hub local-stack -> backend-core -> middle-core agent_runtime.
# Frontend-core is left to start manually (`cd frontend-core && npm run dev`)
# so it stays in the foreground for HMR.
#
# Secrets come from Azure Key Vault (akv01-agentarmy), exported into this
# shell's env at boot — never written to disk. After this script exits,
# `export`ed values persist only for the rest of this shell session.
set -euo pipefail

SKIP_LOCAL_STACK=0; SKIP_BACKEND=0; SKIP_MIDDLE=0; DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --skip-local-stack) SKIP_LOCAL_STACK=1 ;;
    --skip-backend)     SKIP_BACKEND=1 ;;
    --skip-middle)      SKIP_MIDDLE=1 ;;
    --dry-run)          DRY_RUN=1 ;;
    -h|--help) sed -n '1,15p' "$0"; exit 0 ;;
    *) echo "Unknown flag: $arg" >&2; exit 2 ;;
  esac
done

KV="akv01-agentarmy"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SIBLING_ROOT="$(cd "$REPO_ROOT/.." && pwd)"

step() { printf "\033[36m==> %s\033[0m\n" "$1"; }
ok()   { printf "  \033[32m[OK]\033[0m %s\n" "$1"; }
sk()   { printf "  \033[33m[SKIP]\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m[WARN]\033[0m %s\n" "$1"; }

ensure_az_login() {
  # You and Claude Code share the same Azure principal; ~/.azure/ cached creds are
  # the only ambient auth. If expired, all KV reads silently return nothing.
  local acct
  acct=$(az account show --query "user.name" -o tsv 2>/dev/null || true)
  if [[ -z "$acct" ]]; then
    warn "no active az session — running 'az login'"
    az login --only-show-errors >/dev/null
    acct=$(az account show --query "user.name" -o tsv 2>/dev/null || true)
    [[ -n "$acct" ]] || { echo "az login failed" >&2; exit 1; }
  fi
  printf "  [auth] az: %s\n" "$acct"
  # Fail fast on KV access instead of N silent secret skips.
  if ! az keyvault secret list --vault-name "$KV" --query "[0].name" -o tsv >/dev/null 2>&1; then
    echo "KV access check failed: '$acct' cannot list $KV. Verify access policy (Get/List on Secrets) or RBAC role." >&2
    exit 1
  fi
}

kv_get() {
  local v
  v=$(az keyvault secret show --vault-name "$KV" --name "$1" --query value -o tsv 2>/dev/null || true)
  [[ -n "$v" ]] || { warn "KV: '$1' not found in $KV"; return 1; }
  printf '%s' "$v"
}

# --- 1. Hub local-stack -------------------------------------------------------
if [[ $SKIP_LOCAL_STACK -eq 0 ]]; then
  step "Hub local-stack (ArcadeDB + Postgres + NATS + event-bridge + Fuseki)"
  STACK_DIR="$REPO_ROOT/templates/local-stack"
  if [[ $DRY_RUN -eq 1 ]]; then
    sk "(dry-run) docker compose -f $STACK_DIR/docker-compose.yml up -d"
  else
    docker compose -f "$STACK_DIR/docker-compose.yml" up -d
    ok "local-stack up"
  fi
else sk "local-stack (--skip-local-stack)"; fi

# --- 2. Secret hydration from KV ----------------------------------------------
step "Verify az auth + KV access"
[[ $DRY_RUN -eq 0 ]] && ensure_az_login
step "Hydrate secrets from KV $KV into this shell env"
# name_in_env=secret_in_kv
SECRETS=(
  "TAVILY_API_KEY=tavily-api"
  "AZURE_EMBED_API_KEY=embed-v-4-0"
  "ARCADEDB_PASSWORD=arcadedb-root-password"
  "CEREBRAS_API_KEY=cerebras-api"
  "ANTHROPIC_API_KEY=claude-code-oauth-token"
  "OPENAI_API_KEY=openai-api"
)
for pair in "${SECRETS[@]}"; do
  envname="${pair%%=*}"; kvname="${pair##*=}"
  if [[ $DRY_RUN -eq 1 ]]; then
    sk "(dry-run) would resolve $envname from $KV/$kvname"; continue
  fi
  if v=$(kv_get "$kvname"); then
    export "$envname=$v"
    ok "$envname <- akv:$kvname (len=${#v})"
  fi
done

# --- 3. backend-core ----------------------------------------------------------
if [[ $SKIP_BACKEND -eq 0 ]]; then
  step "backend-core (uvicorn :8000) — backgrounded"
  BC_DIR="$SIBLING_ROOT/backend-core"
  if [[ ! -d "$BC_DIR" ]]; then
    warn "$BC_DIR not found — clone it next to AgentArmy or use --skip-backend"
  elif [[ $DRY_RUN -eq 1 ]]; then
    sk "(dry-run) uvicorn app.main:app --reload --port 8000 (cwd=$BC_DIR)"
  else
    ( cd "$BC_DIR" && nohup uvicorn app.main:app --reload --port 8000 >/tmp/backend-core.log 2>&1 & )
    ok "backend-core PID=$! (log: /tmp/backend-core.log)"
  fi
else sk "backend-core (--skip-backend)"; fi

# --- 4. middle-core agent_runtime --------------------------------------------
if [[ $SKIP_MIDDLE -eq 0 ]]; then
  step "middle-core agent_runtime (uvicorn :8001) — backgrounded"
  MC_DIR="$SIBLING_ROOT/middle-core"
  if [[ ! -d "$MC_DIR" ]]; then
    warn "$MC_DIR not found — clone it next to AgentArmy or use --skip-middle"
  elif [[ $DRY_RUN -eq 1 ]]; then
    sk "(dry-run) uvicorn agent_runtime.app:create_app --factory --port 8001 (cwd=$MC_DIR)"
  else
    ( cd "$MC_DIR" && nohup uvicorn agent_runtime.app:create_app --factory --port 8001 >/tmp/middle-core.log 2>&1 & )
    ok "middle-core agent_runtime PID=$! (log: /tmp/middle-core.log)"
  fi
else sk "middle-core (--skip-middle)"; fi

# --- 5. Health summary --------------------------------------------------------
step "Health summary"
echo "  local-stack    -> bash $REPO_ROOT/templates/local-stack/local-stack-doctor.sh"
echo "  backend-core   -> curl -fsS http://localhost:8000/health/ready"
echo "  middle-core    -> curl -fsS http://localhost:8001/health"
echo "  frontend-core  -> start manually: cd ../frontend-core && npm run dev"
echo ""
echo "Tip: source this script (\". scripts/dev-up.sh\") if you want the KV-loaded vars to persist in your shell."
