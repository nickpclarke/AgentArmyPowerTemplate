#!/usr/bin/env bash
# AgentArmy local-stack doctor — probe every service from the host.
# Each check is independent; a failure on one doesn't short-circuit the rest,
# so you see the full picture in one pass. Exits non-zero if any check fails.
set -u
export MSYS_NO_PATHCONV=1

passes=0
fails=0
total=5

check() {
  local n="$1" desc="$2" code="$3"
  echo
  echo "== $n/$total $desc =="
  if eval "$code"; then
    echo "  [PASS]"
    passes=$((passes + 1))
  else
    echo "  [FAIL]"
    fails=$((fails + 1))
  fi
}

# Use curl with -sS (silent + show errors) and -o /dev/null for the body.
# --max-time keeps a hung service from blocking the whole doctor.
# Accept any 2xx as success — ArcadeDB signals ready with 204 (no body),
# Fuseki + NATS + the bridge return 200. All count as "ready."
hit() {
  local url="$1"
  local code
  code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 "$url" || echo "000")
  echo "  $url -> $code"
  [[ "$code" =~ ^2[0-9][0-9]$ ]]
}

check 1 "ArcadeDB readiness"   'hit http://localhost:2480/api/v1/ready'
# Postgres has no HTTP endpoint — exec pg_isready inside its container.
check 2 "Postgres pg_isready" '
  out=$(docker exec agentarmy-postgres pg_isready -U dbos -d dbos_system 2>&1)
  echo "  $out"
  [[ "$out" == *"accepting connections"* ]]
'
check 3 "NATS JetStream /healthz" 'hit http://localhost:8222/healthz'
check 4 "Event-bridge /healthz"   'hit http://localhost:8080/healthz'
check 5 "Fuseki /\$/ping"         'hit http://localhost:3030/$/ping'

echo
echo "── result ──"
echo "$passes/$total passed, $fails failed"
[ "$fails" -eq 0 ]
