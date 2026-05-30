#!/bin/sh
# clock-skew-doctor.sh — prove the cross-cluster clock-skew SLI from OUTSIDE (ARC-ADR-038 §5).
#
#   1/2 readiness    bridge /healthz -> 200 (NATS reachable behind it)
#   2/2 skew-flows   publish a fleet.pin.recorded CloudEvent (carrying an HLC) on an ISOLATED
#                    JetStream stream (skewcheck.>, never overlaps fleet.>), pull it back, run
#                    the baked clock_skew SLI, and assert a plausible fleet.clock.skew_ms metric.
#
# Isolated + self-cleaning: the SKEWCHECK stream is created and deleted, so the shared FLEET
# stream and other consumers are left untouched. Run from the image dir; needs docker compose.
# Requires an image built with scripts/clock_skew.py baked (setup.sh rebuilds it).
set -eu
export MSYS_NO_PATHCONV=1
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"

COMPOSE="${COMPOSE:-docker compose -f examples/compose.event-bridge.example.yml}"
SVC="${BRIDGE_SERVICE:-bridge}"
BASE="${BRIDGE_URL:-http://localhost:8080}"
READY_TIMEOUT="${READY_TIMEOUT:-60}"

fails=0
pass() { printf '  [PASS] %s\n' "$1"; }
fail() { printf '  [FAIL] %s\n' "$1"; fails=$((fails + 1)); }
hdr()  { printf '\n== %s ==\n' "$1"; }

hdr "1/2 readiness"
i=0; ok=0
while [ $i -lt $READY_TIMEOUT ]; do
  if curl -fsS "$BASE/healthz" >/dev/null 2>&1; then ok=1; break; fi
  i=$((i + 2)); sleep 2
done
if [ $ok -eq 1 ]; then pass "GET /healthz -> 200"
else fail "not ready after ${READY_TIMEOUT}s"; $COMPOSE logs --tail=30 "$SVC" 2>&1 || true; exit 1; fi

hdr "2/2 skew-flows (publish HLC event -> SLI emits fleet.clock.skew_ms)"
if $COMPOSE exec -T "$SVC" python - <<'PY'
import asyncio, json, os, sys, time
sys.path.insert(0, "/opt/agentarmy/scripts")
import clock_skew
import nats

STREAM, SUBJ = "SKEWCHECK", "skewcheck.pin.recorded"


async def m():
    nc = await nats.connect(os.environ.get("NATS_URL", "nats://nats:4222"))
    js = nc.jetstream()
    # Dedicated isolated stream — subjects do not overlap fleet.>, so FLEET is untouched.
    try:
        await js.delete_stream(STREAM)
    except Exception:
        pass
    await js.add_stream(name=STREAM, subjects=["skewcheck.>"])

    now_ms = time.time_ns() // 1_000_000
    evt = {
        "specversion": "1.0", "id": "skew-doctor", "source": "urn:agentarmy:mc",
        "type": "fleet.pin.recorded", "time": "2026-01-01T00:00:00.000Z",
        "hlc": f"{now_ms}:0", "data": {"content_hash": "skew-doctor"},
    }
    await js.publish(SUBJ, json.dumps(evt).encode())

    sub = await js.pull_subscribe(SUBJ, durable="skewchk", stream=STREAM)
    msgs = await sub.fetch(1, timeout=8)
    rec = None
    for msg in msgs:
        rec = clock_skew.emit_skew(json.loads(msg.data.decode()))  # prints the NDJSON metric
        await msg.ack()

    assert rec is not None and rec["type"] == "fleet.pin.recorded", rec
    assert abs(rec["value"]) < 60000, ("implausible skew", rec)
    print("SKEW_OK " + json.dumps(rec))

    try:
        await js.delete_stream(STREAM)  # leave NATS exactly as found
    except Exception:
        pass
    await nc.drain()


asyncio.run(m())
PY
then pass "fleet.clock.skew_ms emitted from a real bus message (FLEET untouched)"
else fail "skew SLI did not emit a plausible metric"; fi

hdr "result"
if [ $fails -eq 0 ]; then
  printf 'Clock-skew doctor: ALL CHECKS PASSED — skew SLI flowing end-to-end\n'
else
  printf 'Clock-skew doctor: %s FAILURE(S)\n' "$fails"
fi
[ $fails -eq 0 ]
