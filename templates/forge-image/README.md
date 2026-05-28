# agentarmy-forge

> ⚠️ **RELOCATED — active source now lives at [`nickpclarke/agentarmy-forge`](https://github.com/nickpclarke/agentarmy-forge).** Per **ARC-ADR-029 Option 1b**, the forge moved to its own repo so the generation loop iterates in isolation. **This directory is a frozen mirror** kept only so the hub's image-doctor + image-security-scan keep passing; the hub retains the ADR + container-tiering governance (this `image.json`). Do **not** edit the source here — open PRs against the standalone repo. Full removal of this mirror (and the matching `local-docker-smoke.yml` / `image-security-scan.yml` matrix entries) is tracked in [#304](https://github.com/nickpclarke/AgentArmy/issues/304) P2.

**Status:** v0 + v1 + v2 implemented. **Governing decision:** [ARC-ADR-029 — agentarmy-forge: Extract Code Generator into a Function-Tier Container with Ontology-Driven Multi-Target Emit](../../docs/decisions/ARC-ADR-029-agentarmy-forge-codegen-container.md).

Closes hub issue #294 (forge v0) and supersedes the scaffold-only [PR #292](../../docs/decisions/ARC-ADR-029-agentarmy-forge-codegen-container.md).

---

## What this image is

The fleet's code generator. Lifts middle-core's `modelgen` role into its own function-tier container, expands its input model to consume RDF / OWL ontologies (from HTTP, file, or blob), and emits source for the three application-tier spokes.

| Source (input) | Target (output) |
|---|---|
| `GET /ontology/snapshot` on backend-core (HTTP + conditional `If-None-Match`) | `*.g.cs` for middle-core — records + `I{ObjectType}Projection` interfaces |
| Local file (`.ttl` / `.jsonld` / `.nt` / `.yaml`) | `*.g.ts` for frontend-core — interfaces + Zod schemas |
| Azure Blob URI (managed-identity auth) | `*.g.py` for backend-core — Pydantic v2 models |

Delivery: `forge generate --consumer-repo owner/repo` opens a `chore(generated): forge sync — ontology@<version>` Pull Request against the consumer spoke's `main` branch with auto-merge enabled. Source-only — forge does NOT build binaries, push artifacts, or deploy.

## Quick start

```bash
cd templates/forge-image
./setup.sh
```

This builds the image (~3-5 min cold; multi-toolchain image), brings up the container on port 8086, waits for `/livez`, and execs the doctor inside the container.

Expected output: **7 pass, 0 fail** (one of those is SKIP-with-PASS for the Azure Blob source — see Doctor section).

```bash
./setup.sh --down   # tear down + drop the work-cache volume
```

## Endpoints

| Endpoint | Auth-free? | Returns | Use case |
|---|:---:|---|---|
| `/livez` | yes | 200 always | LB liveness probe |
| `/readyz` | yes | 200 / 503 + Problem Details | LB readiness gate |
| `/healthz` | yes | 200 + version + config snapshot | Heartbeat + dashboards |
| `/webhook` | **HMAC required** | 200 → generate cycle queued | backend-core ontology-change trigger |
| `/generate` | open in v1 | 200 + generation result | on-demand from CLI / MCP control plane |

## CLI

The same code path as the HTTP server. Invoked via `MODE=generate`:

```bash
# generate C# from a local YAML file
docker run --rm -v "$PWD/work:/work" -e MODE=generate agentarmy-forge:local \
  -- --source file:///work/model.yaml --target csharp --out /work/out

# generate all three targets from backend-core HTTP
docker run --rm -v "$PWD/work:/work" -e MODE=generate agentarmy-forge:local \
  -- --source http://backend-core:8000/ontology/snapshot --target all --out /work/out

# generate + open a PR against a real consumer spoke
docker run --rm -v "$PWD/work:/work" -e MODE=generate -e GITHUB_TOKEN=$TOKEN \
  agentarmy-forge:local \
  -- --source http://backend-core:8000/ontology/snapshot --target csharp \
     --out /work/out --consumer-repo nickpclarke/middle-core

# validate an RDF file without emitting
docker run --rm -v "$PWD/work:/work" -e MODE=ingest-validate agentarmy-forge:local \
  -- --source file:///work/model.ttl
```

## Webhook

Backend-core POSTs the following payload to `/webhook` whenever the ontology changes (per ARC-ADR-029 D8):

```json
{
  "event": "ontology.changed",
  "version": "2026-05-27T13:00:00Z",
  "etag": "W/\"abc123\"",
  "snapshot_url": "http://backend-core:8000/ontology/snapshot"
}
```

Signature: `X-Hub-Signature-256: sha256=<hex>` over the raw request body using `WEBHOOK_HMAC_SECRET`. Verified constant-time via `hmac.compare_digest` (CWE-208 protection — primitive lifted verbatim from `templates/hmac-verify-image/scripts/verify-sidecar.py`). If `snapshot_url` is absent, forge falls back to `FORGE_DEFAULT_UPSTREAM`.

Test it locally:

```bash
SECRET='dev-secret-rotate-me'
BODY='{"event":"ontology.changed","version":"1.0.0","snapshot_url":"http://host.docker.internal:8765/reference.ttl"}'
SIG="sha256=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')"
curl -sS -H "Content-Type: application/json" -H "X-Hub-Signature-256: $SIG" \
  -d "$BODY" http://localhost:8086/webhook
```

## Input formats

### YAML (back-compat for the middle-core model)

```yaml
version: "1.0.0"
namespace: "AgentArmy.MiddleCore.Contracts"
objectTypes:
  - name: Document
    annotations:
      label: "Knowledge document"
    fields:
      - { name: id, type: uuid }
      - { name: title, type: string }
      - { name: body, type: string, optional: true }
      - { name: createdAt, type: datetime }
    relations:
      - { name: author, target: User, cardinality: one, inverse: documents }
```

Supported scalars: `string | int | long | float | bool | datetime | uuid | json`.
Cardinality: `one | many`.

### RDF / OWL (Turtle, JSON-LD, N-Triples)

Forge accepts a **deliberately constrained OWL-shaped vocabulary** — not arbitrary OWL. Full spec is in `scripts/forge/parsers/rdf_parser.py` docstring. The bones:

```turtle
@prefix owl:   <http://www.w3.org/2002/07/owl#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
@prefix forge: <http://agentarmy.dev/forge#> .
@prefix ex:    <http://example.org/onto#> .

[] a forge:Model ;
   forge:version "1.0.0" ;
   forge:namespace "AgentArmy.MiddleCore.Contracts" .

ex:Document a owl:Class ;
    rdfs:label "Knowledge document" ;
    forge:fieldOrder ( "id" "title" "body" "createdAt" ) ;
    forge:relationOrder ( "author" ) .

ex:Document__title a owl:DatatypeProperty ;
    rdfs:domain ex:Document ;
    rdfs:range  xsd:string .

ex:Document__author a owl:ObjectProperty ;
    rdfs:domain ex:Document ;
    rdfs:range  ex:User ;
    forge:cardinality "one" ;
    forge:inverse "documents" .
```

XSD → forge primitive map: `xsd:string → string`, `xsd:integer → int`, `xsd:long → long`, `xsd:float|double|decimal → float`, `xsd:boolean → bool`, `xsd:dateTime|date → datetime`, `forge:uuid → uuid`, `forge:json → json`. Anything outside this vocabulary is silently ignored — forge is not an OWL reasoner.

Property URI convention: use `ClassName__fieldName` to disambiguate when two ObjectTypes share a field name. The parser strips through the last `__` so the IR sees `fieldName`.

## Configuration

| Env var | Default | Meaning |
|---|---|---|
| `MODE` | `serve` | `serve` (FastAPI on 8086) / `generate` (CLI) / `ingest-validate` / `doctor` |
| `FORGE_PORT` | `8086` | Listen port for `MODE=serve` |
| `FORGE_OUT_DIR` | `/work/out` | Default output dir for `/generate` |
| `FORGE_DEFAULT_UPSTREAM` | _(unset)_ | Fallback ontology snapshot URL when the webhook payload omits it |
| `WEBHOOK_HMAC_SECRET` | _(unset)_ | HMAC secret for `/webhook` verification — required or webhook 500s |
| `WEBHOOK_SIGNATURE_HEADER` | `X-Hub-Signature-256` | Header name carrying the signature |
| `WEBHOOK_SIGNATURE_PREFIX` | `sha256=` | Algo prefix on the signature |
| `FORGE_HTTP_BEARER` | _(unset)_ | Optional bearer auth for HTTP source fetches |
| `FORGE_DRY_RUN` | _(unset)_ | When `1`, `pr_opener` logs the would-be `gh` call instead of executing |
| `GITHUB_TOKEN` | _(unset)_ | Required when `pr_opener` opens a real PR (not local: mode) |
| `AZURE_STORAGE_CONNECTION_STRING` | _(unset)_ | Auth for blob_source; takes precedence over managed identity |
| `LOG_LEVEL` | `INFO` | Standard Python log level |

## Doctor

The doctor (`scripts/forge-doctor.sh`) proves the seven checks listed in `image.json`'s `doctor.proves`. It runs inside the container against the live FastAPI process.

| # | Check | How it's proven |
|---|---|---|
| 1 | `readiness` | `/healthz` returns 200 within 15s |
| 2 | `ontology-fetch-http` | Doctor starts a `python -m http.server` on `127.0.0.1:8765` serving `reference.ttl`; forge fetches via `POST /generate` with an `http://` source; response IR contains `User` + `Document` |
| 3 | `ontology-fetch-file` | `POST /generate` with `file://` source pointing at `reference.model.yaml`; response IR contains `User` + `Document` |
| 4 | `ontology-fetch-blob` | **SKIP-with-PASS** when `SKIP_AZURE=1` (default in CI / sandboxed runs). The `blob_source._parse_uri` helper is unit-checked even on skip. Set `SKIP_AZURE=0 BLOB_URI=azureblob://acct/container/key` to require a real fetch. |
| 5 | `v0-csharp-emit-byte-identical` | Generate C# from `reference.model.yaml` staged at `/work/reference.model.yaml`; byte-compare `DataPlatformContracts.g.cs` against the checked-in `tests/golden/reference.g.cs` |
| 6 | `smoke-compile-passes` | `python -c "import data_platform_contracts"` via `importlib` on the generated Python module; `tsc --noEmit` on the generated TS (TS toolchain baked in the image). C# `dotnet build` is **SKIP-with-PASS** by default — set `SKIP_DOTNET=0` and layer a .NET SDK image to require it. |
| 7 | `pr-opener-opens-against-dummy` | Doctor inits a bare local git repo (`<workdir>/dummy-consumer.git`), seeds it with a `main` commit, then runs `POST /generate` with `consumer_repo: local:<bare>`; verifies the `forge/doctor-test` branch lands in the bare repo with `DataPlatformContracts.g.cs` in the tree |

Sample doctor output (verified locally):

```
agentarmy-forge doctor
  base:       http://localhost:8086
  golden:     /opt/agentarmy/tests/golden
  workdir:    /tmp/forge-doctor.XXXXXX
  SKIP_AZURE: 1
  SKIP_DOTNET: 1

[1/7] readiness — /healthz 200
  PASS /healthz 200
[2/7] ontology-fetch-http — serve reference.ttl over http; forge fetches + parses
  PASS http source parsed; IR contains User + Document
[3/7] ontology-fetch-file — file:// URI parses to IR
  PASS file source parsed; IR contains User + Document
[4/7] ontology-fetch-blob — Azure Blob source
  SKIP SKIP_AZURE=1 — no Azure creds in sandbox; module imports + URI parser unit-tested only
         (blob_source._parse_uri unit check: ok)
[5/7] v0-csharp-emit-byte-identical — generated C# matches frozen golden
  PASS generated DataPlatformContracts.g.cs == golden reference.g.cs (byte-identical)
[6/7] smoke-compile — TS (tsc --noEmit) + Python (import probe)
  PASS Python emit imports cleanly; User + Document present
  PASS tsc --noEmit clean on generated TS
  SKIP C# smoke-compile (dotnet not in base image; set SKIP_DOTNET=0 + dotnet on PATH to enable)
[7/7] pr-opener — initialise bare local repo, run pr_opener, verify branch lands
  PASS pr_opener pushed forge/doctor-test to bare repo with generated file

summary: 7 pass, 0 fail
```

## Why function-tier

Per [ARC-ADR-023](../../docs/decisions/ARC-ADR-023-container-tiering-strategy.md)'s split-rule discipline, forge clears the bar on all four criteria:

- **Different scale curve** — generation is bursty CPU/memory; consumer runtimes are steady-state web.
- **Different release cadence** — generator improvements ship independently of any spoke's runtime.
- **Different toolchain** — python + nodejs in one image; baking that into a consumer spoke would inflate its blast radius.
- **Different blast radius** — a forge bug at worst opens a bad PR (caught by consumer CI); a runtime bug breaks live traffic.

## Phased rollout

Tracked in the hub Epic linked from ARC-ADR-029.

| Phase | Scope | Status |
|---|---|---|
| **v0** | Lift-and-shift middle-core `modelgen` into the new container. YAML in, C# out. Doctor proves byte-identical output. | **Done** (this PR) |
| **v1** | HTTP / file / blob input adapters; FastAPI webhook trigger (HMAC); CLI; ingest-validate mode. | **Done** (this PR) |
| **v2** | TypeScript + Python emitters; multi-toolchain image with TS smoke-compile. | **Done** (this PR) |
| **v3** *(deferred)* | Binary builds / artifact publishing — **only if** cross-language version coherence requires it. Default = don't go here. | Deferred per ADR |

## See also

- [ARC-ADR-029](../../docs/decisions/ARC-ADR-029-agentarmy-forge-codegen-container.md) — the architectural decision
- [ARC-ADR-023](../../docs/decisions/ARC-ADR-023-container-tiering-strategy.md) — container tiering rationale
- [ARC-ADR-016](../../docs/decisions/ARC-ADR-016-ontology-representation-reification-hyperedges.md) — what forge consumes
- [ARC-ADR-019](../../docs/decisions/ARC-ADR-019-ontology-reasoning-layer.md) — Fuseki + gUFO RDF store this reads from
- [RT7 MCR-F4](../../docs/release-trains/RT7-middle-core-runtime.md) — the existing generator forge v0 lifts unchanged
- [templates/local-embedder-image/](../local-embedder-image/) + [templates/jwt-introspect-image/](../jwt-introspect-image/) + [templates/hmac-verify-image/](../hmac-verify-image/) — reference function-tier siblings whose patterns forge follows
