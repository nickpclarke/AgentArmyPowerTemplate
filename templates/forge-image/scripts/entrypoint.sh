#!/usr/bin/env sh
# agentarmy-forge entrypoint — dispatch on MODE.
#
#   MODE=serve              FastAPI app on :8086 (default)
#   MODE=generate           run forge CLI; args after `--` are passed through
#   MODE=ingest-validate    parse + IR-validate; nonzero on error (no emit)
#   MODE=doctor             run scripts/forge-doctor.sh
#
# Examples:
#   docker run … agentarmy-forge:local
#   docker run -e MODE=generate … agentarmy-forge:local \
#     -- --source file:///work/model.yaml --target csharp --out /work/out
set -eu

MODE="${MODE:-serve}"

case "$MODE" in
  serve)
    exec python -m forge.server
    ;;
  generate)
    # Strip a leading `--` if present (POSIX argv passthrough convention).
    if [ "${1:-}" = "--" ]; then shift; fi
    exec python -m forge.cli generate "$@"
    ;;
  ingest-validate)
    if [ "${1:-}" = "--" ]; then shift; fi
    exec python -m forge.cli validate "$@"
    ;;
  doctor)
    exec /opt/agentarmy/scripts/forge-doctor.sh "$@"
    ;;
  *)
    echo "FATAL: unknown MODE=$MODE (expected serve|generate|ingest-validate|doctor)" >&2
    exit 2
    ;;
esac
