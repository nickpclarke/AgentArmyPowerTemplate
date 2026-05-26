# ARC-ADR-022 — Event Bus Bridges: HTTP ↔ NATS + CloudEvents

| Field | Value |
|---|---|
| ID | ARC-ADR-022 |
| Status | Proposed |
| Date | 2026-05-26 |
| Deciders | Hub owner (HITL — placement is the open call) |
| Supersedes | — |
| Superseded by | — |
| Tags | event-bus, pub-sub, webhooks, nats, jetstream, cloudevents, bridges, image-standard, security |

---

## Context

The fleet just picked **NATS JetStream + CloudEvents v1.0** as the durable cross-spoke pub/sub
transport in middle-core's local `ARC-ADR-001` (PR #73; impl issue middle-core #74). A live broker
is up locally (`nats:2.10-alpine -js`, `localhost:4222` client, `:8222` monitor; `/healthz` ok) — see
the hub heartbeat extension that surfaces broker reachability per cycle.

NATS does **not** speak HTTP webhooks natively. The fleet needs **bridges** in both directions so
HTTP-only event sources/sinks meet the bus:

- **Inbound (HTTP webhook → NATS)** — verify signature → wrap as CloudEvent → publish to a subject.
- **Outbound (NATS → HTTP webhook)** — durable JetStream push-consumer → `POST` each message to
  a configured URL → retry on non-2xx → DLQ on max-deliver.

Primary near-term sources/sinks: **GitHub** (PR/issue/comment/workflow_run) and **Slack** (notify
on merges/dispatches). Future: Stripe, Linear, Postman monitor callbacks.

> **Naming note — ADR-namespace collision:** middle-core's `ARC-ADR-001` (pub/sub broker) is a
> *different* sequence from the hub's `ARC-ADR-001` (HITL pattern). Both share the `ARC-ADR`
> prefix. Worth a small follow-up rename (e.g. `MC-ADR-001`) or a hub-side ADR formally adopting
> the broker choice. Out of scope here; this ADR builds on the choice as given.

## Decision Drivers

| # | Driver |
|---|---|
| D1 | **Minimal infra** — no managed-service dependency unless it pays for itself; no K8s required for v1. |
| D2 | **CloudEvents v1.0 envelope** end-to-end — same payload travels NATS or HTTP. |
| D3 | **Zero public-endpoint surface where possible** — webhooks need a URL; avoid one if a source already runs inside our infra (e.g. GitHub Actions). |
| D4 | **Security by default** — HMAC verification, replay protection, secrets in Key Vault, no plain env keys. |
| D5 | **Conforms to the Image Standard** — `image.json` + setup + external doctor + contract registry entry. |
| D6 | **Owned and small** — bridges are well-understood ~50-line components; keep them ours unless complexity forces a managed gateway. |

## Considered Options (bridge architecture)

1. **Roll our own — Python FastAPI + `nats-py`** — `~50` LOC per direction; HMAC verify, CloudEvents wrap, JS push-consumer + retry/DLQ. Full control, fits the fleet's Python stack, contract-first via OpenAPI.
2. **Managed webhook gateway** — Hookdeck / Webhook Relay / Svix. Free retries/observability + ngrok-style tunneling, but $$, vendor lock, secret-sharing.
3. **Knative Eventing** — CNCF standard, many sources, CloudEvents-native — **but needs Kubernetes**. Overkill at current scale.
4. **Apache Camel-K** — 200+ connectors, heavy Java ops.
5. **GH Actions → NATS direct** *(skips the inbound bridge for GitHub-sourced events)* — a step at the end of relevant workflows publishes a CloudEvent to NATS via a tiny CLI. **Zero public endpoint**, uses GH Actions infra. Only covers GH-sourced events; pair with (1) for non-GH sources.

## Decision Outcome (Proposed)

**Hybrid: Option 5 now + Option 1 when the second source appears.** Build it as **`templates/event-bridge-image/`** — instance #5 of the [Image Standard](../image-standard.md). One image, two entrypoint modes (`serve-inbound` / `relay-outbound`); same code reuses signature + CloudEvents helpers.

- **Phase 0 (this ADR):** ship the **template** — Dockerfile, `image.json`, `entrypoint.sh`, `scripts/{webhook-receiver.py, nats-relay.py, event-bus-doctor.sh}`, `setup.sh`/`setup.ps1`, README, a tiny **GH-Actions reusable workflow** (`publish-cloudevent.yml`) that publishes a CloudEvent to NATS at workflow-end. No public endpoint yet.
- **Phase 1:** wire **a few high-value subjects** — `fleet.repo.*` (PR/issue events from GH Actions reusable workflow), `fleet.contract.*` (heartbeat emits when a contract gap is dispatched), `fleet.deploy.*` (artifact promotion). Subscribe `notification` consumers (Slack relay) to whatever is interesting.
- **Phase 2:** when a non-GH source (Stripe, etc.) appears or an external integrator wants webhooks IN, deploy the **inbound receiver** to ACA with `cloudflared` for dev tunnels.

