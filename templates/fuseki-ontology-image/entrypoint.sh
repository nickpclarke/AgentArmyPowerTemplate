#!/bin/sh
# Dispatch for the Fuseki super-image. One image, several interfaces:
#   server  (default)  → TDB2-backed fuseki-server on /knowledge
#   sieve   <data> [shapes] [ds]  → strict SHACL gate → GSP load on pass
#   emit    <sparql> [accept] [ds] → SPARQL CONSTRUCT/SELECT result
#   shacl|sparql|riot|tdb2.tdbloader|robot|pyshacl <args>   pass-through CLIs
#   <any command>      runs as-is (shell, python, etc.)
set -e

DS_NAME="${DS_NAME:-knowledge}"
DATA_DIR="/fuseki/databases/${DS_NAME}"

# locate fuseki-server across image layouts (apache/jena-fuseki may vary)
fuseki_bin() {
  if command -v fuseki-server >/dev/null 2>&1; then echo "fuseki-server"
  elif [ -x /jena-fuseki/fuseki-server ]; then echo "/jena-fuseki/fuseki-server"
  elif [ -x /opt/fuseki/fuseki-server ]; then echo "/opt/fuseki/fuseki-server"
  else return 1; fi
}

case "${1:-server}" in
  server)
    shift 2>/dev/null || true
    # Default: persistent TDB2 dataset on /knowledge (override by passing args).
    if [ $# -eq 0 ]; then
      mkdir -p "$DATA_DIR" 2>/dev/null || true
      set -- --tdb2 --update --loc="$DATA_DIR" "/${DS_NAME}"
    fi
    bin=$(fuseki_bin) || { echo "fuseki-server not found in image" >&2; exit 127; }
    exec "$bin" "$@"
    ;;
  sieve)  shift; exec sh /opt/agentarmy/scripts/sieve.sh "$@" ;;
  emit)   shift; exec sh /opt/agentarmy/scripts/emit.sh  "$@" ;;
  shacl|sparql|riot|tdb2.tdbloader|tdbloader|robot|pyshacl)
    exec "$@" ;;
  *)      exec "$@" ;;
esac
