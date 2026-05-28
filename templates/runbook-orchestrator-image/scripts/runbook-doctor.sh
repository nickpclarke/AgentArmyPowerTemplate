#!/bin/sh
# runbook-doctor.sh — prove the runbook-orchestrator image from OUTSIDE.
#
#   1/4 readiness            /healthz -> 200, NATS connected, triggers subscribed
#   2/4 all-runbooks-valid   GET /runbooks shows no invalid files
#   3/4 event-trigger-fires  publish a CloudEvent to fleet.siem.phishing ->
#                            the phishing runbook runs -> a completion event lands
#                            on fleet.runbook.completed (the headline promise)
#   4/4 rejects-invalid      `validate` on a malformed file -> non-zero exit
#
# Run from the image dir (cd's there). Needs curl + docker compose.
set -eu
export MSYS_NO_PATHCONV=1

cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"

COMPOSE="${COMPOSE:-docker compose -f examples/compose.runbook.example.yml}"
SVC="${ORCH_SERVICE:-orchestrator}"
BASE="${ORCH_URL:-http://localhost:8088}"
SUBJECT="${TRIGGER_SUBJECT:-fleet.siem.phishing}"
PHISH_ID="playbook--a1b2c3d4-0000-4abc-8def-000000000000"
READY_TIMEOUT="${READY_TIMEOUT:-60}"

fails=0
pass() { printf '  [PASS] %s\n' "$1"; }
fail() { printf '  [FAIL] %s\n' "$1"; fails=$((fails + 1)); }
hdr()  { printf '\n== %s ==\n' "$1"; }

hdr "1/4 readiness"
i=0; ok=0
while [ $i -lt $READY_TIMEOUT ]; do
  if curl -fsS "$BASE/healthz" >/dev/null 2>&1; then ok=1; break; fi
  i=$((i + 2)); sleep 2
done
if [ $ok -eq 1 ]; then
  health="$(curl -fsS "$BASE/healthz")"
  pass "GET /healthz -> 200"
  printf '%s' "$health" | grep -q "$SUBJECT" \
    && pass "trigger subject subscribed ($SUBJECT)" \
    || fail "subject $SUBJECT not in subscribed list: $health"
else
  fail "not ready after ${READY_TIMEOUT}s"; $COMPOSE logs --tail=30 "$SVC" 2>&1 || true; exit 1
fi

hdr "2/4 all-runbooks-valid"
runbooks="$(curl -fsS "$BASE/runbooks")"
if printf '%s' "$runbooks" | grep -q '"valid": false'; then
  fail "at least one runbook is invalid: $runbooks"
else
  pass "every indexed runbook is valid"
fi

hdr "3/4 event-trigger-fires (publish -> run -> completion)"
echo "  publishing a CloudEvent to $SUBJECT ..."
$COMPOSE exec -T "$SVC" python -c "
import asyncio, json, os, nats
async def m():
    nc = await nats.connect(os.environ.get('NATS_URL','nats://nats:4222'))
    js = nc.jetstream()
    evt = {'specversion':'1.0','id':'doctor','type':'$SUBJECT','source':'doctor',
           'data':{'severity':'low','user':'alice'}}
    await js.publish('$SUBJECT', json.dumps(evt).encode())
    await nc.drain()
asyncio.run(m())
" >/dev/null 2>&1 || { fail "could not publish trigger event"; }

echo "  reading back from fleet.runbook.completed ..."
recv="$($COMPOSE exec -T "$SVC" python -c "
import asyncio, json, os, sys, nats
async def m():
    nc = await nats.connect(os.environ.get('NATS_URL','nats://nats:4222'))
    js = nc.jetstream()
    sub = await js.pull_subscribe('fleet.runbook.completed', durable='doctor-completed', stream='FLEET')
    try:
        for msg in await sub.fetch(5, timeout=10):
            print(msg.data.decode()); await msg.ack()
    except Exception as e:
        print('TIMEOUT:', e); sys.exit(1)
    await nc.drain()
asyncio.run(m())
" 2>&1 | tail -5 || true)"
if printf '%s' "$recv" | grep -q "$PHISH_ID"; then
  pass "phishing runbook ran in response to the bus event (completion observed)"
else
  fail "no completion event for $PHISH_ID; got: $(printf '%s' "$recv" | head -c 200)"
fi

hdr "4/4 rejects-invalid"
code=0
$COMPOSE exec -T "$SVC" sh -c \
  'printf "{\"type\":\"playbook\",\"spec_version\":\"cacao-1.0\"}" > /tmp/bad.json; \
   python /opt/agentarmy/scripts/runbook_engine.py validate /tmp/bad.json' >/dev/null 2>&1 || code=$?
if [ "$code" -ne 0 ]; then pass "malformed runbook rejected (validate exit $code)"
else fail "validate accepted a malformed runbook"; fi

hdr "result"
if [ $fails -eq 0 ]; then
  printf 'Runbook-orchestrator doctor: ALL CHECKS PASSED — runbooks fire on bus events ✅\n'
else
  printf 'Runbook-orchestrator doctor: %s FAILURE(S)\n' "$fails"
fi
[ $fails -eq 0 ]
