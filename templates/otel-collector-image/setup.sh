#!/usr/bin/env sh
# One-shot setup for the AgentArmy otel-collector image (Linux/macOS/WSL/Git-Bash).
#   1. build the image
#   2. compose up (standalone mode + file exporter by default)
#   3. wait for /:13133 readiness
#   4. exec the doctor — proves OTLP-accept + file export end-to-end
# Usage:  ./setup.sh           # bring up + prove
#         ./setup.sh --down    # tear down + clear span artifacts
set -eu

cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

COMPOSE="examples/compose.otel-collector.example.yml"

if [ "${1:-}" = "--down" ]; then
  docker compose -f "$COMPOSE" down -v
  rm -rf otel-spans 2>/dev/null || true
  echo "stack down (spans removed)"
  exit 0
fi

mkdir -p otel-spans
docker compose -f "$COMPOSE" up -d --build

echo "waiting for collector readiness (/:13133)..."
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -sS -o /dev/null -w '%{http_code}' --max-time 2 http://localhost:13133/ 2>/dev/null | grep -q 200; then
    echo "ready (attempt $i)"
    break
  fi
  sleep 1
done

echo
echo "running doctor..."
chmod +x scripts/otel-doctor.sh
HOST_SPANS_FILE=./examples/otel-spans/spans.jsonl CONTAINER=otel-collector ./scripts/otel-doctor.sh
