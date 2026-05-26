#!/bin/sh
# fuseki-doctor.sh — prove the Fuseki super-image from OUTSIDE.
#
#   1/4 readiness                  /$/ping -> 200
#   2/4 sieve-accepts-conformant   bundled good.ttl against shapes.ttl -> loads
#   3/4 sieve-rejects-violating    bundled bad.ttl  against shapes.ttl -> reject (the sieve holds)
#   4/4 construct-emits            SPARQL CONSTRUCT returns the loaded triples as JSON-LD
#
# Run from the image dir (cd's there). Needs curl + docker compose.
set -eu

# Git Bash / MSYS on Windows otherwise rewrites POSIX paths like
# `/opt/agentarmy/...` into Windows form (`C:/Program Files/Git/opt/...`) when
# forwarding args to `docker.exe` — that breaks `docker compose exec` paths into
# the container. Harmless on Linux/macOS.
export MSYS_NO_PATHCONV=1

cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
COMPOSE="${COMPOSE:-docker compose -f examples/compose.fuseki.example.yml}"
SVC="${FUSEKI_SERVICE:-fuseki}"
BASE="${FUSEKI_URL:-http://localhost:3030}"
DS="${DS_NAME:-knowledge}"
READY_TIMEOUT="${READY_TIMEOUT:-120}"

fails=0
pass() { printf '  [PASS] %s\n' "$1"; }
fail() { printf '  [FAIL] %s\n' "$1"; fails=$((fails + 1)); }
hdr()  { printf '\n== %s ==\n' "$1"; }

hdr "1/4 readiness"
i=0; ready=0
while [ $i -lt $READY_TIMEOUT ]; do
  if curl -fsS "$BASE/\$/ping" >/dev/null 2>&1; then ready=1; break; fi
  i=$((i + 2)); sleep 2
done
if [ $ready -eq 1 ]; then pass "GET /\$/ping -> 200 (Fuseki up)"
else fail "not ready after ${READY_TIMEOUT}s"; $COMPOSE logs --tail=30 "$SVC" 2>&1 || true; exit 1; fi

hdr "2/4 sieve — accept conformant data"
if $COMPOSE exec -T "$SVC" sh /opt/agentarmy/scripts/sieve.sh \
    /opt/agentarmy/fixtures/good.ttl \
    /opt/agentarmy/fixtures/shapes.ttl >/dev/null 2>&1; then
  pass "good.ttl accepted (loaded into $DS)"
else fail "good.ttl was rejected (sieve too strict?)"; fi

hdr "3/4 sieve — reject violating data (the sieve must hold)"
if $COMPOSE exec -T "$SVC" sh /opt/agentarmy/scripts/sieve.sh \
    /opt/agentarmy/fixtures/bad.ttl \
    /opt/agentarmy/fixtures/shapes.ttl >/dev/null 2>&1; then
  fail "bad.ttl was ACCEPTED — the sieve failed!"
else pass "bad.ttl rejected (sieve held: violation report emitted)"; fi

hdr "4/4 construct-emits (SPARQL emission)"
body="$(curl -fsS -G --data-urlencode 'query=CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o } LIMIT 25' \
        -H 'Accept: application/ld+json' "$BASE/$DS/sparql" || true)"
case "$body" in
  *'@graph'*|*'@id'*|*'@context'*) pass "CONSTRUCT returned JSON-LD (knowledge emitted)" ;;
  *) fail "CONSTRUCT did not return JSON-LD: $(printf '%s' "$body" | head -c 120)" ;;
esac

hdr "result"
if [ $fails -eq 0 ]; then
  printf 'Fuseki super-image doctor: ALL CHECKS PASSED\n'
else
  printf 'Fuseki super-image doctor: %s FAILURE(S)\n' "$fails"
fi
[ $fails -eq 0 ]
