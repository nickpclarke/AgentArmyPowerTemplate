"""AgentArmy NATS-to-HTTP relay — JetStream push-consumer → POST.

Subscribes to a NATS subject filter (default `fleet.>`), POSTs each CloudEvent
to ${SINK_URL} as `application/cloudevents+json`, acks on 2xx, naks (with
backoff) on 4xx/5xx — JetStream's max-deliver eventually moves it to the
configured DLQ subject. Full retry-policy + DLQ-config tuning is Phase 1.

Environment:
  NATS_URL          default nats://nats:4222
  STREAM_NAME       default FLEET
  SUBJECT_FILTER    default fleet.>
  DURABLE_NAME      default fleet-relay
  SINK_URL          required — where each event POSTs
  SINK_AUTH_HEADER  optional `Authorization: Bearer …` value
"""
from __future__ import annotations

import asyncio
import os
import sys

import httpx
import nats

NATS_URL = os.environ.get("NATS_URL", "nats://nats:4222")
SUBJECT_FILTER = os.environ.get("SUBJECT_FILTER", "fleet.>")
DURABLE = os.environ.get("DURABLE_NAME", "fleet-relay")
SINK_URL = os.environ.get("SINK_URL", "")
SINK_AUTH = os.environ.get("SINK_AUTH_HEADER", "")


async def main() -> None:
    if not SINK_URL:
        print("SINK_URL is required", file=sys.stderr)
        sys.exit(2)

    nc = await nats.connect(NATS_URL)
    js = nc.jetstream()
    sub = await js.subscribe(SUBJECT_FILTER, durable=DURABLE, manual_ack=True)

    headers = {"Content-Type": "application/cloudevents+json"}
    if SINK_AUTH:
        headers["Authorization"] = SINK_AUTH

    print(f"relay: {SUBJECT_FILTER} → {SINK_URL} (durable={DURABLE})", flush=True)
    async with httpx.AsyncClient(timeout=10) as client:
        while True:
            try:
                msg = await sub.next_msg(timeout=30)
            except Exception:
                continue
            try:
                r = await client.post(SINK_URL, content=msg.data, headers=headers)
                if 200 <= r.status_code < 300:
                    await msg.ack()
                else:
                    # JetStream will redeliver per the stream/consumer policy;
                    # DLQ subject is configured at stream level (Phase 1).
                    await msg.nak(delay=5)
            except Exception:
                await msg.nak(delay=5)


if __name__ == "__main__":
    asyncio.run(main())
