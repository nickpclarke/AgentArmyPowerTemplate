# ARC-ADR-031 — Automated Runbook Orchestration: BPMN 2.0 + OASIS CACAO 2.0 on a Shared Kernel in a Function-Tier Container

| Field | Value |
|---|---|
| ID | ARC-ADR-031 |
| Status | Accepted |
| Date | 2026-05-28 |
| Deciders | Hub owner (Nicky Clarke) — accepted 2026-05-28 (v1 scope; live doctor 4/4) |
| Supersedes | — |
| Superseded by | — |
| Tags | runbooks, playbooks, bpmn, cacao, soar, function-tier, container, event-bus, security, hitl |

---

## Context and Problem Statement

The fleet has an event bus ([ARC-ADR-022](ARC-ADR-022-event-bus-bridges.md): NATS JetStream + CloudEvents) and an `incident-responder` agent persona, but **no executable layer that turns a documented response procedure into an automated, event-triggered run.** "When event X fires, do A, branch on B, fan out to C and D, escalate to a human at E" lives only in prose and in agents' heads.

Two open, mature standards already describe exactly this:

- **BPMN 2.0** (OMG) — XML process orchestration: start/end events, tasks, gateways, sequence flows, message/timer/signal triggers. Strong at event-driven control flow and has a graphical notation.
- **OASIS CACAO 2.0** — JSON security playbooks: a `workflow` map of typed steps (`action`, `if/while/switch-condition`, `parallel`, `playbook-action`), with first-class `agent`/`target` binding and `command` objects (`ssh`, `http-api`, `manual`, `openc2-http`, …). Purpose-built for SOAR.

Neither is a superset of the other (CACAO has no event-wait primitive or diagram; BPMN has no executor/target binding or step variables), and the fleet uses both kinds of artifact: process-shaped runbooks and security playbooks.

**The decision: how should the fleet execute automated runbooks — what runtime, what architectural home, what format support, and what command-execution safety posture?**

---

## Decision Drivers

| # | Driver |
|---|---|
| D1 | **Support both standards, not a bespoke DSL.** Authors should write BPMN or CACAO, not a proprietary format. Interop with existing SOAR/BPMN tooling matters. |
| D2 | **Streamlined + isolated.** The headline requirement: a small helper whose *only* required input is runbook files. No DB, no spoke coupling, runnable standalone with zero network. |
| D3 | **Respond to events and triggers.** It must subscribe to the existing event bus and fire a runbook on a matching event — but event handling must be an *optional layer*, not a hard dependency. |
| D4 | **Fit ARC-ADR-023 function-tier criteria.** Bursty, stateless, independently rolled out, small blast radius — a worker, not a platform service. |
| D5 | **Safe by default for security playbooks.** A playbook executor that blindly runs `ssh`/`bash` against targets is a remote-code-execution engine. The default posture must be observe-and-gate, with real execution opt-in and HITL-gated. |
| D6 | **Reuse fleet primitives.** NATS JetStream + CloudEvents (ARC-ADR-022) for triggers; HITL Decision Artifacts (ARC-ADR-001/-006) for human gates; structured NDJSON / OTel (ARC-ADR-010) for observability. |
| D7 | **Supply-chain minimalism.** Security tooling should minimize its dependency surface. Prefer stdlib + a hardened XML parser over a heavyweight workflow engine. |

---

## Considered Options

### Option A — Hand-rolled minimal interpreter over a shared intermediate representation, Python, function-tier image (recommended)

Both formats are parsed into one **annotated directed graph** (the IR: `Node` + routing fields). A single ~400-line execution kernel runs the IR; only the parsers and condition evaluators are format-specific. Kernel deps: Python stdlib + `defusedxml` (XXE-hardened BPMN parsing). The serve layer (FastAPI + `nats-py`) is optional and degrades gracefully. Default executor is a **safe orchestrator**: `manual` → HITL ack, `http-api`/`emit-event` → publish CloudEvent, `ssh`/`bash`/`powershell` → dry-run.

### Option B — Embed an off-the-shelf BPMN engine (SpiffWorkflow / `bpmn-engine`)

Use a maintained engine for BPMN. **Problem:** CACAO is *not* BPMN — no BPMN engine speaks CACAO's step model, agent/target binding, or STIX-pattern conditions, so CACAO would need a separate runtime anyway. SpiffWorkflow is LGPL (license review for a security container); `bpmn-engine` is Node (a second language in the image). Neither gives the safe-executor posture for free.

### Option C — Heavyweight SOAR/orchestration platform (Zeebe/Camunda, or a hosted SOAR)

Reject on D2/D4/D7: Zeebe needs a Raft broker cluster (~2 GB RAM minimum, durable RocksDB state) — the opposite of a small isolated stateless helper.

### Option D — Status quo: runbooks stay as prose + agent personas

No executable layer; every response is hand-driven. Fails the originating requirement.

---

## Decision Outcome

**Accepted: Option A**, with the **safe-orchestrator** command posture as the shipped v1 default (hub owner decision, 2026-05-28). Real exec / timers / JWS remain open questions for a later version.

The implementation lands as `templates/runbook-orchestrator-image/` (function-tier, `agentarmy-runbook-orchestrator`): one IR, one kernel, two parsers, structural validators, a serve-mode control API + JetStream trigger dispatcher, three bundled fixtures, and an external doctor that proves a bus event fires a runbook end-to-end.

