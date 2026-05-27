#!/usr/bin/env sh
# One-shot setup for the AgentArmy jwt-introspect image (Linux/macOS/WSL/Git-Bash).
#   1. build the image
#   2. compose up (sidecar bound to :8084, JWKS_URL points at the doctor's
#      local http.server that the doctor brings up)
#   3. wait for /livez
#   4. exec the doctor — mints keypair + JWKS + JWTs, restarts container with
#      leeway=60 for the leeway-honored check, restores leeway=0 after.
# Usage:  ./setup.sh           # bring up + prove
#         ./setup.sh --down    # tear down
set -eu

cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

COMPOSE="examples/compose.jwt-introspect.example.yml"

if [ "${1:-}" = "--down" ]; then
  docker compose -f "$COMPOSE" down
  echo "stack down"
  exit 0
fi

docker compose -f "$COMPOSE" up -d --build

echo "waiting for /livez..."
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 2 http://localhost:8084/livez 2>/dev/null || echo 000)"
  if [ "$code" = "200" ]; then echo "ready (attempt $i)"; break; fi
  sleep 1
done

echo
echo "running doctor (mints JWKS + JWTs, runs 5 checks, restarts for leeway test)..."
chmod +x scripts/jwt-doctor.sh
./scripts/jwt-doctor.sh
