# ARC-ADR-003 — Certified-Module Auto-Discovery & Deploy

- **Status:** Proposed (number to be reconciled with the hub ADR index)
- **Date:** 2026-05-28
- **Deciders:** middle-core maintainers
- **Consulted:** generator team (external repo), backend-core
- **Informed:** AgentArmy hub, frontend-core
- **Extends:** ARC-ADR-001 (pub/sub broker — NATS JetStream + CloudEvents)

## Context and Problem Statement

The model→code generator (modelgen) has been **split into its own repository**. It
remains the factory that turns `model.yaml` into **certified code modules** — the
generated C# contracts (`templates/middle-core/generated/*.g.cs`), the compiled LangGraph
graph, typed clients, etc. Until now those modules were produced in-tree; now they are
produced *elsewhere* and must be **delivered to middle-core**.

middle-core needs a way to:

1. **Auto-discover** when the external generator has certified a new module (or a new
   version of one), without middle-core polling the generator or the generator enumerating
   consumers.
2. **Deploy** that module into the running middle-core so the platform can, in effect,
   **rebuild itself** from freshly certified output.
3. Do (1) and (2) over the **messaging fabric that already exists** (ARC-ADR-001), with the
   smallest possible new surface — *speed of delivery is the primary driver for v1*.

## Decision

A **certified module is announced as a CloudEvent on NATS JetStream and pulled by
middle-core over the same connection**, then **staged and activated at runtime**. Every
trust/transport/deploy concern is behind a narrow seam so the fast v1 can be hardened later
without touching callers.

### 1. Transport — reuse the secure channel (fastest)

The generator publishes the module **bytes** into a **NATS JetStream Object Store** bucket
(`aax-certified-modules`) and emits a **CloudEvent** announcing it on subject
`aax.fleet.module.certified.v1` (the `aax.fleet.*` convention from the NATS smoke test).
middle-core is already connected to NATS (ARC-ADR-001), so there is **no new registry, no
new credential, no new network path** — the artifact rides the channel that is already
trusted and wired. The fetch is abstracted behind a `Fetcher` protocol, so an OCI registry
(ORAS) or a blob bucket can replace the Object Store later with no change to the
orchestrator.

### 2. Deploy — runtime staging + in-process registry ("the system builds itself")

On discovery, middle-core writes the verified bytes to a **content-addressed staging
directory** and **registers/activates** the module in an in-process `ModuleRegistry`. This
is the **no-git path**: the running service adopts the new certified module without a commit
or redeploy. A `GitVendorSink` stub is kept as a pluggable alternative for when an **audited
PR trail** is wanted (it would open a vendor PR and let existing CI drift-gates take over) —
but that is explicitly *not* the v1 default.

### 3. Trust — checksum now, pluggable to signatures later

v1 verification is a **SHA-256 digest** match: the CloudEvent carries `artifact.digest`
(`sha256:…`); middle-core hashes the fetched bytes and **rejects on mismatch** before
anything is staged. Verification sits behind a `Verifier` protocol, so cosign/sigstore
signatures or a PROV-O evidence-pack attestation (ADR-0002 lineage) can be layered in later
without changing the discovery flow. **Nothing unverified is ever staged or activated.**

### 4. Messaging shape

| Concern | Choice |
|---|---|
| Transport | NATS JetStream (ARC-ADR-001) |
| Announce subject | `aax.fleet.module.certified.v1` |
| Envelope | CloudEvents v1.0 JSON, `type = com.agentarmy.module.certified.v1` |
| Artifact store | NATS JetStream Object Store bucket `aax-certified-modules` |
| Consumer | durable JetStream consumer `middle-core-module-autodiscovery` (at-least-once; ack after stage) |
| Contract | `contracts/module-certified.cloudevent.schema.json` |

The event `data` payload (see the schema for the normative definition):

```json
{
  "moduleId": "middle-core/data-platform-contracts",
  "version": "1.4.0",
  "target": "csharp",
  "artifact": {
    "store": "nats-object",
    "bucket": "aax-certified-modules",
    "object": "middle-core/data-platform-contracts/1.4.0.tar.zst",
    "contentType": "application/zstd",
    "sizeBytes": 12345,
    "digest": "sha256:…"
  },
  "provenance": { "modelSnapshot": "sha256:…", "generatorCommit": "…" },
  "issuedAt": "2026-05-28T22:00:00Z"
}
```

## Flow

```
generator (external repo)                 middle-core (agent_runtime/modules)
─────────────────────────                 ───────────────────────────────────
 certify module
 put bytes → JetStream Object Store
 publish CloudEvent ─────────────────────▶ durable consumer on
   aax.fleet.module.certified.v1            aax.fleet.module.certified.v1
                                            │
                                            ├─ parse + validate envelope   (events.py)
                                            ├─ fetch bytes by ArtifactRef   (fetch.py: Fetcher)
                                            ├─ verify sha256 digest         (verify.py: Verifier)
                                            ├─ stage content-addressed      (sink.py: ModuleSink)
                                            └─ register + activate          (registry.py)
                                            ack ──────────────────────────▶ (re-delivered if not acked)
```

A failed verification or malformed event produces a **rejected** `DiscoveryResult` and the
message is *not* acked into a poison loop — it is recorded and dead-lettered (DLQ wiring is a
follow-up; see Open Questions).

## Consequences

**Positive**
- Fastest possible v1: no new infra, rides the existing trusted channel.
- The platform can adopt freshly certified modules at runtime — the self-build loop.
- Every hard decision (transport, trust, deploy target) is a swappable seam, so hardening is
  additive, not a rewrite.

**Negative / risks**
- Object Store is fine for the module sizes we ship today; very large artifacts may later
  warrant OCI/ORAS (the `Fetcher` seam covers this).
- Runtime hot-activation without a git trail trades auditability for speed; `GitVendorSink`
  exists for when that trade is wrong.
- At-least-once delivery means `handle()` must be **idempotent** (it is: staging is
  content-addressed and re-stage is a no-op).

## Open questions (follow-ups, out of scope for v1)

- Dead-letter subject + retry policy for repeatedly-failing modules.
- Signature/attestation verifier (cosign / PROV-O evidence-pack) — the `Verifier` seam.
- Emitting a `com.agentarmy.module.deployed.v1` acknowledgement event back to the fleet.
- Rollback / pinning a known-good version when a newly activated module misbehaves.

## References

- ARC-ADR-001 — Pub/Sub broker selection (NATS JetStream + CloudEvents)
- `contracts/module-certified.cloudevent.schema.json` — the announce envelope
- `agent_runtime/modules/` — the consumer skeleton implementing this ADR
- `scripts/middle-core/nats-smoke.sh` — the `aax.fleet.*` CloudEvents round-trip precedent
