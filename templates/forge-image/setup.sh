#!/usr/bin/env sh
# One-shot setup for the AgentArmy agentarmy-forge image (Linux/macOS/WSL/Git-Bash).
#   1. build the image (~3–5 min cold; multi-toolchain: python + nodejs)
#   2. compose up (FastAPI on :8086)
#   3. wait for /livez
#   4. exec the doctor inside the container (7 checks; one SKIP-with-PASS for blob)
# Usage:  ./setup.sh           # bring up + prove
#         ./setup.sh --down    # tear down + drop the work-cache volume
set -eu

cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

COMPOSE="examples/compose.forge.example.yml"

if [ "${1:-}" = "--down" ]; then
  docker compose -f "$COMPOSE" down -v
  echo "stack down (work-cache volume dropped)"
  exit 0
fi

docker compose -f "$COMPOSE" up -d --build

echo "waiting for /livez..."
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 2 http://localhost:8086/livez 2>/dev/null || echo 000)"
  if [ "$code" = "200" ]; then echo "ready (attempt $i)"; break; fi
  sleep 1
done

echo
echo "running doctor inside the container..."
# MSYS_NO_PATHCONV=1 stops Git Bash on Windows from rewriting the Linux paths
# in argv (without it, /opt/agentarmy/... becomes C:/Program Files/Git/opt/...).
MSYS_NO_PATHCONV=1 docker exec -e SKIP_AZURE=1 -e SKIP_DOTNET=1 -e HOST=localhost agentarmy-forge /opt/agentarmy/scripts/forge-doctor.sh
