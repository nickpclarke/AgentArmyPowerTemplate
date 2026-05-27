#!/usr/bin/env sh
# One-shot setup for the AgentArmy local-embedder image (Linux/macOS/WSL/Git-Bash).
#   1. build the image (CPU baseline; ~15 min cold for torch)
#   2. compose up (sentence-transformers BAAI/bge-small-en-v1.5 on CPU)
#   3. wait for /livez
#   4. exec the doctor — warmup triggers lazy model load (~30-60s cold)
# Usage:  ./setup.sh           # bring up + prove
#         ./setup.sh --down    # tear down + drop the model-cache volume
set -eu

cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

COMPOSE="examples/compose.local-embedder.example.yml"

if [ "${1:-}" = "--down" ]; then
  docker compose -f "$COMPOSE" down -v
  echo "stack down (model cache volume dropped)"
  exit 0
fi

docker compose -f "$COMPOSE" up -d --build

echo "waiting for /livez..."
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 2 http://localhost:8082/livez 2>/dev/null || echo 000)"
  if [ "$code" = "200" ]; then echo "ready (attempt $i)"; break; fi
  sleep 1
done

echo
echo "running doctor (warmup may take 30-60s on first run while model downloads)..."
chmod +x scripts/embedder-doctor.sh
./scripts/embedder-doctor.sh
