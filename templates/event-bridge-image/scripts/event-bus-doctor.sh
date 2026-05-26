#!/bin/sh
# event-bus-doctor.sh — prove the event-bridge image from OUTSIDE.
#
#   1/3 readiness                receiver /healthz -> 200
#   2/3 hmac-rejects-bad-sig     POST with WRONG signature -> 401 (the sieve holds)
#   3/3 events-flowing           POST with GOOD signature -> 202; the same
#                                CloudEvent reads back from the JetStream FLEET stream
#
# Run from the image dir (cd's there). Needs curl + openssl + docker compose.
set -eu

# Git Bash / MSYS: don't rewrite /opt paths when calling docker exec.
export MSYS_NO_PATHCONV=1

cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"

COMPOSE="${COMPOSE:-docker compose -f examples/compose.event-bridge.example.yml}"
SVC="${BRIDGE_SERVICE:-bridge}"
BASE="${BRIDGE_URL:-http://localhost:8080}"
SECRET_FILE="${SECRET_FILE:-examples/.secrets/github_webhook_secret.txt}"
SUBJECT_PREFIX="${SUBJECT_PREFIX:-fleet.gh}"
READY_TIMEOUT="${READY_TIMEOUT:-60}"

fails=0
pass() { printf '  [PASS] %s\n' "$1"; }
fail() { printf '  [FAIL] %s\n' "$1"; fails=$((fails + 1)); }
hdr()  { printf '\n== %s ==\n' "$1"; }

hdr "1/3 readiness"
i=0; ok=0
while [ $i -lt $READY_TIMEOUT ]; do
  if curl -fsS "$BASE/healthz" >/dev/null 2>&1; then ok=1; break; fi
  i=$((i + 2)); sleep 2
done
if [ $ok -eq 1 ]; then pass "GET /healthz -> 200"
else fail "not ready after ${READY_TIMEOUT}s"; $COMPOSE logs --tail=30 "$SVC" 2>&1 || true; exit 1; fi

# Bundled fake-GH payload + signature.
SECRET="$(cat "$SECRET_FILE")"
BODY='{"action":"opened","number":99,"repository":{"full_name":"nickpclarke/agentarmy"}}'
DELIVERY="doctor-$(date +%s)-$$"
SIG="sha256=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$SECRET" | sed 's/^.* //')"

hdr "2/3 hmac-rejects-bad-sig (the sieve must hold)"
code="$(curl -s -o /dev/null -w '%{http_code}' -X POST \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=deadbeef" \
  -H "X-GitHub-Event: pull_request" \
  -H "X-GitHub-Delivery: ${DELIVERY}-bad" \
  --data "$BODY" "$BASE/webhooks/github")"
if [ "$code" = "401" ]; then pass "POST with bad signature -> 401"
else fail "expected 401, got $code"; fi

hdr "3/3 events-flowing (good sig -> JetStream -> replay)"
code="$(curl -s -o /tmp/recv-resp.json -w '%{http_code}' -X POST \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: ${SIG}" \
  -H "X-GitHub-Event: pull_request" \
  -H "X-GitHub-Delivery: ${DELIVERY}" \
  --data "$BODY" "$BASE/webhooks/github")"
if [ "$code" = "202" ]; then pass "POST with good signature -> 202 (publish accepted)"
else fail "expected 202, got $code: $(cat /tmp/recv-resp.json 2>/dev/null | head -c 200)"; printf '\n%s failures\n' "$fails"; exit 1; fi

# Replay the message from the stream via a one-shot JS subscribe inside the
# bridge container — events are durable, so order doesn't matter.
echo "  reading back from JetStream FLEET stream..."
recv="$($COMPOSE exec -T "$SVC" python -c "
import asyncio, json, sys, nats, os
async def m():
    nc = await nats.connect(os.environ.get('NATS_URL','nats://nats:4222'))
    js = nc.jetstream()
    sub = await js.pull_subscribe('${SUBJECT_PREFIX}.>', durable='doctor-$$', stream='FLEET')
    try:
        msgs = await sub.fetch(1, timeout=8)
        for msg in msgs:
            print(msg.data.decode()[:300])
            await msg.ack()
    except Exception as e:
        print('TIMEOUT:', e); sys.exit(1)
    await nc.drain()
asyncio.run(m())
" 2>&1 | tail -5 || true)"
if printf '%s' "$recv" | grep -q "${DELIVERY}"; then
  pass "CloudEvent received from JetStream — events FLOWING (id=${DELIVERY})"
else
  fail "did not see delivery id ${DELIVERY} in stream replay; got: $(printf '%s' "$recv" | head -c 200)"
fi

hdr "result"
if [ $fails -eq 0 ]; then
  printf 'Event-bridge doctor: ALL CHECKS PASSED — events flowing end-to-end ✅\n'
else
  printf 'Event-bridge doctor: %s FAILURE(S)\n' "$fails"
fi
[ $fails -eq 0 ]
