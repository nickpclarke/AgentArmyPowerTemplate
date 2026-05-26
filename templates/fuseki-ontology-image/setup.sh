#!/usr/bin/env sh
# One-shot setup for the AgentArmy Fuseki super-image (Linux/macOS/WSL/Git-Bash).
#   1. generate the admin secret (if missing)
#   2. build + start the container (docker compose)
#   3. wait until /$/ping returns 200
#   4. run the doctor — proves sieve (accept + reject) + emit
#
# Usage:  ./setup.sh            # bring up + prove
#         ./setup.sh --down     # tear down (keeps the secret), then exit
set -eu

cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

COMPOSE="examples/compose.fuseki.example.yml"
SECRETS="examples/.secrets"
PW_FILE="$SECRETS/fuseki_admin_password.txt"

if [ "${1:-}" = "--down" ]; then
  docker compose -f "$COMPOSE" down -v
  echo "stack down (secret kept under $SECRETS/)"
  exit 0
fi

# 1. Secret (alphanumeric, 32 chars).
gen_pw() { LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom 2>/dev/null | dd bs=1 count=32 2>/dev/null; }
mkdir -p "$SECRETS"
[ -s "$PW_FILE" ] || { gen_pw > "$PW_FILE"; echo "generated $PW_FILE"; }

# 2. Build + start.
docker compose -f "$COMPOSE" up -d --build

# 3. Run the doctor (it waits for readiness internally).
echo "running the Fuseki super-image doctor..."
sh scripts/fuseki-doctor.sh

echo
echo "Fuseki ready: SPARQL/Studio on http://localhost:3030  (dataset: knowledge)"
echo "Admin password is in $PW_FILE (gitignored)."
echo "Tear down with:  ./setup.sh --down"
