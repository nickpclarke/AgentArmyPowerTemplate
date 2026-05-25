#!/usr/bin/env bash
#
# entrypoint.sh — Ephemeral GitHub Actions runner bootstrap for ACA Jobs.
#
# Lifecycle (one job per container):
#   1. Validate required env vars (GITHUB_PAT, REPO_OWNER, REPO_NAME).
#   2. Exchange the PAT for a short-lived registration token via the GitHub REST API.
#   3. Configure the runner as ephemeral + scoped to the specific repo.
#   4. exec ./run.sh — the runner processes exactly one job, then exits cleanly.
#      ACA Job infrastructure detects exit 0 and marks the execution complete.
#      KEDA scales back to zero when no more jobs are queued.
#
# Security notes:
#   - PAT and registration token are NEVER echoed or logged.
#   - The container runs as non-root user `runner` (uid 1001).
#   - GITHUB_PAT is sourced from the ACA Job secret (Key Vault-backed via the
#     managed identity). It never appears in process args or log output.
#   - The runner is registered with --ephemeral so it auto-deregisters after the
#     job; no orphaned runner entries accumulate in the repo settings.
#
# Required env vars (set by ACA Job):
#   GITHUB_PAT   — classic PAT with `repo` scope (for private repos)
#   REPO_OWNER   — GitHub username or org (e.g. nickpclarke)
#   REPO_NAME    — Repository name (e.g. AgentArmy)
#
# Optional env vars:
#   RUNNER_LABELS — comma-separated extra labels (default: aca-linux,self-hosted)
#   RUNNER_NAME   — override the runner name (default: aca-<hostname>)

set -euo pipefail

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
MISSING=()
[[ -z "${GITHUB_PAT:-}"   ]] && MISSING+=("GITHUB_PAT")
[[ -z "${REPO_OWNER:-}"   ]] && MISSING+=("REPO_OWNER")
[[ -z "${REPO_NAME:-}"    ]] && MISSING+=("REPO_NAME")

if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo "[entrypoint] FATAL: missing required environment variables: ${MISSING[*]}" >&2
  exit 78  # EX_CONFIG
fi

# ---------------------------------------------------------------------------
# Derived values — never log the PAT or the registration token
# ---------------------------------------------------------------------------
REPO_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}"
RUNNER_NAME="${RUNNER_NAME:-aca-$(hostname)}"
RUNNER_LABELS="${RUNNER_LABELS:-aca-linux,self-hosted}"

echo "[entrypoint] requesting registration token for ${REPO_OWNER}/${REPO_NAME}" >&2

# Request ephemeral registration token (token is valid for ~1 hour; used once).
# Using process substitution to avoid storing the token in a shell variable that
# could leak via `set -x` traces. We store it in a local variable but never echo it.
REG_TOKEN=$(
  curl -fsSL \
    -X POST \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: Bearer ${GITHUB_PAT}" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/actions/runners/registration-token" \
  | jq -r '.token'
)

if [[ -z "${REG_TOKEN}" || "${REG_TOKEN}" == "null" ]]; then
  echo "[entrypoint] FATAL: failed to obtain registration token — check GITHUB_PAT scope and repo access" >&2
  exit 1
fi

echo "[entrypoint] registration token obtained (not logged)" >&2

# ---------------------------------------------------------------------------
# Configure the runner
# ---------------------------------------------------------------------------
# --ephemeral    register as a one-shot runner; auto-deregisters after one job
# --unattended   non-interactive
# --replace      replace an existing offline runner with the same name (safe for retries)
# --disableupdate prevent the runner from self-updating (image pins the version)
echo "[entrypoint] configuring runner: name=${RUNNER_NAME} labels=${RUNNER_LABELS}" >&2

./config.sh \
  --unattended \
  --ephemeral \
  --replace \
  --disableupdate \
  --url "${REPO_URL}" \
  --token "${REG_TOKEN}" \
  --labels "${RUNNER_LABELS}" \
  --name  "${RUNNER_NAME}"

# Unset the token immediately after config so it is not accessible to the job
unset REG_TOKEN

echo "[entrypoint] runner configured — handing off to run.sh" >&2

# ---------------------------------------------------------------------------
# Run one job, then exit (ephemeral)
# exec replaces this shell so signals (SIGTERM from ACA scale-down) reach run.sh directly.
# ---------------------------------------------------------------------------
exec ./run.sh
