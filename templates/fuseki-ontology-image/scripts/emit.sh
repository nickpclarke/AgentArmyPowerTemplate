#!/bin/sh
# emit.sh — knowledge emission. Run a SPARQL query against the dataset and
# stream the result in the requested format (JSON-LD by default for CONSTRUCT;
# pick application/sparql-results+json for SELECT/ASK).
#
# Usage:  emit.sh <sparql-query> [accept=application/ld+json] [dataset=knowledge]
# Env:    FUSEKI_URL (default http://localhost:3030)
set -eu

Q="${1:?usage: emit.sh <sparql-query> [accept] [dataset]}"
FMT="${2:-application/ld+json}"
DS="${3:-${DS_NAME:-knowledge}}"
BASE="${FUSEKI_URL:-http://localhost:3030}"

curl -fsS -G \
  --data-urlencode "query=$Q" \
  -H "Accept: $FMT" \
  "$BASE/$DS/sparql"
