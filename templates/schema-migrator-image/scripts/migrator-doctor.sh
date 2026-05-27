#!/usr/bin/env bash
# AgentArmy schema-migrator doctor.
#
# Proves three things against a freshly-built image (per image.json):
#   1. migrations-applied         — first run creates schema_version + (if ARCADEDB) migration_marker
#   2. idempotent-on-rerun        — second run exits 0 and the alembic version doesn't change
#   3. fails-fast-on-bad-revision — MIGRATION_BAD_REV makes the container exit nonzero
#
# This doctor spins up its own Postgres (postgres:16-alpine) and an optional
# ArcadeDB (arcadedata/arcadedb:latest) on the host network and cleans them up
# at the end.  By default ArcadeDB is included; export SKIP_ARCADEDB=1 to run
# Postgres-only (faster, works in resource-constrained environments).
#
# Usage:
#   ./scripts/migrator-doctor.sh                  # PG + ArcadeDB
#   SKIP_ARCADEDB=1 ./scripts/migrator-doctor.sh  # PG only
set -eu

IMAGE="${IMAGE:-agentarmy-schema-migrator:local}"
NET="${NET:-schema-migrator-doctor-net}"
PG_NAME="${PG_NAME:-doctor-pg}"
ARCADE_NAME="${ARCADE_NAME:-doctor-arcadedb}"
SKIP_ARCADEDB="${SKIP_ARCADEDB:-0}"

PASS=0
FAIL=0
ok()   { printf "  \033[32mPASS\033[0m %s\n" "$1"; PASS=$((PASS+1)); }
fail() { printf "  \033[31mFAIL\033[0m %s\n" "$1"; FAIL=$((FAIL+1)); }

cleanup() {
    rc=$?
    # Best-effort teardown. Always run, don't propagate failures.
    docker rm -f "$PG_NAME" >/dev/null 2>&1 || true
    docker rm -f "$ARCADE_NAME" >/dev/null 2>&1 || true
    docker network rm "$NET" >/dev/null 2>&1 || true
    exit "$rc"
}
trap cleanup EXIT INT TERM

echo "agentarmy schema-migrator doctor"
echo "  image:         ${IMAGE}"
echo "  network:       ${NET}"
echo "  SKIP_ARCADEDB: ${SKIP_ARCADEDB}"
echo

# ---- pre-flight: image exists --------------------------------------------
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    fail "image ${IMAGE} not found; run setup.sh first (builds the image)"
    echo "summary: ${PASS} pass, ${FAIL} fail"
    exit 1
fi

# ---- bring up a private network + dependencies ---------------------------
docker network rm "$NET" >/dev/null 2>&1 || true
docker network create "$NET" >/dev/null

echo "starting postgres:16-alpine..."
docker run -d --name "$PG_NAME" --network "$NET" \
    -e POSTGRES_PASSWORD=doctor -e POSTGRES_USER=doctor -e POSTGRES_DB=doctor \
    postgres:16-alpine >/dev/null

# Wait for PG to be ready (pg_isready inside the container).
echo "waiting for postgres to accept connections..."
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
    if docker exec "$PG_NAME" pg_isready -U doctor >/dev/null 2>&1; then
        echo "  postgres ready (attempt $i)"
        break
    fi
    sleep 2
done

ARCADE_ENV=""
if [ "$SKIP_ARCADEDB" != "1" ]; then
    echo "starting arcadedb..."
    if docker run -d --name "$ARCADE_NAME" --network "$NET" \
        -e JAVA_OPTS="-Darcadedb.server.rootPassword=playwithdata" \
        arcadedata/arcadedb:latest >/dev/null 2>&1; then
        # ArcadeDB has no anonymous /ready probe; /api/v1/server returns 200
        # once the HTTP listener is up (auth-gated). curl isn't shipped in the
        # arcadedb image, so we probe from the migrator image (curl is baked).
        echo "waiting for arcadedb to be ready..."
        ARCADE_READY="false"
        for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30; do
            code=$(docker run --rm --network "$NET" --entrypoint curl "$IMAGE" \
                -s -o /dev/null -w '%{http_code}' --max-time 3 \
                -u root:playwithdata \
                "http://${ARCADE_NAME}:2480/api/v1/server" 2>/dev/null || echo 000)
            if [ "$code" = "200" ] || [ "$code" = "401" ]; then
                ARCADE_READY="true"
                echo "  arcadedb ready (attempt $i, HTTP $code)"
                break
            fi
            sleep 2
        done
        if [ "$ARCADE_READY" = "true" ]; then
            ARCADE_ENV="-e ARCADEDB_URL=http://${ARCADE_NAME}:2480 -e ARCADEDB_DB=agentarmy -e ARCADEDB_USER=root -e ARCADEDB_PASSWORD=playwithdata"
        else
            echo "  WARN: arcadedb did not become ready in 50s — continuing PG-only"
            SKIP_ARCADEDB=1
            docker rm -f "$ARCADE_NAME" >/dev/null 2>&1 || true
        fi
    else
        echo "  WARN: arcadedb image failed to start — continuing PG-only"
        SKIP_ARCADEDB=1
    fi
