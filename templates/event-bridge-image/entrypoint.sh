#!/bin/sh
# Dispatch for the AgentArmy event-bridge image.
#   serve-inbound  (default)  uvicorn webhook-receiver on $PORT (default 8080)
#   relay-outbound            nats-relay (JetStream push-consumer → POST SINK_URL)
#   <any command>             runs as-is (sh, python, nats CLI passthrough, …)
set -e

case "${1:-serve-inbound}" in
  serve-inbound)
    shift 2>/dev/null || true
    exec uvicorn webhook_receiver:app \
      --app-dir /opt/agentarmy/scripts \
      --host 0.0.0.0 --port "${PORT:-8080}" "$@"
    ;;
  relay-outbound)
    shift 2>/dev/null || true
    exec python /opt/agentarmy/scripts/nats-relay.py "$@"
    ;;
  *)
    exec "$@"
    ;;
esac
