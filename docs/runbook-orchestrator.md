# Automated Runbook Orchestrator

A streamlined, **isolated** Function-tier helper ([ARC-ADR-023](decisions/ARC-ADR-023-container-tiering-strategy.md)) that executes automated runbooks in two open standards and responds to event-bus triggers. Governing decision: [ARC-ADR-031](decisions/ARC-ADR-031-automated-runbook-orchestration.md). Image: [`templates/runbook-orchestrator-image/`](../templates/runbook-orchestrator-image/).

- **BPMN 2.0 XML** — OMG business-process orchestration
- **OASIS CACAO 2.0 JSON** — security playbooks (SOAR)

## Why one engine for two formats

BPMN and CACAO describe the same thing — an ordered, branching, sometimes-parallel set of steps — with different vocabularies and different strengths (BPMN has event-wait + a diagram; CACAO has executor/target binding + command objects). Rather than convert one to the other (lossy, per [Zych et al. 2023](https://arxiv.org/abs/2305.18928)), **both parsers emit one intermediate representation** — an annotated directed graph — and **one execution kernel** runs it. Only the parsers and the condition evaluators are format-specific.

```
 BPMN XML  ──▶ bpmn_parser  ──┐
                              ├──▶  IR (Graph of Nodes) ──▶ Engine ──▶ trace + events
 CACAO JSON ─▶ cacao_parser ──┘                              │
                                                     SafeExecutor (observe / gate / dry-run)
```

## Format → IR mapping

| IR `NodeKind` | BPMN 2.0 | OASIS CACAO 2.0 |
|---|---|---|
| `START` | `startEvent` (+ message/timer/signal def) | `start` step (`workflow_start`) |
| `END` | `endEvent` | `end` step |
| `ACTION` | `serviceTask` / `scriptTask` / `userTask` / `manualTask` / `sendTask` / `task` | `action` step (`commands` + `agent` + `targets`) |
| `DECISION` | `exclusiveGateway` (+ `conditionExpression`, `default`) | `if-condition` / `while-condition` / `switch-condition` |
| `PARALLEL` | `parallelGateway` (split paired to a join gateway) | `parallel` step (`next_steps`, implicit join at `on_completion`) |
| `CATCH_EVENT` | `intermediateCatchEvent` / `receiveTask` | *(no native equivalent — modeled via step `delay` + serve-mode correlation)* |
| `CALL` | `callActivity` | `playbook-action` step (`playbook_id`) |

Routing is normalized: BPMN `sequenceFlow`/`default` and CACAO `on_completion` / `on_success` / `on_failure` / `on_true` / `on_false` / `cases` / `next_steps` all collapse onto Node routing fields, so the kernel never re-reads the source format.

### Condition languages (never cross-translated, never `eval()`)

| Source | Language | v1 support |
|---|---|---|
| BPMN `conditionExpression` | JUEL/FEEL (`${severity == 'HIGH'}`) | `==`, `!=`, `>`, `<`, `>=`, `<=` against a context variable |
| CACAO `condition` | STIX Patterning (`__severity__:value = 'high'`) | same comparison subset; the head token is read as the context variable |

## Execution model

Token traversal of the IR graph with a global step budget (guards cycles / runaway `while`):

- **ACTION** → run commands via the executor; route by outcome (`on_success`/`on_failure`) or `on_completion`.
- **DECISION** → `if`/`while` evaluate a condition; `switch` reads a variable against `cases` (+ `default`); BPMN `exclusive` evaluates branch conditions in order, else the `default` flow.
- **PARALLEL** → fan out to branches; each branch runs until it reaches the join (BPMN) / the convergence step (CACAO) or an `END`; then continue once. (v1 handles the common single split/join diamond; multi-join graphs are a documented limitation.)
- **CATCH_EVENT** → in one-shot `run` it records the wait and passes through; serve mode does real correlation upstream.
- **CALL** → records the sub-playbook invocation and continues.

Every step emits a structured NDJSON trace record (feeds `tools/tail.mjs`; OTel spans are a roadmap item per [ARC-ADR-010](decisions/ARC-ADR-010-observability-standard.md)).

## Safe-orchestrator posture (the security stance)

These are security playbooks, so the default executor never blindly detonates commands:

| CACAO/BPMN command type | v1 behavior |
|---|---|
| `manual` (BPMN `userTask`/`manualTask`) | **HITL ack required** — recorded, does not auto-proceed in production wiring (ARC-ADR-006) |
| `http-api`, `emit-event` (BPMN `serviceTask`/`sendTask`) | publish an observable **CloudEvent** to `fleet.runbook.command` |
| `ssh`, `bash`, `powershell`, `openc2-http`, `sigma`, `yara`, … | **dry-run** — log what *would* run; real execution is deferred + opt-in |

Real `ssh`/`bash` execution is intentionally **not** implemented in v1. Enabling it later requires an explicit flag **plus** a per-command allowlist **plus** HITL for destructive ops (ARC-ADR-031 Open Question 2).

## Triggers — three sources, all derived from the files

1. **Manual / CLI** — `run <file>`: execute immediately, zero network.
2. **Event** — serve mode derives a `fleet.*` subject from each runbook's start trigger (BPMN `messageStartEvent`; CACAO start `step_extensions.trigger`), subscribes via JetStream, and runs the runbook when a matching CloudEvent arrives.
3. **Timer** — BPMN `timerStartEvent` / CACAO step `delay` (parsed into the IR; scheduling is a roadmap item).

## Usage

### Standalone (isolated, file-only)

```sh
python scripts/runbook_engine.py validate runbooks/incident-response.bpmn
python scripts/runbook_engine.py run      runbooks/block-mac.cacao.json
python scripts/runbook_engine.py run      runbooks/incident-response.bpmn ctx.json
```

### Serve mode (responds to events)

```sh
./setup.sh   # nats + orchestrator + doctor
```

| Endpoint | Purpose |
|---|---|
| `GET /healthz` | liveness + indexed count + subscribed subjects |
| `GET /runbooks` | the index (id, format, trigger, validity) |
| `POST /runbooks/{id}/trigger` | run now; JSON body = context |

Control API contract: [`contracts/runbook-orchestrator.openapi.yaml`](../contracts/runbook-orchestrator.openapi.yaml).

## Bundled fixtures

| File | Format | Exercises |
|---|---|---|
| `runbooks/block-mac.cacao.json` | CACAO | canonical OASIS example — start → ssh action (dry-run) → end |
| `runbooks/phishing-response.cacao.json` | CACAO | `parallel` + `if-condition` + `manual` (HITL) + `http-api` (emit) + event trigger |
| `runbooks/incident-response.bpmn` | BPMN | `messageStartEvent` + `serviceTask` + `exclusiveGateway` (HIGH/default) |

## Doctor

`scripts/runbook-doctor.sh` proves the image from outside: readiness with trigger subjects subscribed → every runbook valid → **a CloudEvent on `fleet.siem.phishing` makes the phishing playbook run and emit `fleet.runbook.completed`** → a malformed file fails `validate`.

## v1 limitations / roadmap

- Single split/join parallel diamond (no arbitrary multi-join graphs yet).
- Condition support is a comparison subset of FEEL/STIX, not the full grammars.
- `intermediateCatchEvent` passes through in one-shot mode; durable, resumable long waits are deferred (ARC-ADR-031 OQ1).
- No real `ssh`/`bash` execution; no timer scheduling; no JWS signature verification of playbooks — all tracked as ADR-031 open questions.