### v1 scope

**In:** parse + validate BPMN and CACAO; the IR kernel (START/END/ACTION/DECISION/PARALLEL/CALL + a pass-through CATCH_EVENT in one-shot mode); `manual`/`emit-event`/dry-run executors; CLI `run`/`validate`; serve mode with NATS event triggers; doctor.
**Out (deferred):** real `ssh`/`bash` execution (opt-in + per-command allowlist + HITL for destructive ops); durable/resumable long waits across restarts; JWS signature verification of playbooks; the full STIX-pattern condition grammar (v1 supports an equality/inequality/numeric subset); timer-driven scheduling; graphical rendering.

### Why not the alternatives

- **B** — a second runtime for CACAO defeats the "one small kernel" goal; the IR gives BPMN coverage at a fraction of the surface, and we control the security posture.
- **C** — violates the isolation/footprint requirement outright.
- **D** — leaves the originating need unmet.

---

## Affected Layers / Repos

| Layer | Repo | Impact |
|---|---|---|
| (infra) | hub | New function-tier image `templates/runbook-orchestrator-image/`; this ADR; `contracts/runbook-orchestrator.openapi.yaml`; a `docs/contracts.md` Registry row; `docs/runbook-orchestrator.md` |
| middle-core | nickpclarke/middle-core | Hosts the NATS broker (ARC-ADR-001); relates to issue #93 (`workflow-orchestrator` — runbooks/playbooks as middle-core semantic artifacts). The orchestrator can be the *executor* those semantic artifacts compile to |
| (cross-cutting) | event bus | Adds producers (`fleet.runbook.command`, `fleet.runbook.completed`) and consumers (any `fleet.*` subject a runbook's start trigger names) |

---

## Pros and Cons of the Options

### Option A — hand-rolled IR kernel (recommended)

**Pros:** smallest dependency surface (D7); one kernel for both formats; full control of the safe-executor posture (D5); stdlib kernel runs standalone (D2); event layer is optional and degrades (D3); clean function-tier fit (D4).
**Cons:** we own BPMN/CACAO semantic correctness (parallel-join, conditions) rather than inheriting it; v1 deliberately covers a subset (documented limitations: single split/join diamond, condition subset, no durable waits).

### Option B — off-the-shelf BPMN engine
**Pros:** mature BPMN semantics for free.
**Cons:** still needs a separate CACAO runtime; license/second-language cost; no safe-executor posture out of the box.

### Option C — heavyweight SOAR/Zeebe
**Pros:** durable, scalable orchestration.
**Cons:** fails isolation/footprint/supply-chain drivers decisively.

### Option D — status quo
**Pros:** zero cost.
**Cons:** the requirement goes unmet.

---

## Open Questions

1. **Durable long-running waits.** A real `intermediateCatchEvent` (wait days for an external signal) needs resumable state. v1 passes through in one-shot mode and correlates at the dispatcher in serve mode. When durable waits are needed, where does state live — JetStream KV, a small embedded store, or an external one? (Likely punts to a v2.)
2. **Enabling real execution.** What is the opt-in shape for `ssh`/`bash`? Proposed: an env flag **plus** a per-command allowlist **plus** HITL routing (ARC-ADR-006) for anything destructive. Does the executor call out to a separate, even-more-isolated exec sidecar rather than running commands in-process?
3. **CACAO trigger grammar.** CACAO has no native event-trigger field; v1 uses a non-normative `step_extensions.trigger` block on the start step. Should the fleet standardize that extension, or carry triggers in a sidecar manifest?
4. **Condition engine.** Full STIX Patterning (CACAO) and full FEEL (BPMN) are large grammars. v1 supports a comparison subset. Do we adopt a vetted library per language, or grow the subset as runbooks demand?
5. **Relationship to middle-core issue #93.** Should middle-core's semantic runbook/playbook artifacts *compile to* CACAO/BPMN that this engine executes, making the orchestrator the runtime for the ontology layer?
6. **Signature verification.** CACAO supports JWS signing (TLP markings, signed playbooks). When do we verify signatures before executing a playbook from an untrusted source?

---

## Related Decisions

- **[ARC-ADR-023](ARC-ADR-023-container-tiering-strategy.md):** Container tiering — the orchestrator is a function-tier image.
- **[ARC-ADR-022](ARC-ADR-022-event-bus-bridges.md):** Event bus bridges — NATS JetStream + CloudEvents, the trigger transport.
- **[ARC-ADR-001](ARC-ADR-001-hitl-decision-point-pattern.md) / [ARC-ADR-006](ARC-ADR-006-hitl-destructive-ops.md):** HITL decision points / destructive ops — the gate for `manual` steps and (future) real destructive execution.
- **[ARC-ADR-010](ARC-ADR-010-observability-standard.md):** Observability standard — structured NDJSON traces + OTel spans.
- **[ARC-ADR-029](ARC-ADR-029-agentarmy-forge-codegen-container.md):** Forge — the reference function-tier image pattern this one mirrors (image.json + setup + doctor).
- **middle-core #93** — `workflow-orchestrator` runbooks/playbooks as middle-core semantic artifacts.

---

## Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-28 | Claude Code (assisted) | Initial Proposed from interactive design session: research (BPMN 2.0 + CACAO 2.0) → shared-IR kernel design → function-tier image scaffold + safe-orchestrator posture |
