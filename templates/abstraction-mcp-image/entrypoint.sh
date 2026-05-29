#!/usr/bin/env sh
# abstraction-mcp dispatch: doctor (offline correctness gate) | serve (run the MCP server).
set -e
case "${1:-doctor}" in
  doctor) exec python doctor.py ;;
  serve)  exec python server.py ;;
  *) echo "usage: abstraction-mcp [doctor|serve]"; exit 2 ;;
esac
