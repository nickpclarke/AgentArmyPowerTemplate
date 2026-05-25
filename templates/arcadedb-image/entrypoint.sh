#!/usr/bin/env sh
#
# AgentArmy thin-ArcadeDB entrypoint (POSIX sh — the base image has no bash).
#
# Hybrid bootstrap:
#   - BUILD time: read-only MCP posture + doctor-stub schema are baked into the
#     image under /opt/agentarmy/ (see Dockerfile).
#   - FIRST BOOT: this script applies the MCP posture, creates the database +
#     read-only service user, starts the server, then (idempotently) ensures the
#     doctor-stub document types exist.
#
# The base image runs as the non-root user "arcadedb" (uid 1000). Only sh, wget
# (BusyBox), base64 and java are available — do NOT assume bash/curl/jq.
#
# Secrets: passwords are read from *_FILE (preferred) or the plain env var, and
# are never echoed. NOTE: ArcadeDB takes passwords as JVM -D args, so they are
# visible in the in-container process list (/proc) — same as the upstream image.
# Avoid the characters : [ ] { } in the service password (defaultDatabases
# delimiters).

set -eu

ARCADEDB_HOME="${ARCADEDB_HOME:-/home/arcadedb}"
SEED_DIR="/opt/agentarmy"
DB="${ARCADEDB_DATABASE:-knowledge}"
SVC_USER="${ARCADEDB_SERVICE_USER:-platform_reader}"
HTTP_PORT="${ARCADEDB_HTTP_PORT:-2480}"
SERVER_MODE="${ARCADEDB_SERVER_MODE:-production}"
READY_URL="http://localhost:${HTTP_PORT}/api/v1/ready"
CMD_URL="http://localhost:${HTTP_PORT}/api/v1/command/${DB}"

log() { echo "[agentarmy-entrypoint] $*" >&2; }

# --- 1. Apply the baked read-only MCP posture (config/ is a base VOLUME, so we
#        copy at runtime to win over any volume-seeded default). -------------
if [ -f "${SEED_DIR}/mcp-config.json" ]; then
  cp "${SEED_DIR}/mcp-config.json" "${ARCADEDB_HOME}/config/mcp-config.json"
  log "applied read-only MCP posture to config/mcp-config.json"
fi

# --- 2. Resolve secrets (FILE wins over plain env). -------------------------
read_secret() { # $1=file-env-name $2=plain-env-name
  _f="$(eval "printf '%s' \"\${$1:-}\"")"
  _v="$(eval "printf '%s' \"\${$2:-}\"")"
  if [ -n "$_f" ] && [ -f "$_f" ]; then
    cat "$_f"            # command substitution by caller strips trailing newline
  else
    printf '%s' "$_v"
  fi
}

ROOT_PW="$(read_secret ARCADEDB_ROOT_PASSWORD_FILE ARCADEDB_ROOT_PASSWORD)"
SVC_PW="$(read_secret ARCADEDB_SERVICE_PASSWORD_FILE ARCADEDB_SERVICE_PASSWORD)"

if [ -z "$ROOT_PW" ]; then
  log "FATAL: no root password (set ARCADEDB_ROOT_PASSWORD_FILE or ARCADEDB_ROOT_PASSWORD)"
  exit 78  # EX_CONFIG
fi
if [ -z "$SVC_PW" ]; then
  log "FATAL: no service-user password for '${SVC_USER}' (set ARCADEDB_SERVICE_PASSWORD_FILE or ARCADEDB_SERVICE_PASSWORD)"
  exit 78
fi

# --- 3. Background bootstrapper: wait for readiness, then ensure stub types.
#        Runs as root over HTTP; idempotent (IF NOT EXISTS). Survives the exec
#        below as an independent child process. ------------------------------
(
  i=0
  while [ "$i" -lt 60 ]; do
    if wget -q -O /dev/null -T 3 "$READY_URL" 2>/dev/null; then
      break
    fi
    i=$((i + 1))
    sleep 2
  done
  if [ "$i" -ge 60 ]; then
    log "WARN: server not ready after timeout; skipping doctor-stub schema"
    exit 0
  fi

  if [ ! -f "${SEED_DIR}/doctor-stub-schema.json" ]; then
    log "WARN: doctor-stub-schema.json missing; skipping"
    exit 0
  fi

  AUTH="$(printf '%s' "root:${ROOT_PW}" | base64 | tr -d '\n')"
  if wget -q -O /tmp/stub_out \
       --header="Authorization: Basic ${AUTH}" \
       --header="Content-Type: application/json" \
       --post-file="${SEED_DIR}/doctor-stub-schema.json" \
       "$CMD_URL" 2>/dev/null; then
    log "doctor-stub schema ensured (Chunk, StoredObject, IngestJob)"
  else
    log "WARN: doctor-stub schema apply failed (server stays up; backend may own schema)"
  fi
  rm -f /tmp/stub_out 2>/dev/null || true
) &

# --- 4. Assemble server settings and hand off (server becomes PID-stable so
#        docker stop / signals reach it directly). ---------------------------
cd "$ARCADEDB_HOME"

set -- \
  "-Darcadedb.server.rootPassword=${ROOT_PW}" \
  "-Darcadedb.server.defaultDatabases=${DB}[${SVC_USER}:${SVC_PW}:readonly]" \
  "-Darcadedb.server.mode=${SERVER_MODE}"

# Optional extra -D settings for spokes (space-separated), e.g.
#   ARCADEDB_EXTRA_SETTINGS="-Darcadedb.server.httpsIncomingPort=2490"
if [ -n "${ARCADEDB_EXTRA_SETTINGS:-}" ]; then
  # shellcheck disable=SC2086
  set -- "$@" ${ARCADEDB_EXTRA_SETTINGS}
fi

log "starting ArcadeDB server (db=${DB}, user=${SVC_USER}, mode=${SERVER_MODE})"
exec ./bin/server.sh "$@"
