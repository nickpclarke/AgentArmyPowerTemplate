#!/usr/bin/env sh
#
# One-shot setup for the AgentArmy ArcadeDB image (Linux/macOS/WSL/Git-Bash).
#   1. generate local secrets (if missing)
#   2. build + start the container (docker compose)
#   3. wait until healthy
#   4. prove it with agentarmy-doctor (if node is available)
#   5. emit MCP client wiring to a gitignored env file
#
# Usage:  ./setup.sh            # bring up
#         ./setup.sh --down     # tear down (keeps secrets), then exit
set -eu

cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

COMPOSE="examples/compose.arcadedb-server.example.yml"
SECRETS="examples/.secrets"
ROOT_FILE="$SECRETS/arcadedb_root_password.txt"
READER_FILE="$SECRETS/arcadedb_password.txt"
MCP_ENV="$SECRETS/mcp-client.env"

if [ "${1:-}" = "--down" ]; then
  docker compose -f "$COMPOSE" down -v
  echo "stack down (secrets kept under $SECRETS/)"
  exit 0
fi

# 1. Secrets. Alnum only — avoids the defaultDatabases delimiters : [ ] { }.
gen_pw() { LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom 2>/dev/null | dd bs=1 count=32 2>/dev/null; }
mkdir -p "$SECRETS"
[ -s "$ROOT_FILE" ]   || { gen_pw > "$ROOT_FILE";   echo "generated $ROOT_FILE"; }
[ -s "$READER_FILE" ] || { gen_pw > "$READER_FILE"; echo "generated $READER_FILE"; }

# 2. Build + start.
docker compose -f "$COMPOSE" up -d --build

# 3. Wait for healthy.
cid="$(docker compose -f "$COMPOSE" ps -q arcadedb)"
printf 'waiting for healthy'
st=starting; i=0
while [ "$i" -lt 60 ]; do
  st="$(docker inspect --format '{{.State.Health.Status}}' "$cid" 2>/dev/null || echo starting)"
  [ "$st" = healthy ] && { printf ' ok\n'; break; }
  printf '.'; i=$((i + 1)); sleep 2
done
if [ "$st" != healthy ]; then
  printf ' FAILED\n'
  docker compose -f "$COMPOSE" logs --tail=40 arcadedb || true
  exit 1
fi

# 4. Prove it (best-effort).
if command -v node >/dev/null 2>&1; then
  echo "running agentarmy-doctor arcadedb..."
  ARCADEDB_URL=http://localhost:2480 ARCADEDB_DATABASE=knowledge \
  ARCADEDB_USER=platform_reader ARCADEDB_PASSWORD_FILE="$READER_FILE" \
    node ../../tools/agentarmy-doctor.mjs arcadedb || true
fi

# 5. Emit MCP client wiring (Basic = turnkey; Bearer = optional, hardened).
READER_PW="$(cat "$READER_FILE")"
BASIC="$(printf 'platform_reader:%s' "$READER_PW" | base64 | tr -d '\n')"
{
  echo "# MCP client wiring for the AgentArmy ArcadeDB image (gitignored)."
  echo "ARCADEDB_MCP_URL=http://localhost:2480/api/v1/mcp"
  echo "# Turnkey: Basic auth as the read-only platform_reader user."
  echo "ARCADEDB_MCP_BASIC=$BASIC"
  echo "# Hardened alt: create a token in ArcadeDB Studio -> Security, then:"
  echo "# ARCADEDB_MCP_TOKEN="
} > "$MCP_ENV"

echo
echo "ArcadeDB + MCP ready at http://localhost:2480/api/v1/mcp"
echo "MCP client env written to $MCP_ENV (gitignored)."
echo "Load it, then point .mcp.json at:  \"Authorization\": \"Basic \${ARCADEDB_MCP_BASIC}\""
echo "Tear down with:  ./setup.sh --down"
