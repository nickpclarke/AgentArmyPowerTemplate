# AgentArmy Image Standard

Every platform container image is a **deliverable**, not a Dockerfile. The standard makes a
fresh container **correct-by-default**, **externally testable with one command**, **contract-first**,
and **deployable** — the same rigor for every image. It generalizes the pattern proven by the
[ArcadeDB image](#reference-instances) so any new image (a service, a service + Postgres, a
multi-service stack) gets it for free.

The standard has three parts:

1. **A declarative manifest — `image.json`** at the image's root, validated against
   [`templates/image-schema.json`](https://github.com/nickpclarke/AgentArmy/blob/main/templates/image-schema.json).
2. **A doctor** — `node tools/agentarmy-doctor.mjs image <dir>` reads the manifest, checks conformance
   + that declared artifacts exist + contracts are declared, and probes each service's healthcheck.
3. **A one-command external test CLI** — `setup.sh` / `setup.ps1`: gen secrets → bring the stack up
   → wait healthy → **run the image's own doctor (prove it from outside)** → emit client wiring →
   `--down`.

## The manifest (`image.json`)

```jsonc
{
  "name": "backend-core-dbos",                 // kebab-case identity
  "kind": "app+db",                            // single | app+db | multi-service
  "base": "python:3.12-slim@sha256:…",         // digest-pinned
  "services": [                                 // the compose units setup.sh brings up
    { "name": "backend-core", "build": ".", "role": "api", "ports": ["8000:8000"],
      "healthcheck": { "http": "/health/ready", "expect": 200 },
      "entrypointModes": ["serve","test","dbos"] },
    { "name": "postgres", "image": "postgres:16", "role": "dbos-system-db",
      "healthcheck": { "cmd": "pg_isready -U dbos" } }     // companion datastore
  ],
  "secrets": [                                  // wiring only, never values; prefer *_FILE
    { "name": "dbos_database_url", "fileEnv": "DBOS_SYSTEM_DATABASE_URL_FILE" }
  ],
  "shims": { "apt": ["libreoffice"], "pip": ["-r requirements.txt"] },   // packages layered on
  "baked": [ { "path": "config/…", "purpose": "correct-by-default posture" } ],
  "setup": { "sh": "setup.sh", "ps1": "setup.ps1" },
  "doctor": { "cmd": "scripts/dbos-doctor.sh",
              "proves": ["readiness","durable-workflow","crash-recovery"] },
  "contract": [                                 // contract-first: the interface this image exposes
    { "service": "backend-core", "type": "openapi", "spec": "contracts/backend-core.openapi.json",
      "registry": "docs/contracts.md", "governingAdr": "ARC-ADR-005" }
  ],
  "deploy": { "target": "aca", "bicep": "deploy/….bicep" }
}
```

### Field reference (load-bearing)

| Field | Required | Purpose |
|---|---|---|
| `name`, `kind`, `base` | ✅ | identity; `single` / `app+db` / `multi-service`; digest-pinned base |
| `services[]` | ✅ | each has `name` + (`image` \| `build`); `ports` (host:container), `healthcheck` (`http`+`expect`, or `cmd`), `role`, `entrypointModes` |
| `doctor.cmd` | ✅ | the external verifier that **proves** the running image (exits non-zero on failure) |
| `secrets[]` | — | `name` + `env`/`fileEnv` (prefer the `*_FILE` form); **never values** |
| `shims` | — | extra `apt`/`pip` packages layered on the base (the "shim onto it" lane) |
| `baked[]` | — | config/posture copied into the image so a fresh container is correct-by-default |
| `setup` | — | the `setup.sh`/`setup.ps1` one-command CLI |
| `contract[]` | —* | the API(s) this image exposes; `type` openapi/asyncapi/graphql/grpc/upstream/prose + `spec` + `registry` + `mock` + `governingAdr`. *Required in spirit for any image that exposes an HTTP interface — the doctor warns if you expose HTTP with no contract.* |
| `deploy` | — | cloud deploy lane (`target` + `bicep`/`workflow`) |
| `volumes` | — | named volumes that must persist **together** (e.g. config + data) |

## Multi-service & Postgres

`kind: app+db` (or `multi-service`) lets one deliverable own its companion datastore. Each peer is a
`services[]` entry — the app `build`s, the datastore pulls an `image` and declares its own
`healthcheck` (`pg_isready` for Postgres). `setup.sh` brings the whole stack up; the doctor probes
each. The DBOS fusion is the reference: `backend-core` + `postgres` (the DBOS system DB) as one unit.

## Shimming packages

`shims.apt` / `shims.pip` declare the extra packages layered onto the base. This is the deliberate,
reviewed lane for "we need LibreOffice for legacy doc extraction" or "pip-install the durable-runtime".
The manifest documents *what* was added and *why* so the image stays auditable instead of drifting.

## Contract-first (interfaces)

An image that exposes an API must declare its interface contract — the fleet
[contract-first rule](contracts.md) applied to images. Bind each interface-exposing service to a
versioned spec registered in [docs/contracts.md](contracts.md) and, where possible, a Postman mock so
consumers can build in parallel. The doctor **warns** if a service exposes HTTP but the manifest
declares no `contract[]`, and **fails/warns** if a declared `openapi`/`asyncapi` spec file is missing.

## The doctor

```bash
node tools/agentarmy-doctor.mjs image templates/arcadedb-image      # validate a hub image
node tools/agentarmy-doctor.mjs image .                             # validate a spoke image (cwd)
node tools/agentarmy-doctor.mjs image . --format json --strict      # CI-friendly, strict
```

Checks: `image.manifest` (parses) · `image.schema` (conforms) · `image.artifacts` (declared files
exist) · `image.contract` (interfaces declared + spec files present) · `image.health.<service>`
(probes each `healthcheck.http` on its host port — skips when the stack is down).

## The external test CLI (`setup.sh` / `setup.ps1`)

Mirrors the ArcadeDB image: gen secrets (random if missing) → bring the stack up → wait for the
healthcheck → **run the image's own `doctor.cmd` to prove it from the outside** → emit client wiring
→ `--down` to tear down. This is what "testing it from the outside with the same rigor" means: a
human (or CI) runs one command and gets a proven-good stack or a clear failure.

## Directory layout

```
<image>/                     # templates/<name>-image/ (hub) or a spoke repo root
  image.json                 # the manifest (validated by the doctor)
  Dockerfile                 # the image (base digest-pinned; shims applied)
  entrypoint.sh              # serve | test | <tool> | <cmd> dispatch
  setup.sh / setup.ps1       # the one-command external test CLI
  README.md                  # bakes / files / secrets / quick-start / verify / ops
  examples/compose.*.yml     # run with file-mounted secrets + volumes
  examples/.secrets/         # gitignored; placeholders only
  scripts/<name>-doctor.sh   # the external verifier (doctor.cmd)
  deploy/                    # ACA bicep + bootstrap + deploy.yml (optional)
```

## Tiering (ARC-ADR-023)

Every image declares which **tier** it belongs to. The tier governs lifecycle expectations, manifest shape, and rollout cadence — it's *the* placement question for a new container.

| Tier | Lifecycle | Has state? | What lives here | `kind` (typical) |
|---|---|---|---|---|
| **`platform`** | Slow (days–months); careful upgrades | Yes | Databases, brokers, ontology stores, persistent caches | `single` (per-service); composed via `templates/local-stack/` |
| **`application`** | Rolling deploys (hours–days) | No | One container per spoke (the spoke's main service) | `single` |
| **`function`** | Fast (minutes); independently rolled out | No (or one-shot) | Small workers, sidecars, ontology jobs, micro-services | `single` |

Declare the tier in the manifest:

```jsonc
{
  "name": "agentarmy-event-bridge",
  "kind": "single",
  "tier": "function",  // ← required (recommended) on new manifests
  ...
}
```

The fleet-heartbeat reads this field to emit a tier-grouped container inventory; tier mismatches (e.g. a `platform`-tier image bundling app code, or an `application`-tier manifest with `kind: "multi-service"` and a database companion) get flagged as drift. See [ARC-ADR-023 — Fleet Container Tiering Strategy](decisions/ARC-ADR-023-container-tiering-strategy.md) for the rule and the anti-patterns.

## Reference instances

| Image | `kind` | `tier` | Doctor proves | Contract |
|---|---|---|---|---|
| [`templates/arcadedb-image`](https://github.com/nickpclarke/AgentArmy/tree/main/templates/arcadedb-image) | `single` | `platform` | readiness, schema-stubs, MCP posture | upstream ArcadeDB API + cockpit prose (to formalize) |
| [`templates/fuseki-ontology-image`](https://github.com/nickpclarke/AgentArmy/tree/main/templates/fuseki-ontology-image) | `single` | `platform` | readiness, SHACL sieve, KG emit | SPARQL + SHACL prose |
| [`templates/event-bridge-image`](https://github.com/nickpclarke/AgentArmy/tree/main/templates/event-bridge-image) | `single` | `function` | readiness, HMAC-rejects-bad-sig, events-flowing | webhook-receiver OpenAPI + CloudEvents prose |
| [`templates/local-stack`](https://github.com/nickpclarke/AgentArmy/tree/main/templates/local-stack) | _(compose only)_ | `platform` umbrella | 5/5 services healthy | composes the three platform images + Postgres + NATS |
| [backend-core/image.json](https://github.com/nickpclarke/backend-core/blob/main/image.json) | `single` | `application` | readiness, ArcadeDB-reachable, Postgres-reachable | backend-core OpenAPI (`ARC-ADR-005`) |
| [backend-core/llm-gateway/image.json](https://github.com/nickpclarke/backend-core/blob/main/llm-gateway/image.json) | `single` | `function` | readiness, `/v1/models` wired, unauth-rejected | LLM gateway OpenAPI (`ARC-ADR-021`) |

## Adding a new image

1. Copy the layout above; write `image.json` (start from a reference instance).
2. Digest-pin `base`; declare `services`, `secrets` (`*_FILE`), `shims`, `healthcheck`s.
3. Write `scripts/<name>-doctor.sh` that **proves** the running image and exits non-zero on failure;
   point `doctor.cmd` at it.
4. Declare `contract[]` for every interface and register it in [docs/contracts.md](contracts.md).
5. Validate: `node tools/agentarmy-doctor.mjs image <dir>` is green.
6. Wire `setup.sh`/`setup.ps1`; confirm one command brings it up and the doctor passes.

## Related

- [Inter-Layer Contracts](contracts.md) — the registry every image's `contract[]` binds to.
- [Fleet Heartbeat](fleet-heartbeat.md) — audits contracts across the fleet.
- [Azure Container Apps Dev Deploy](azure-container-apps-dev.md) — the spoke build/push lane.
