#!/usr/bin/env bash
# AgentArmy schema-migrator entrypoint.
#
# Modes (via MODE env, default `migrate`):
#   migrate  — wait for DBs → alembic upgrade head → apply pending ArcadeDB DDL → exit 0
#   dryrun   — print the plan; exit 0 without applying
#   rollback — alembic downgrade -1; print "ArcadeDB rollback not implemented"
#
# Required env:
#   DATABASE_URL              — postgres://user:pass@host:port/db (psycopg-style)
# Optional env:
#   ARCADEDB_URL              — http://host:2480 (omit to skip arcadedb step)
#   ARCADEDB_DB               — database name on the ArcadeDB server (default: agentarmy)
#   ARCADEDB_USER             — default: root
#   ARCADEDB_PASSWORD         — default: playwithdata
#   MIGRATION_BAD_REV         — if set, alembic upgrades to this nonexistent rev (forces FAIL)
#   PG_WAIT_SECS              — default 60
#   ARCADEDB_WAIT_SECS        — default 60
set -euo pipefail

MODE="${MODE:-migrate}"
PG_WAIT_SECS="${PG_WAIT_SECS:-60}"
ARCADEDB_WAIT_SECS="${ARCADEDB_WAIT_SECS:-60}"
ALEMBIC_CONFIG="${ALEMBIC_CONFIG:-/opt/agentarmy/migrations/postgres/alembic.ini}"
ARCADEDB_MIGRATIONS_DIR="${ARCADEDB_MIGRATIONS_DIR:-/opt/agentarmy/migrations/arcadedb}"

log() { printf '%s migrate.sh %s\n' "$(date -u +%FT%TZ)" "$*"; }

if [ -z "${DATABASE_URL:-}" ]; then
    log "FATAL: DATABASE_URL is unset"
    exit 2
fi

# ---- mode: dryrun --------------------------------------------------------
if [ "$MODE" = "dryrun" ]; then
    log "MODE=dryrun — emitting plan, not applying"
    log "plan: alembic upgrade head (DATABASE_URL set)"
    if [ -n "${ARCADEDB_URL:-}" ]; then
        log "plan: arcadedb DDL files to apply (if not already applied):"
        ls -1 "$ARCADEDB_MIGRATIONS_DIR"/*.sql 2>/dev/null | sed 's/^/  - /' || log "  (none)"
    else
        log "plan: arcadedb step SKIPPED (ARCADEDB_URL unset)"
    fi
    exit 0
fi

# ---- mode: rollback ------------------------------------------------------
if [ "$MODE" = "rollback" ]; then
    log "MODE=rollback — alembic downgrade -1"
    alembic -c "$ALEMBIC_CONFIG" downgrade -1
    log "WARN: ArcadeDB rollback not implemented; graph DDL is forward-only."
    exit 0
fi

# ---- mode: migrate -------------------------------------------------------
if [ "$MODE" != "migrate" ]; then
    log "FATAL: unknown MODE=$MODE (expected migrate|dryrun|rollback)"
    exit 2
fi

# Wait for Postgres -------------------------------------------------------
log "waiting up to ${PG_WAIT_SECS}s for postgres at \$DATABASE_URL"
# pg_isready understands a libpq-style conninfo string; rewrite the psycopg
# URL into something it accepts. For simplicity, parse user:pass@host:port/db
# from the URL.
PG_URL_FOR_ISREADY="${DATABASE_URL#postgresql+psycopg://}"
PG_URL_FOR_ISREADY="${PG_URL_FOR_ISREADY#postgresql://}"
PG_URL_FOR_ISREADY="${PG_URL_FOR_ISREADY#postgres://}"
HOSTPORT="${PG_URL_FOR_ISREADY#*@}"
HOSTPORT="${HOSTPORT%%/*}"
PG_HOST="${HOSTPORT%%:*}"
PG_PORT="${HOSTPORT#*:}"
if [ "$PG_PORT" = "$PG_HOST" ]; then PG_PORT=5432; fi

elapsed=0
until pg_isready -h "$PG_HOST" -p "$PG_PORT" >/dev/null 2>&1; do
    if [ "$elapsed" -ge "$PG_WAIT_SECS" ]; then
        log "FATAL: postgres at ${PG_HOST}:${PG_PORT} not ready in ${PG_WAIT_SECS}s"
        exit 3
    fi
    sleep 2
    elapsed=$((elapsed + 2))
done
log "postgres ready at ${PG_HOST}:${PG_PORT}"

# Wait for ArcadeDB if configured ----------------------------------------
if [ -n "${ARCADEDB_URL:-}" ]; then
    log "waiting up to ${ARCADEDB_WAIT_SECS}s for arcadedb at ${ARCADEDB_URL}"
    # ArcadeDB has no anonymous /ready probe; /api/v1/server returns 200 once
    # the HTTP listener is up (auth-gated, so we use the same creds as the
    # runner). 401 also means "process up" — we treat that as ready too.
    elapsed=0
    AUTH_USER="${ARCADEDB_USER:-root}"
    AUTH_PASS="${ARCADEDB_PASSWORD:-playwithdata}"
    while :; do
        code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 \
            -u "${AUTH_USER}:${AUTH_PASS}" \
            "${ARCADEDB_URL%/}/api/v1/server" 2>/dev/null || echo 000)
        if [ "$code" = "200" ] || [ "$code" = "401" ]; then
            break
        fi
        if [ "$elapsed" -ge "$ARCADEDB_WAIT_SECS" ]; then
            log "FATAL: arcadedb not ready in ${ARCADEDB_WAIT_SECS}s (last HTTP=${code})"
            exit 4
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done
    log "arcadedb ready"
fi

# Run alembic --------------------------------------------------------------
if [ -n "${MIGRATION_BAD_REV:-}" ]; then
    log "MIGRATION_BAD_REV=${MIGRATION_BAD_REV} — forcing a known-failing upgrade target"
    # alembic exits nonzero when asked to upgrade to a revision it doesn't know.
    alembic -c "$ALEMBIC_CONFIG" upgrade "$MIGRATION_BAD_REV"
    log "FATAL: alembic should have errored on bad revision but did not"
    exit 5
fi

log "running: alembic upgrade head"
alembic -c "$ALEMBIC_CONFIG" upgrade head

# Apply ArcadeDB DDL ------------------------------------------------------
if [ -n "${ARCADEDB_URL:-}" ]; then
    log "applying pending arcadedb DDL files from ${ARCADEDB_MIGRATIONS_DIR}"
    python3 /opt/agentarmy/scripts/apply_arcadedb.py
fi

log "migration complete; exiting 0"
exit 0
