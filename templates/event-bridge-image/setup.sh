#!/usr/bin/env sh
# One-shot setup for the AgentArmy event-bridge image (Linux/macOS/WSL/Git-Bash).
#   1. generate the GitHub webhook secret (if missing)
#   2. build + start (compose brings up nats + bridge)
#   3. wait healthy + run the doctor — proves events flow end-to-end
# Usage:  ./setup.sh           # bring up + prove
#         ./setup.sh --down    # tear down (keeps the secret), then exit
set -eu

cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

COMPOSE="examples/compose.event-bridge.example.yml"
SECRETS="examples/.secrets"
SECRET_FILE="$SECRETS/github_webhook_secret.txt"

if [ "${1:-}" = "--down" ]; then
  docker compose -f "$COMPOSE" down -v
  echo "stack down (secret kept under $SECRETS/)"
  exit 0
fi

gen_pw() { LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom 2>/dev/null | dd bs=1 count=48 2>/dev/null; }
mkdir -p "$SECRETS"
[ -s "$SECRET_FILE" ] || { gen_pw > "$SECRET_FILE"; echo "generated $SECRET_FILE"; }

docker compose -f "$COMPOSE" up -d --build

echo "running the event-bridge doctor..."
sh scripts/event-bus-doctor.sh

echo
echo "bridge ready: webhooks → http://localhost:8080/webhooks/github  ·  NATS :4222 / monitor :8222"
echo "configure GitHub: payload URL above, content type application/json, secret = $(cat "$SECRET_FILE")"
echo "tear down with:  ./setup.sh --down"
