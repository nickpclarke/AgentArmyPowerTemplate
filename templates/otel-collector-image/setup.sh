#!/usr/bin/env bash
# Scaffold — see README.md. Real setup.sh lands in the implementation issue
# (contracts.md Backlog XC-2). Behavior MUST match templates/event-bridge-image/setup.sh:
# (1) docker compose up -d, (2) wait for /:13133, (3) print connect-here info, (4) exec doctor.
set -euo pipefail
echo "otel-collector-image is a scaffold. See README.md."
echo "Implementation pending; track in docs/contracts.md Backlog row XC-2."
exit 0
