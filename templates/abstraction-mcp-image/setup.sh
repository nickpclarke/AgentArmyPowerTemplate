#!/usr/bin/env sh
# Local (non-docker) setup for abstraction-mcp: install the tiny MCP + httpx deps.
set -e
pip install --quiet -r ../../tools/mcp-abstraction/requirements.txt || true
echo "abstraction-mcp ready.  doctor: python doctor.py"
echo "serve (local): (cd ../../tools/mcp-abstraction && MCP_TRANSPORT=streamable-http python server.py)"
