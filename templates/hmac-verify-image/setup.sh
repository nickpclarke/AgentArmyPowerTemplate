#!/usr/bin/env sh
# One-shot setup for the AgentArmy hmac-verify sidecar image
# (Linux/macOS/WSL/Git-Bash).
#   1. build the image
#   2. compose up (sidecar + tiny echo upstream so the doctor can prove
#      "accepts-good-sig" actually forwarded the request)
#   3. wait for /livez on both services
#   4. exec the doctor — proves the four security invariants
# Usage:  ./setup.sh           # bring up + prove
#         ./setup.sh --down    # tear down
set -eu

cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

COMPOSE="examples/compose.hmac-verify.example.yml"

if [ "${1:-}" = "--down" ]; then
  docker compose -f "$COMPOSE" down -v
  echo "stack down"
  exit 0
fi

docker compose -f "$COMPOSE" up -d --build

echo "waiting for hmac-verify /livez..."
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 2 http://localhost:8083/livez 2>/dev/null || echo 000)"
  if [ "$code" = "200" ]; then echo "ready (attempt $i)"; break; fi
  sleep 1
done

echo "waiting for echo-upstream /livez..."
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 2 http://localhost:8085/livez 2>/dev/null || echo 000)"
  if [ "$code" = "200" ]; then echo "ready (attempt $i)"; break; fi
  sleep 1
done

echo
echo "running doctor..."
chmod +x scripts/hmac-doctor.sh
HMAC_SECRET="${HMAC_SECRET:-doctor-secret}" ./scripts/hmac-doctor.sh