> Placement choice — **standalone hub template** (recommended) keeps it decoupled and vendorable to any spoke. Alternatives (middle-core / backend-core) couple the bus with another concern. **Open decision** — see "Open" below.

## Security (must-haves)

- **HMAC-SHA256** on GitHub webhooks via `X-Hub-Signature-256`; verify with **`hmac.compare_digest`** (constant-time). The GH-Actions path doesn't need this — events come from inside the trust boundary.
- **Replay protection** — TTL cache of `X-GitHub-Delivery` IDs (e.g. 5 min) so an attacker can't replay a captured webhook.
- **Egress secrets** (Slack URL, etc.) via **Azure Key Vault** secret references — never plain env, never logged.
- **CloudEvents v1.0 envelope** — prevents schema confusion across producers; consumers bind to `type` + `source`.
- **Prefer well-tested security libraries** over bespoke: stdlib `hmac`, `cryptography` for KV resolution, pydantic for input validation (RFC 9457 errors), `slowapi` if rate-limit is needed on the receiver. No hand-rolled crypto.

## Consequences

- **+** One small surface for all event traffic; one envelope (CloudEvents); one broker (JetStream).
  Replaces ad-hoc per-source webhook handlers with one auditable path.
- **+** GH-events-via-Actions path means **no public webhook endpoint for the most common source** — large security/operational simplification.
- **+** Conforming to the Image Standard means the bridge is doctored, contract-registered, and
  inventoried by the heartbeat (it counts as one more image-standard instance).
- **−** A `nats` service has to be reachable from the bridge runtime (ACA networking design when
  Phase 2 lands — same lane as middle-core).
- **−** Outbound retry/DLQ logic is on us; gets exercised only when external sinks misbehave.
  Mitigation: standard JS push-consumer config (`MaxDeliver`, `BackOff`, DLQ subject).

## Implementation outline (Phase 0 deliverables)

1. **`templates/event-bridge-image/`** (hub) — Image Standard instance #5:
   - `Dockerfile` — `FROM python:3.12-slim` + `nats-py`, `fastapi`, `uvicorn`, `cloudevents`, `cryptography`, `pydantic`; non-root user.
   - `entrypoint.sh` — `serve-inbound | relay-outbound | <cmd>`.
   - `scripts/webhook-receiver.py` (FastAPI; HMAC verify; CloudEvents wrap; publish).
   - `scripts/nats-relay.py` (JS push-consumer; POST + retry + DLQ).
   - `scripts/event-bus-doctor.sh` — proves *readiness · pub/sub roundtrip · inbound-rejects-bad-sig · outbound-retries-DLQ*.
   - `setup.sh` / `setup.ps1` + `examples/compose.event-bridge.example.yml` + README + `image.json` + `.gitattributes`.
2. **`.github/workflows/publish-cloudevent.yml`** (hub, reusable) — call from any workflow with `{type, source, data}`; uses the `nats` CLI from `nats:2.10-alpine` to publish.
3. **`docs/contracts.md`** — add an "**Event bus** (NATS JetStream + CloudEvents)" row (producer = the fleet; consumers = any subscriber; status = proposed/live-locally).
4. **mkdocs nav** — ADR-022 entry under Architecture Decisions.

## Open decisions

- **Bridge placement** *(this ADR's HITL call)* — **standalone hub template** (recommended), or middle-core, or backend-core. Recommended: hub template.
- **ADR-namespace collision** (middle-core `ARC-ADR-001` ≠ hub `ARC-ADR-001`) — separate small ADR / rename.
- **Subject taxonomy** — `fleet.repo.*` / `fleet.contract.*` / `fleet.deploy.*` as a starting cut; first impl PR proposes the canonical list.

## Related

- middle-core PR #73 — pub/sub broker ADR (NATS JetStream + CloudEvents).
- middle-core #74 — impl: add NATS service to compose (`copilot-task`).
- [ARC-ADR-021](ARC-ADR-021-llm-gateway.md) — guardrails / trusted-boundary pattern that bridges' egress secret handling should follow.
- [Image Standard](../image-standard.md) — instance #5 lands here.
- [docs/contracts.md](../contracts.md) — registry adds the event-bus row.
- [Fleet heartbeat](../fleet-heartbeat.md) — currently checks pull-state; future: subscribe to `fleet.contract.*` for push-style invalidation.
