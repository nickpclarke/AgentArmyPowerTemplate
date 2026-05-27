# ARC-ADR-001 — Pub/Sub Broker Selection for Cross-Spoke Eventing

- **Status:** Proposed
- **Date:** 2026-05-26
- **Deciders:** middle-core maintainers
- **Consulted:** backend-core, frontend-core
- **Informed:** AgentArmy hub

## Context and Problem Statement

Middle-core is the provider-neutral semantic and governance layer between
`frontend-core` and `backend-core`. Today every cross-spoke interaction is
synchronous HTTP. As use cases UC-01–UC-16 expand, several flows want
asynchronous fan-out that HTTP request/response cannot model cleanly:

- **Knowledge-landed notifications** — backend-core finishes an ingest;
  middle-core, frontend-core, and tool-promotion need to react independently
  without backend-core enumerating consumers.
- **Evidence event log** — "evidence is a primitive" implies a replayable
  audit stream that lives outside any single workflow's memory.
- **Tool-promotion re-evaluation** — capability evidence aging out should
  trigger re-checks across consumers that don't know about each other.

We need to pick **one** durable pub/sub transport and **one** wire envelope
that work across the polyglot fleet (Python modelgen, C# runtime, JS frontend)
and do not violate the charter's provider-neutral stance.

### Scope: pub/sub vs. durable workflows

This ADR covers **decoupled fan-out across services**, not workflow
orchestration. Middle-core's BPMN scenarios, state-machine lifecycle
transitions, MCP tool-promotion gating, and HITL waits are workflow-shaped
and belong on a durable execution engine (Temporal-class), not a message
bus. A separate ADR will cover that. The rule of thumb:

| Concern | Engine |
|---|---|
| Middle-core code must survive crash mid-step | durable workflow |
| Something outside middle-core reacts when middle-core finishes | pub/sub (this ADR) |

## Decision Drivers

1. **Provider-neutral by charter.** Middle-core exists to keep meaning
   independent of any single provider. A pub/sub choice that hard-couples
   middle-core to one cloud actively contradicts that.
2. **Polyglot clients.** Python (modelgen), C#/.NET (runtime), JS
   (frontend-core) must all be first-class — no second-tier SDKs.
3. **Dev parity with prod.** The local lane is `docker compose up`. The
   broker must run in compose without managed-service stubs.
4. **Durable + replayable.** At-least-once delivery, consumer offsets,
   replay from a position; not fire-and-forget.
5. **One tool covers queue and log semantics.** The fan-out use case is
   work-queue-shaped; the evidence audit is log-shaped. Picking two
   technologies doubles the ops surface.
6. **Operational floor.** Prototype scale today (single-digit producers,
   handful of consumers). The broker must not require a dedicated
   platform team.
7. **Envelope portability.** The wire format must outlive any broker
   choice — we should be able to swap brokers without rewriting
   producers and consumers.

## Considered Options

1. **NATS JetStream** with CloudEvents v1.0 envelope
2. **Azure Service Bus** with CloudEvents v1.0 envelope
3. **Google Cloud Pub/Sub** with CloudEvents v1.0 envelope
4. **Apache Kafka / Redpanda** with CloudEvents v1.0 envelope

## Decision Outcome

**Chosen: NATS JetStream with CloudEvents v1.0 as the wire envelope.**

- **Broker:** NATS JetStream — self-hosted in `docker-compose.yml` for dev
  and CI; deployed as a stateful workload on Azure Container Apps (or
  Synadia Cloud) for shared environments.
- **Envelope:** CloudEvents v1.0, JSON format, transported as a NATS
  message with the CloudEvents binding for NATS. This keeps producers and
  consumers broker-agnostic at the message-shape level.
- **Subject naming:** `aax.<spoke>.<domain>.<event>.v<n>` (e.g.
  `aax.backend.knowledge.landed.v1`). Streams group by `aax.<spoke>.>`.
- **Delivery:** at-least-once, durable consumers with explicit ack,
  per-stream DLQ as `aax.dlq.<stream>`.
- **Schemas:** event schemas live in `contracts/events/` alongside the
  existing OpenAPI vendoring lane, validated by the modelgen drift gate.

### Positive Consequences

- Charter-aligned: NATS is portable across Azure, GCP, on-prem, and
  Synadia managed — no cloud coupling.
- One technology covers both work-queue (durable consumer groups) and
  log-replay (JetStream stream replay from offset) needs.
- First-class clients in all three languages (Python `nats-py`, .NET
  `NATS.Client`, JS `nats.js`), maintained by the same upstream.
- `docker compose up` keeps working: a single NATS container is enough.
- CloudEvents envelope makes the transport replaceable later without
  touching producer/consumer code.
- Lightweight enough to live alongside ArcadeDB without justifying a
  new dedicated cluster.

### Negative Consequences

- Less managed than Service Bus or Google Pub/Sub — running JetStream
  in production means owning a stateful workload (storage, backup,
  upgrade). Mitigated by deferring to Synadia Cloud if ops becomes
  painful.
- Smaller hosted-service ecosystem in 2026 than Kafka — fewer
  drop-in observability and CDC integrations.
- CloudEvents-over-NATS binding is less ubiquitous than
  CloudEvents-over-HTTP; consumers must use a small shared helper for
  envelope decode rather than copy-pasting framework code.

## Pros and Cons of the Options

### NATS JetStream + CloudEvents

- ✅ Provider-neutral; identical on Azure, GCP, on-prem, Synadia
- ✅ Polyglot SDK parity across Python, .NET, JS
- ✅ Queue + log + KV in one binary
- ✅ Trivial dev story — one container in compose
- ✅ Subject hierarchy fits a "spoke.domain.event" namespace
- ❌ Self-hosting JetStream requires owning storage and upgrade
- ❌ Smaller managed-ecosystem footprint than Kafka

### Azure Service Bus + CloudEvents

- ✅ Fully managed; ACA and ArcadeDB are already on Azure
- ✅ Mature .NET SDK; tight Azure identity integration
- ✅ DLQ, sessions, and scheduled delivery built in
- ❌ Couples middle-core to Azure; violates the provider-neutral charter
- ❌ Local-dev story relies on Service Bus emulator or stubs — no true
  parity with prod
- ❌ Topic/subscription model is queue-shaped; weak as an event log

### Google Cloud Pub/Sub + CloudEvents

- ✅ Fully managed; aligns with the listed GCP project
- ✅ Strong throughput and global availability
- ❌ ACA-hosted producers in Azure pay inter-cloud egress
- ❌ Same provider-coupling concern as Service Bus, in the other direction
- ❌ No serious local-dev parity (emulator exists but lags)

### Apache Kafka / Redpanda + CloudEvents

- ✅ Industry-standard durable log; replay and CDC story unmatched
- ✅ Redpanda gives a single-binary, compose-friendly local lane
- ❌ Heavier ops burden than current scale justifies
- ❌ Consumer-group semantics are richer than current consumers need
- ❌ Schema-registry expectation pushes a second piece of infra

## Confirmation

The decision is confirmed when:

1. `docker-compose.yml` includes a `nats` service running JetStream and
   middle-core's `/health` reports broker reachability.
2. `contracts/events/` contains at least one event schema
   (`backend.knowledge.landed.v1`) with a CloudEvents JSON example fixture.
3. A modelgen drift gate validates event schemas the same way it
   validates the OpenAPI contract today.
4. A round-trip integration test publishes a CloudEvent on
   `aax.backend.knowledge.landed.v1` and a middle-core consumer acks it,
   with replay-from-offset proven in the same test.
5. The ADR is referenced from `docs/middle-core-charter.md` under "What
   the layer owns."

## More Information

- **Related:** ADR for durable workflow engine selection (Temporal-class,
  TBD). That ADR will cover BPMN scenario execution, state-machine
  lifecycle, MCP gating, and HITL waits — explicitly out of scope here.
- **Standards:** CloudEvents v1.0 (CNCF), NATS JetStream subject and
  stream conventions, AsyncAPI 3.0 for documenting event contracts.
- **Follow-ups:**
  - Decide whether AsyncAPI 3.0 docs are generated from the same modelgen
    pipeline that produces OpenAPI today.
  - Decide hosting: Synadia Cloud vs. self-hosted JetStream on ACA, once
    the first cross-spoke consumer ships.
  - Define the `aax.dlq.*` redrive runbook.
