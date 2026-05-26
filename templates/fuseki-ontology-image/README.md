# Fuseki super-image — the AgentArmy ontology pipeline

An Apache Jena Fuseki 5 super-image built from **`eclipse-temurin:21-jre`** +
the official **Apache Jena Fuseki** and **Jena** tarballs (no third-party image
dependency), with the ontology toolchain baked on top: **Jena CLI** (`shacl`,
`sparql`, `riot`, `tdb2.tdbloader`), **Python + pyshacl + rdflib**, and **ROBOT**
(OBO workflow). One image, one TDB2 store, one persistent SPARQL endpoint, one
strict ingest sieve.

It implements the **AgentArmy ontology pipeline**:

> **In**: only strictly-typed ontological data (SHACL-validated). **Out**:
> knowledge graphs + structures (SPARQL CONSTRUCT/SELECT).

Conforms to the [AgentArmy Image Standard](../../docs/image-standard.md) —
manifest at [`image.json`](image.json). Realizes [ARC-ADR-019](../../docs/decisions/ARC-ADR-019-ontology-reasoning-layer.md).

## What it bakes in

| Concern | How |
|---|---|
| SPARQL 1.1 + GSP | Apache Jena Fuseki 5.x (digest-pinnable via `ARG JENA_VERSION`). |
| TDB2 store | `--tdb2 --loc=/fuseki/databases/${DS_NAME:-knowledge}` (persistent). |
| Jena CLI tools | `apache-jena` tarball extracted at `/opt/jena/bin` (matches server version): `shacl`, `sparql`, `riot`, `tdb2.tdbloader`. |
| Python ontology toolkit | `pyshacl` (second SHACL impl) + `rdflib`. |
| OBO workflow | `robot` (JAR + launcher on PATH) for reason/reduce/repair/convert/validate/diff. |
| Healthcheck | Polls `GET /$/ping`. |
| Non-root | Switches back to the base image's `fuseki` user before `ENTRYPOINT` (CWE-269). |

## Entrypoint dispatch

One image, several interfaces (`entrypoint.sh`):

```
server  (default)     fuseki-server, TDB2 /knowledge dataset
sieve   <data> [shapes] [ds]   strict SHACL gate → load on pass
emit    <sparql> [accept] [ds] SPARQL CONSTRUCT/SELECT result
shacl|sparql|riot|tdb2.tdbloader|robot|pyshacl <args>   pass-through CLIs
<any command>         runs as-is
```

## Quick start (one command)

```bash
./setup.sh            # Linux / macOS / WSL / Git-Bash
.\setup.ps1           # Windows PowerShell / pwsh  (needs sh on PATH)
```

It generates the admin secret, builds + starts the container, waits for
readiness, and **runs the doctor** — proving the sieve accepts conformant data,
**rejects** non-conformant data, and that SPARQL CONSTRUCT emits the result.
Tear down: `./setup.sh --down`.

## The sieve (strict ingest)

`scripts/sieve.sh <data.ttl> [shapes.ttl] [dataset]`:

1. `shacl validate --shapes <shapes> --data <data>`
2. If the report has `sh:conforms true` → POST the data to `GSP /<dataset>/data?default`.
3. Otherwise → **reject** with the full conformance report on stderr, exit non-zero.

```bash
docker compose exec -T fuseki sh /opt/agentarmy/scripts/sieve.sh \
  /opt/agentarmy/fixtures/good.ttl \
  /opt/agentarmy/fixtures/shapes.ttl
# ACCEPTED — loaded.

docker compose exec -T fuseki sh /opt/agentarmy/scripts/sieve.sh \
  /opt/agentarmy/fixtures/bad.ttl \
  /opt/agentarmy/fixtures/shapes.ttl
# REJECTED — sh:conforms false; <report>
```

Bring your own shapes — mount a directory at `/shapes` (compose has the slot).

## Emission

`scripts/emit.sh '<sparql>' [accept] [dataset]` — runs against the SPARQL
endpoint and streams the result. JSON-LD is the default (for `CONSTRUCT`); use
`application/sparql-results+json` for `SELECT`/`ASK`.

```bash
docker compose exec -T fuseki sh /opt/agentarmy/scripts/emit.sh \
  'CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o } LIMIT 50' \
  application/ld+json
```

## Verify (the doctor)

```bash
sh scripts/fuseki-doctor.sh
```

Asserts: **readiness · sieve-accepts-conformant · sieve-rejects-violating · construct-emits.**
Exits non-zero on any failure. Run by `setup.sh` automatically.

## Volumes

| Mount | Why |
|---|---|
| `fuseki-data → /fuseki/databases` | TDB2 store (persistent). |
| `shapes → /shapes` (optional, ro) | Bring-your-own SHACL shape graphs. |
| `ontologies → /ontologies` (optional, ro) | Bring-your-own foundational ontologies (UFO / gUFO / BFO 2020 / IAO / RO …). Fetch as a one-off (`curl … -o /ontologies/…`) or mount a vendored set. |

## Files

| File | Purpose |
|---|---|
| `image.json` | The Image Standard manifest (validated by `agentarmy-doctor image .`). |
| `Dockerfile` | The thin derived image (base + Jena CLI + Python toolkit + ROBOT). |
| `entrypoint.sh` | `server` (default) `| sieve | emit | <tool> | <cmd>` dispatch. |
| `scripts/sieve.sh` | Strict SHACL ingest → GSP load. |
| `scripts/emit.sh` | SPARQL CONSTRUCT/SELECT emission. |
| `scripts/fuseki-doctor.sh` | External doctor (4 checks). |
| `setup.sh` / `setup.ps1` | One-command bring-up + doctor. |
| `examples/compose.fuseki.example.yml` | Local compose with file-mounted secret. |
| `fixtures/{shapes,good,bad}.ttl` | Doctor's accept/reject fixtures. |
| `.gitattributes` | Force LF on shell scripts (Windows CRLF would break the entrypoint). |

## Operational notes

- **Production deploy.** Stateful TDB2 needs a persistent volume — ACA with
  Azure Files, AKS with a PVC, or a managed equivalent. The `deploy.target`
  in `image.json` is `aca`; spokes copy this directory in and own the push.
- **Auth.** Dataset endpoints are **open** in the example compose (dev). Admin
  endpoints (`/$/*`) use `ADMIN_PASSWORD` from a mounted secret. For prod, layer
  a Shiro config that restricts the dataset endpoints too.
- **ROBOT.** `docker compose exec fuseki robot reason --input my.owl --output reasoned.owl`
  (and the full ROBOT subcommand surface) works in-image.
- **Foundational ontologies.** Not baked (network at build = flaky); mount them
  at `/ontologies` (vendored Turtle/OWL), or run a one-off `curl` inside the
  container to fetch gUFO/BFO/IAO/RO from their canonical URLs.
- **Related Labs:** [[Ontology-Pipeline]], [[Reification-and-Hyperedges]] (in
  the in-repo Obsidian vault).
