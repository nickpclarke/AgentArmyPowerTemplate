# Event-bridge — HTTP ↔ NATS + CloudEvents v1.0

An AgentArmy event-bus bridge in one image: an **inbound** webhook receiver
(HMAC-verified, CloudEvents-wrapped, JetStream-published) and an **outbound**
NATS-to-HTTP relay (JS push-consumer + retry + DLQ). Realizes
[ARC-ADR-022](../../docs/decisions/ARC-ADR-022-event-bus-bridges.md) on top of
the broker choice in middle-core's `ARC-ADR-001` (PR #73) — NATS JetStream +
CloudEvents v1.0. Conforms to the [AgentArmy Image Standard](../../docs/image-standard.md)
(manifest: [`image.json`](image.json)).

## Modes

```
serve-inbound   (default)  uvicorn webhook_receiver on $PORT (default 8080)
relay-outbound             nats-relay.py: JS push-consumer → POST $SINK_URL
<any command>              passthrough (sh, python, nats CLI, …)
```

## Quick start

```bash
./setup.sh            # gen secret · build · up (nats + bridge) · run doctor
.\setup.ps1           # Windows (needs sh on PATH)
```

Doctor proves: **readiness** · **HMAC rejects bad signature** · **events flowing** end-to-end
(POST with good signature → 202 → same CloudEvent reads back from the JetStream `FLEET` stream).
Tear down with `./setup.sh --down`.

## Wire GitHub webhooks

After `setup.sh`, the secret is in `examples/.secrets/github_webhook_secret.txt`:

- **Payload URL:** `http://<your-host>:8080/webhooks/github` (use a tunnel — e.g. `cloudflared tunnel --url http://localhost:8080` — for local dev so GitHub can reach you).
- **Content type:** `application/json`
- **Secret:** the contents of that file.

Each delivery becomes a CloudEvent on `fleet.gh.<event>` (e.g. `fleet.gh.pull_request`).

## Inbound surface

`POST /webhooks/github` — verifies `X-Hub-Signature-256` with `hmac.compare_digest`
(constant-time, secure-by-default), dedups `X-GitHub-Delivery` for a 5-min TTL window
(replay protection), wraps the payload as **CloudEvents v1.0**:

```json
{
  "specversion": "1.0",
  "id": "<X-GitHub-Delivery>",
  "source": "https://github.com/webhook",
  "type": "github.<X-GitHub-Event>",
  "datacontenttype": "application/json",
  "time": "2026-05-26T...",
  "data": { ...the raw webhook body... }
}
```

…and publishes to the `FLEET` JetStream stream (auto-created on boot with the
configured subject filter).

## Outbound surface

`relay-outbound` subscribes a durable JetStream consumer to `SUBJECT_FILTER`
(default `fleet.>`) and POSTs each event to `$SINK_URL` as
`application/cloudevents+json`. Acks on 2xx; naks on non-2xx (JetStream
redelivers per stream policy; DLQ subject is Phase 1).

## Security

| | |
|---|---|
| HMAC SHA-256 | `hmac.compare_digest` constant-time (stdlib). |
| Replay protection | TTL cache on `X-GitHub-Delivery`. |
| Secrets | `*_FILE` (Key Vault / mounted) preferred; env fallback for dev. |
| Non-root runtime | Drops to `bridge` user before `ENTRYPOINT` (CWE-269). |
| Input validation | Pydantic + FastAPI; JSON-only data path; raw fallback never executed. |

## Files

| File | Purpose |
|---|---|
| `image.json` | Image Standard manifest. |
| `Dockerfile` | python:3.12-slim + fastapi + nats-py + httpx + cryptography. |
| `entrypoint.sh` | `serve-inbound | relay-outbound | <cmd>` dispatch. |
| `scripts/webhook_receiver.py` | FastAPI inbound (HMAC + CloudEvents + JS publish). |
| `scripts/nats-relay.py` | JS push-consumer → POST. |
| `scripts/event-bus-doctor.sh` | External doctor (readiness + HMAC + flow). |
| `setup.sh` / `setup.ps1` | One-command bring-up + doctor. |
| `examples/compose.event-bridge.example.yml` | Local stack (nats + bridge). |
| `.gitattributes` | LF for shell scripts (Windows CRLF would break the entrypoint). |

## Related

- [`ARC-ADR-022`](../../docs/decisions/ARC-ADR-022-event-bus-bridges.md) — this decision.
- middle-core `ARC-ADR-001` / PR #73 — broker choice (NATS + CloudEvents).
- `.github/workflows/publish-cloudevent.yml` — reusable GH-Actions step (zero-public-endpoint path for GH-sourced events).