fi

PG_URL="postgresql://doctor:doctor@${PG_NAME}:5432/doctor"
RUN_ARGS="--rm --network ${NET} -e DATABASE_URL=${PG_URL} ${ARCADE_ENV}"

# ---- check 1: migrations applied -----------------------------------------
echo
echo "[1/3] migrations-applied — first run creates expected tables/types"
if docker run $RUN_ARGS "$IMAGE" >/tmp/migrator-run1.log 2>&1; then
    ok "first run exited 0"
else
    rc=$?
    fail "first run exited $rc (see /tmp/migrator-run1.log)"
    sed 's/^/    /' /tmp/migrator-run1.log
fi

# Verify schema_version table exists in PG.
if docker exec "$PG_NAME" psql -U doctor -d doctor -tAc \
    "SELECT to_regclass('public.schema_version') IS NOT NULL" \
    2>/dev/null | grep -q '^t$'; then
    ok "schema_version table exists in postgres"
else
    fail "schema_version table missing in postgres after migrate"
fi

if [ "$SKIP_ARCADEDB" != "1" ]; then
    # ArcadeDB: query schema, look for migration_marker type. The arcadedb
    # image ships without curl, so we probe from the migrator image (curl baked).
    docker run --rm --network "$NET" --entrypoint curl "$IMAGE" \
        -sf -u root:playwithdata -X POST \
        -H "Content-Type: application/json" \
        -d '{"language":"sql","command":"SELECT FROM schema:types"}' \
        "http://${ARCADE_NAME}:2480/api/v1/query/agentarmy" >/tmp/arcade-q.json 2>&1 || true
    if grep -q migration_marker /tmp/arcade-q.json 2>/dev/null; then
        ok "migration_marker vertex type exists in arcadedb"
    else
        fail "migration_marker vertex type not found in arcadedb (response: $(cat /tmp/arcade-q.json 2>/dev/null))"
    fi
fi

# Snapshot alembic version (for check 2 comparison).
ALEMBIC_V1=$(docker exec "$PG_NAME" psql -U doctor -d doctor -tAc \
    "SELECT version_num FROM alembic_version" 2>/dev/null || echo "")
HIST_COUNT_1=$(docker exec "$PG_NAME" psql -U doctor -d doctor -tAc \
    "SELECT count(*) FROM arcadedb_migration_history" 2>/dev/null || echo 0)

# ---- check 2: idempotent on re-run ---------------------------------------
echo
echo "[2/3] idempotent-on-rerun — second run is a no-op (exit 0, no schema drift)"
if docker run $RUN_ARGS "$IMAGE" >/tmp/migrator-run2.log 2>&1; then
    ok "second run exited 0"
else
    rc=$?
    fail "second run exited $rc (see /tmp/migrator-run2.log)"
    sed 's/^/    /' /tmp/migrator-run2.log
fi

ALEMBIC_V2=$(docker exec "$PG_NAME" psql -U doctor -d doctor -tAc \
    "SELECT version_num FROM alembic_version" 2>/dev/null || echo "")
if [ -n "$ALEMBIC_V1" ] && [ "$ALEMBIC_V1" = "$ALEMBIC_V2" ]; then
    ok "alembic version unchanged across runs (still ${ALEMBIC_V2})"
else
    fail "alembic version drifted: run1=${ALEMBIC_V1} run2=${ALEMBIC_V2}"
fi

if [ "$SKIP_ARCADEDB" != "1" ]; then
    HIST_COUNT_2=$(docker exec "$PG_NAME" psql -U doctor -d doctor -tAc \
        "SELECT count(*) FROM arcadedb_migration_history" 2>/dev/null || echo 0)
    if [ "$HIST_COUNT_1" = "$HIST_COUNT_2" ]; then
        ok "arcadedb_migration_history row count stable (${HIST_COUNT_2})"
    else
        fail "arcadedb_migration_history grew on rerun: ${HIST_COUNT_1} -> ${HIST_COUNT_2}"
    fi
fi

# ---- check 3: fails-fast on bad revision ---------------------------------
echo
echo "[3/3] fails-fast-on-bad-revision — MIGRATION_BAD_REV makes the container exit nonzero"
if docker run $RUN_ARGS -e MIGRATION_BAD_REV=fakeXYZ "$IMAGE" >/tmp/migrator-run3.log 2>&1; then
    fail "container exited 0 despite MIGRATION_BAD_REV — depends_on guard would never trigger"
else
    rc=$?
    ok "container exited nonzero (${rc}) on bad revision — depends_on guard holds"
fi

# ---- summary -------------------------------------------------------------
echo
echo "summary: ${PASS} pass, ${FAIL} fail"
[ "$FAIL" -eq 0 ]
