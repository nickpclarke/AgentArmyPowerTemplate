#!/usr/bin/env sh
# One-shot setup for the AgentArmy schema-migrator image (Linux/macOS/WSL/Git-Bash).
#   1. build the image
#   2. run the doctor — spins up its own throwaway PG (+ optional ArcadeDB),
#      runs the migrator twice, then runs it again with a bad revision
#
# Usage:
#   ./setup.sh                       # PG + ArcadeDB
#   SKIP_ARCADEDB=1 ./setup.sh       # PG only (faster; doctor skips the
#                                      arcadedb checks gracefully)
set -eu

cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

IMAGE="agentarmy-schema-migrator:local"

echo "building ${IMAGE}..."
docker build -t "$IMAGE" .

echo
echo "running doctor..."
chmod +x scripts/migrator-doctor.sh scripts/migrate.sh scripts/apply_arcadedb.py
IMAGE="$IMAGE" SKIP_ARCADEDB="${SKIP_ARCADEDB:-0}" ./scripts/migrator-doctor.sh
