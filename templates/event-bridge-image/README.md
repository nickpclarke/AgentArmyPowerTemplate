# Event-bridge — HTTP ↔ NATS + CloudEvents v1.0

> **Tier:** `function` ([ARC-ADR-023](../../docs/decisions/ARC-ADR-023-container-tiering-strategy.md)) — small, stateless, independently rolled out. The reference function-tier container.

An AgentArmy event-bus bridge in one image: an **inbound** webhook receiver
(HMAC-verified, CloudEvents-wrapped, JetStream-published) and an **outbound**
NATS-to-HTTP relay (JS push-consumer + retry + DLQ). It also includes the
subscription-aware **NATS-to-webhook projector** for capability
`platform.messaging.update-system`. Realizes
[ARC-ADR-022](../../docs/decisions/ARC-ADR-022-event-bus-bridges.md) on top of
the broker choice in middle-core's `ARC-ADR-001` (PR #73) — NATS JetStream +
CloudEvents v1.0. Conforms to the [AgentArmy Image Standard](../../docs/image-standard.md)
(manifest: [`image.json`](image.json)).

## Modes

```
serve-inbound   (default)  uvicorn webhook_receiver on $PORT (default 8080)
relay-outbound             nats-relay.py: JS push-consumer → POST $SINK_URL
project-webhooks           webhook_projector.py: subscription filters → webhook sinks
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

## Platform update projector

`project-webhooks` is the native adoption path for
`platform.messaging.update-system`. It reads `SUBSCRIPTIONS_FILE`, subscribes to
the active subject scopes, applies exact CloudEvents filters, and POSTs the
original CloudEvent body to matching webhook sinks. Webhook delivery is a
projection from NATS CloudEvents, not a new source of truth.

Configuration contract:
[`contracts/platform-update-subscription.schema.json`](../../contracts/platform-update-subscription.schema.json).
Example:
[`contracts/examples/platform-update-subscription.example.json`](../../contracts/examples/platform-update-subscription.example.json).

Environment:

| Name | Default | Purpose |
|---|---|---|
| `SUBSCRIPTIONS_FILE` | `/etc/agentarmy/platform-update-subscriptions.json` | JSON subscription registry. |
| `PROJECTOR_SECRET_REFS_JSON` | unset | JSON object or file path mapping secret refs to runtime secret values. |
| `PROJECTOR_VALIDATE_SECRETS_ON_START` | `1` | Resolve all active subscription secrets before consuming. |
| `PROJECTOR_ALLOW_LOCAL_HTTP` | `0` | Dev-only override for `http://localhost` sinks. |
| `PROJECTOR_VALIDATE_DNS` | `0` | Optional SSRF guard that rejects hosts resolving to private ranges. |
| `DURABLE_NAME` | `platform-update-webhook-projector` | Durable consumer prefix. |

MECE message families:

- `platform.capability.*`
- `platform.adoption.*`
- `platform.hvfs.*`
- `fleet.agent.*`
- `platform.security.*`

Active sinks must use HTTPS, per-subscription auth, and structured CloudEvents
HTTP POSTs:

```http
POST {sink.url}
Content-Type: application/cloudevents+json
User-Agent: AgentArmy-Webhook-Projector/0.1
X-AgentArmy-Capability: platform.messaging.update-system
X-AgentArmy-Subscription-Id: <subscription id>
X-AgentArmy-Delivery-Id: <stable delivery id>
X-AgentArmy-Attempt: <1-based attempt>
Idempotency-Key: <ce-source>#<ce-id>
```

Supported auth modes:

- `hmac-sha256`: signs `timestamp + "." + body` with
  `X-AgentArmy-Signature-256: t=<unix>,kid=<key id>,sha256=<hmac>`.
- `cloudflare-access-service-token`: sends `CF-Access-Client-Id` and
  `CF-Access-Client-Secret` from secret refs.

`platform.security.*` subscriptions are fail-closed: they must be
`securityTrusted`, `replayable`, HTTPS, and backed by `akv://` secret refs.
Delivery is at-least-once; sinks must dedupe by `X-AgentArmy-Delivery-Id`,
`Idempotency-Key`, or CloudEvents `id`.

## Security

| | |
|---|---|
| HMAC SHA-256 | `hmac.compare_digest` constant-time (stdlib). |
| Replay protection | TTL cache on `X-GitHub-Delivery`. |
| Secrets | `*_FILE` (Key Vault / mounted) preferred; env fallback for dev. |
| Non-root runtime | Drops to `bridge` user before `ENTRYPOINT` (CWE-269). |
| Input validation | Pydantic + FastAPI; JSON-only data path; raw fallback never executed. |
| Projector egress | HTTPS-only active sinks; HMAC-SHA256 or Cloudflare Access auth; unresolved secret refs fail closed. |
| Projector logs | Sink hosts and hashes only; no raw URLs, tokens, `akv://` refs, response bodies, or CloudEvent payloads. |

## Files

| File | Purpose |
|---|---|
| `image.json` | Image Standard manifest. |
| `Dockerfile` | python:3.12-slim + fastapi + nats-py + httpx + cryptography. |
| `entrypoint.sh` | `serve-inbound | relay-outbound | <cmd>` dispatch. |
| `scripts/webhook_receiver.py` | FastAPI inbound (HMAC + CloudEvents + JS publish). |
| `scripts/nats-relay.py` | JS push-consumer → POST. |
| `scripts/webhook_projector.py` | Subscription-aware NATS CloudEvents → webhook projector for `platform.messaging.update-system`. |
| `scripts/test_projector.py` | Unit tests for projector validation, filtering, auth headers, delivery classification, and log redaction. |
| `scripts/event-bus-doctor.sh` | External doctor (readiness + HMAC + flow). |
| `setup.sh` / `setup.ps1` | One-command bring-up + doctor. |
| `examples/compose.event-bridge.example.yml` | Local stack (nats + bridge). |
| `.gitattributes` | LF for shell scripts (Windows CRLF would break the entrypoint). |

## Related

- [`ARC-ADR-022`](../../docs/decisions/ARC-ADR-022-event-bus-bridges.md) — this decision.
- middle-core `ARC-ADR-001` / PR #73 — broker choice (NATS + CloudEvents).
- `.github/workflows/publish-cloudevent.yml` — reusable GH-Actions step (zero-public-endpoint path for GH-sourced events).
