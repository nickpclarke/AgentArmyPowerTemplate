#!/usr/bin/env sh
# AgentArmy hmac-verify doctor.
#
# Proves four invariants against a running container + a tiny upstream echo
# server (booted as part of the example compose):
#   1. readiness         — /healthz returns 200
#   2. rejects-bad-sig   — POST /verify with a wrong signature returns 401
#   3. accepts-good-sig  — POST /verify with the correct signature returns 200
#                          AND the upstream service was reached (verified by
#                          the upstream echo's request log)
#   4. replay-protection — same delivery-id within REPLAY_TTL_SECONDS — second
#                          attempt returns 409
#
# Usage:
#   ./scripts/hmac-doctor.sh                                    # default localhost:8083
#   HOST=hmac-verify PORT=8083 ./scripts/hmac-doctor.sh         # in-compose
#
# Env (must match the running container):
#   HMAC_SECRET           shared secret (default: doctor-secret)
#   UPSTREAM_CHECK_URL    URL on the echo container exposing its last hit
#                         (default: http://localhost:8085/last)
set -eu

HOST="${HOST:-localhost}"
PORT="${PORT:-8083}"
BASE="http://${HOST}:${PORT}"
HMAC_SECRET="${HMAC_SECRET:-doctor-secret}"
UPSTREAM_CHECK_URL="${UPSTREAM_CHECK_URL:-http://localhost:8085/last}"

PASS=0
FAIL=0
ok()   { printf "  \033[32mPASS\033[0m %s\n" "$1"; PASS=$((PASS+1)); }
fail() { printf "  \033[31mFAIL\033[0m %s\n" "$1"; FAIL=$((FAIL+1)); }

echo "agentarmy hmac-verify doctor"
echo "  base:           ${BASE}"
echo "  upstream check: ${UPSTREAM_CHECK_URL}"
echo

# Helper — compute the GitHub-style "sha256=<hex>" signature for a payload.
PYTHON_BIN="${PYTHON_BIN:-python}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then PYTHON_BIN=python3; fi
sign() {
  # $1 = payload, $2 = secret. Echo "sha256=<hex>".
  printf '%s' "$1" | "$PYTHON_BIN" -c "
import hmac, hashlib, sys, os
body = sys.stdin.buffer.read()
secret = os.environ['SECRET'].encode()
print('sha256=' + hmac.new(secret, body, hashlib.sha256).hexdigest())
" 2>/dev/null
}

# -----------------------------------------------------------------------------
# 1. readiness — /healthz 200
# -----------------------------------------------------------------------------
echo "[1/4] readiness — /healthz returns 200"
READINESS_OK="false"
for i in 1 2 3 4 5 6 7 8 9 10; do
  http_code="$(curl -sS -o /tmp/hmac-health.json -w '%{http_code}' --max-time 3 "${BASE}/healthz" 2>/dev/null || echo 000)"
  if [ "$http_code" = "200" ]; then
    READINESS_OK="true"
    break
  fi
  echo "  attempt $i: HTTP ${http_code} — retrying in 2s"
  sleep 2
done
if [ "$READINESS_OK" = "true" ]; then
  ok "/healthz returns 200"
else
  fail "/healthz never returned 200 in 10 attempts (~20s)"
  echo "summary: ${PASS} pass, ${FAIL} fail"
  exit 1
fi

# Reset the upstream echo's last-hit counter so check #3 is unambiguous.
curl -sS -X POST --max-time 3 "${UPSTREAM_CHECK_URL%/last}/reset" >/dev/null 2>&1 || true

# -----------------------------------------------------------------------------
# 2. rejects-bad-sig — wrong signature -> 401
# -----------------------------------------------------------------------------
echo
echo "[2/4] rejects-bad-sig — POST /verify with a wrong signature returns 401"
PAYLOAD='{"action":"opened","number":1}'
BAD_SIG="sha256=deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
http_code="$(curl -sS -o /tmp/hmac-bad.json -w '%{http_code}' --max-time 5 \
  -H 'Content-Type: application/json' \
  -H "X-Hub-Signature-256: ${BAD_SIG}" \
  -H 'X-GitHub-Delivery: doctor-bad-001' \
  -X POST -d "$PAYLOAD" "${BASE}/verify" 2>/dev/null || echo 000)"
