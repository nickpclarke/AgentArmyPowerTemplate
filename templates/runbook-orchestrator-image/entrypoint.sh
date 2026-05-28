#!/bin/sh
# Dispatch for the AgentArmy runbook-orchestrator image.
#   serve  (default)      uvicorn control API + event-bus trigger dispatcher
#   run <file>            execute one runbook to completion (CLI / one-shot)
#   validate <file>       structural validation only (exit non-zero on error)
#   <any command>         runs as-is (sh, python, …)
set -e

SCRIPTS=/opt/agentarmy/scripts

case "${1:-serve}" in
  serve)
    shift 2>/dev/null || true
    exec uvicorn server:app --app-dir "$SCRIPTS" \
      --host 0.0.0.0 --port "${PORT:-8080}" "$@"
    ;;
  run)
    shift
    exec python "$SCRIPTS/runbook_engine.py" run "$@"
    ;;
  validate)
    shift
    exec python "$SCRIPTS/runbook_engine.py" validate "$@"
    ;;
  *)
    exec "$@"
    ;;
esac
