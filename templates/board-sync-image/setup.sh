#!/usr/bin/env sh
# Local (non-docker) setup for board-sync: only the Key Vault SDK is needed, and only
# when GH_TOKEN is not already in the env (the GitHub fetch itself is stdlib urllib).
set -e
pip install --quiet azure-identity azure-keyvault-secrets || true
echo "board-sync ready.  doctor: python doctor.py   |   live: BOARD_SOURCE=github python sync.py"
