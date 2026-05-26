# `templates/local-stack` — the AgentArmy fleet data platform, locally

One `docker compose` that brings up every database / broker / ontology
system the fleet relies on:

| Service       | Role                                                  | Port(s)              |
|---------------|-------------------------------------------------------|----------------------|
| ArcadeDB      | Graph DB — pin store, business object graph           | 2480                 |
| Postgres      | DBOS durable-execution metadata + app relational data | 5432                 |
| NATS JetStream| Fleet event broker — durable pub/sub                  | 4222 (cli) / 8222 (mon) |
| event-bridge  | HTTP webhook → HMAC verify → CloudEvents → JetStream  | 8080                 |
| Fuseki + Jena | SPARQL endpoint + SHACL strict-sieve validator        | 3030                 |

## Quick start

```bash
cd templates/local-stack
./setup.sh                 # generate secrets, build, up, doctor
# ...work locally; point your spoke at the ports above...
./setup.sh --down          # stop containers, keep volumes
./setup.sh --wipe          # stop AND drop volumes (destroys local data)
```

Windows: `.\setup.ps1` (mirror), `.\setup.ps1 -Down`, `.\setup.ps1 -Wipe`.

Health probe alone (stack already up):

```bash
./local-stack-doctor.sh
```

## What this stack is NOT

It does **not** include the spoke applications (`frontend-core`,
`backend-core`, `middle-core`). Run those separately from their own repos
and point them at the ports above:

```bash
# backend-core/.env
ARCADEDB_URL=http://localhost:2480
POSTGRES_URL=postgresql://dbos:<secret>@localhost:5432/dbos_system
NATS_URL=nats://localhost:4222
```

The split is intentional: **data systems have slower lifecycles than app
code**. You want to rebuild your Python container every minute without
losing your Postgres state.

## Repo organization (the "where does this live" map)

The fleet has **4 repos** — that's enough, and we don't need a 5th.

```
AgentArmy (hub)
├── templates/
│   ├── arcadedb-image/         ← prebuilt-by-us platform image
│   ├── fuseki-ontology-image/  ← prebuilt-by-us platform image
│   ├── event-bridge-image/     ← prebuilt-by-us platform image
│   ├── local-stack/            ← THIS — umbrella stack of the above
│   ├── gcp-cloud-run/          ← deployment scaffold (IaC + workflow)
│   ├── azure-container-apps-dev/ ← deployment scaffold
│   └── aca-github-runner/      ← deployment scaffold
├── .claude/agents/             ← shared agents, synced to spokes
├── .github/workflows/          ← shared CI workflows, synced to spokes
└── docs/                       ← governance + ADRs

frontend-core   ← Next.js BFF + UI                  (its own image)
backend-core    ← FastAPI + DBOS + LLM gateway     (its own image.json)
middle-core     ← Rust GraphEngine + model factory (its own image)
```

The `templates/` dir holds **two kinds** of things:

1. **Platform images** (`*-image/`, `local-stack/`) — products we build and
   ship; data systems the fleet runs on.
2. **Deployment scaffolds** (`gcp-cloud-run/`, `azure-container-apps-dev/`,
   `aca-github-runner/`) — IaC + workflow snippets a spoke copies and
   adapts.

> **"What about DBOS — shouldn't 'non-core systems we built' live in their
> own repo?"** DBOS isn't a *system*, it's a Python *library* that
> backend-core imports. The system is Postgres (stock image, here in
> `local-stack`) — that's where DBOS persists workflow state. No separate
> "DBOS repo" needed; the only place that matters is wherever the library
> is imported (backend-core), and the only piece of infrastructure we
> operate is the Postgres it talks to.

## Why each piece exists

- **ArcadeDB** is the graph backend the runtime objects materialise into —
  pinning, hyperedges, time-indexed snapshots ([hub #130 PIN-E](https://github.com/nickpclarke/AgentArmy/issues/130)).
- **Postgres** is required by DBOS and gives backend-core relational
  storage too (low effort, high leverage).
- **NATS JetStream** is the fleet's pub/sub spine
  ([ARC-ADR-022](../../docs/decisions/ARC-ADR-022-event-bus-bridges.md)).
  Cheap to run, gives every spoke a place to emit/consume events.
- **event-bridge** turns external HTTP webhooks (GitHub, alerting) into
  CloudEvents on the bus — same envelope as everything else.
- **Fuseki** is the strict-typing front door for ontology data:
  SHACL-conform or get rejected. Powers the ontology-driven model
  generation pipeline.

## Secrets

`setup.sh` / `setup.ps1` generate dev-only secrets into `.secrets/*.txt`
on first run (gitignored). These are **not** rotated and **not** suitable
for any environment beyond your laptop. For deployed environments, point
each `*_FILE` environment variable at a real secret manager (Azure Key
Vault, GCP Secret Manager) — see
[`docs/arcadedb-secret-hardening.md`](../../docs/arcadedb-secret-hardening.md).

## Image Standard

Each `templates/*-image/` directory follows the AgentArmy
[Image Standard](../../docs/image-standard.md): declarative `image.json`
manifest, JSON schema validation via `tools/agentarmy-doctor.mjs`, secrets
via `*_FILE`, non-root user, healthcheck endpoint, doctor script. This
stack composes those building blocks but doesn't re-derive them — each
image is owned by its own directory.
