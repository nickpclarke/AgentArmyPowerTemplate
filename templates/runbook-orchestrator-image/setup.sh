#!/usr/bin/env sh
# One-shot setup for the AgentArmy runbook-orchestrator (Linux/macOS/WSL/Git-Bash).
#   1. build + start (compose brings up nats + orchestrator)
#   2. wait healthy + run the doctor — proves runbooks fire on bus events
# Usage:  ./setup.sh           # bring up + prove
#         ./setup.sh --down    # tear down
set -eu

cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

COMPOSE="examples/compose.runbook.example.yml"

if [ "${1:-}" = "--down" ]; then
  docker compose -f "$COMPOSE" down -v
  echo "stack down"
  exit 0
fi

docker compose -f "$COMPOSE" up -d --build

echo "running the runbook-orchestrator doctor..."
# Host 8088 (8080 is taken by the platform event-bridge); doctor honors ORCH_URL.
ORCH_URL=http://localhost:8088 sh scripts/runbook-doctor.sh

echo
echo "orchestrator ready: control API → http://localhost:8088  ·  NATS internal-only (compose net)"
echo "  GET  /runbooks                      list indexed runbooks"
echo "  POST /runbooks/{id}/trigger         run one now (JSON body = context)"
echo "drop .bpmn / .cacao.json files in ./runbooks/ (mounted) — no rebuild needed"
echo "tear down with:  ./setup.sh --down"