if [ "$http_code" = "401" ]; then
  ok "bad signature -> 401"
else
  fail "expected 401 for bad signature, got ${http_code} (body: $(cat /tmp/hmac-bad.json 2>/dev/null || echo ''))"
fi

# -----------------------------------------------------------------------------
# 3. accepts-good-sig — correct signature -> 200 + upstream was reached
# -----------------------------------------------------------------------------
echo
echo "[3/4] accepts-good-sig — correct signature -> 200 AND upstream was reached"
GOOD_PAYLOAD='{"action":"opened","number":42,"doctor":"good-sig"}'
SECRET="$HMAC_SECRET" export SECRET
GOOD_SIG="$(sign "$GOOD_PAYLOAD" "$HMAC_SECRET")"
http_code="$(curl -sS -o /tmp/hmac-good.json -w '%{http_code}' --max-time 5 \
  -H 'Content-Type: application/json' \
  -H "X-Hub-Signature-256: ${GOOD_SIG}" \
  -H 'X-GitHub-Delivery: doctor-good-001' \
  -X POST -d "$GOOD_PAYLOAD" "${BASE}/verify" 2>/dev/null || echo 000)"
if [ "$http_code" = "200" ]; then
  ok "good signature -> 200"
else
  fail "expected 200 for good signature, got ${http_code} (body: $(cat /tmp/hmac-good.json 2>/dev/null || echo ''))"
fi

# Was the upstream actually reached?  The echo server records the last
# body it saw under GET /last; we look for our distinctive payload marker.
LAST="$(curl -sS --max-time 3 "${UPSTREAM_CHECK_URL}" 2>/dev/null || echo '')"
if echo "$LAST" | grep -q 'good-sig'; then
  ok "upstream echo recorded the proxied request (saw doctor marker)"
else
  fail "upstream echo did NOT see the request (got: ${LAST})"
fi

# -----------------------------------------------------------------------------
# 4. replay-protection — same delivery-id twice within TTL -> 409
# -----------------------------------------------------------------------------
echo
echo "[4/4] replay-protection — same delivery-id within TTL -> 409"
REPLAY_PAYLOAD='{"action":"opened","number":99,"doctor":"replay"}'
REPLAY_SIG="$(sign "$REPLAY_PAYLOAD" "$HMAC_SECRET")"
# First attempt — should be accepted (200).
first_code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 \
  -H 'Content-Type: application/json' \
  -H "X-Hub-Signature-256: ${REPLAY_SIG}" \
  -H 'X-GitHub-Delivery: doctor-replay-001' \
  -X POST -d "$REPLAY_PAYLOAD" "${BASE}/verify" 2>/dev/null || echo 000)"
if [ "$first_code" != "200" ]; then
  fail "first attempt should have been 200 but was ${first_code} — replay setup broken"
else
  # Second attempt with the SAME delivery-id — must be 409.
  second_code="$(curl -sS -o /tmp/hmac-replay.json -w '%{http_code}' --max-time 5 \
    -H 'Content-Type: application/json' \
    -H "X-Hub-Signature-256: ${REPLAY_SIG}" \
    -H 'X-GitHub-Delivery: doctor-replay-001' \
    -X POST -d "$REPLAY_PAYLOAD" "${BASE}/verify" 2>/dev/null || echo 000)"
  if [ "$second_code" = "409" ]; then
    ok "replay of delivery-id 'doctor-replay-001' -> 409"
  else
    fail "expected 409 on replay, got ${second_code} (body: $(cat /tmp/hmac-replay.json 2>/dev/null || echo ''))"
  fi
fi

echo
echo "summary: ${PASS} pass, ${FAIL} fail"
[ "$FAIL" -eq 0 ]
