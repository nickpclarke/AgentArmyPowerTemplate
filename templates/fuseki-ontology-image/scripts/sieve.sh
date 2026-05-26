#!/bin/sh
# sieve.sh — strict ontology ingest. SHACL-validate <data> against <shapes>;
# only on conformance, load into the Fuseki dataset via the Graph Store Protocol.
# On violation, REJECTS with the conformance report and exits non-zero.
#
# Usage:  sieve.sh <data.ttl> [shapes.ttl=/opt/agentarmy/fixtures/shapes.ttl] [dataset=knowledge]
# Env:    FUSEKI_URL (default http://localhost:3030)
set -eu

DATA="${1:?usage: sieve.sh <data.ttl> [shapes.ttl] [dataset]}"
SHAPES="${2:-/opt/agentarmy/fixtures/shapes.ttl}"
DS="${3:-${DS_NAME:-knowledge}}"
BASE="${FUSEKI_URL:-http://localhost:3030}"

[ -r "$DATA" ]   || { echo "sieve: data file not readable: $DATA" >&2; exit 2; }
[ -r "$SHAPES" ] || { echo "sieve: shapes file not readable: $SHAPES" >&2; exit 2; }

REPORT="$(mktemp 2>/dev/null || echo /tmp/shacl-report.$$)"
trap 'rm -f "$REPORT"' EXIT

# Jena's shacl CLI: exits 0 on completion regardless; the report's sh:conforms
# tells you whether the data passed. Grep for it strictly.
shacl validate --shapes "$SHAPES" --data "$DATA" > "$REPORT" 2>&1 || true

if grep -qE '(sh:conforms|<http://www\.w3\.org/ns/shacl#conforms>)[[:space:]]+true' "$REPORT"; then
  echo "ACCEPTED — $DATA conforms to $SHAPES"
  echo "loading into $BASE/$DS (default graph)..."
  curl -fsS -X POST -H "Content-Type: text/turtle" --data-binary "@$DATA" \
       "$BASE/$DS/data?default" > /dev/null
  echo "loaded."
  exit 0
else
  echo "REJECTED — $DATA does NOT conform to $SHAPES. Report:" >&2
  cat "$REPORT" >&2
  exit 1
fi
