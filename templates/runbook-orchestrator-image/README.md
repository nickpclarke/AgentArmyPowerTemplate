# agentarmy-runbook-orchestrator

A **Function-tier** ([ARC-ADR-023](../../docs/decisions/ARC-ADR-023-container-tiering-strategy.md)) helper that runs **automated runbooks** in two standard formats and responds to event-bus triggers:

- **BPMN 2.0 XML** — process orchestration (`<process>` with events, tasks, gateways, flows)
- **OASIS CACAO 2.0 JSON** — security playbooks (`spec_version: "cacao-2.0"`)

Both formats are parsed into **one intermediate representation** and run by **one execution kernel**, so the engine stays small. It is **isolated by design**: the kernel depends only on the runbook files (Python stdlib + `defusedxml`). Event handling is an optional layer on the fleet's NATS JetStream + CloudEvents bus ([ARC-ADR-022](../../docs/decisions/ARC-ADR-022-event-bus-bridges.md)). Governing decision: [ARC-ADR-031](../../docs/decisions/ARC-ADR-031-automated-runbook-orchestration.md). Full design: [docs/runbook-orchestrator.md](../../docs/runbook-orchestrator.md).

## Safe-orchestrator posture

These are *security* playbooks, so the engine never blindly executes remote commands:

| Command | Behavior |
|---|---|
| `manual` | Recorded as **HITL ack required** (does not auto-proceed in production wiring) |
| `http-api`, `emit-event` | Publishes an observable **CloudEvent** to NATS |
| `ssh`, `bash`, `powershell`, `openc2-http`, … | **Dry-run** — logs what *would* run; real exec is deferred + opt-in |

## Quick start

```sh
./setup.sh                 # build + up (nats + orchestrator) + doctor
```

### Standalone (no network, file only)

```sh
python scripts/runbook_engine.py validate runbooks/incident-response.bpmn
python scripts/runbook_engine.py run      runbooks/block-mac.cacao.json
echo '{"severity":"HIGH"}' > ctx.json
python scripts/runbook_engine.py run runbooks/incident-response.bpmn ctx.json
```

### Serve mode (responds to triggers)

```
serve (default)   uvicorn control API + JetStream trigger dispatcher
```

| Endpoint | Purpose |
|---|---|
| `GET /healthz` | liveness + indexed runbooks + subscribed trigger subjects |
| `GET /runbooks` | list indexed runbooks (id, format, trigger, validity) |
| `POST /runbooks/{id}/trigger` | run a runbook now; JSON body = execution context |

On startup the helper indexes `RUNBOOK_DIR`, derives a `fleet.*` subject from each runbook's start trigger (BPMN `messageStartEvent` / CACAO `step_extensions.trigger`), and runs the matching runbook when a CloudEvent arrives. With no reachable NATS it degrades to control-API-only.

## Files

```
scripts/
  ir.py             shared intermediate representation
  bpmn_parser.py    BPMN 2.0 XML  -> IR   (defusedxml)
  cacao_parser.py   CACAO 2.0 JSON -> IR
  validators.py     structural pre-flight checks (both formats)
  runbook_engine.py execution kernel + SafeExecutor + CLI
  triggers.py       runbook directory index + trigger derivation
  server.py         serve mode: control API + event dispatcher
  runbook-doctor.sh external proof (readiness, validity, event-fires, rejects-invalid)
runbooks/           bundled fixtures (drop your own files here)
```

## Doctor

`scripts/runbook-doctor.sh` proves the image from outside: readiness with trigger subjects subscribed → every runbook valid → **a CloudEvent on `fleet.siem.phishing` makes the phishing playbook run and emit `fleet.runbook.completed`** → a malformed file fails `validate`.
