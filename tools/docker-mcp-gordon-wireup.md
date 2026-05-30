# Docker MCP Toolkit — Gordon wire-up (DevSecOps + layered local-host)

Curated set of MCP servers from the **Docker MCP Catalog** (`mcp/docker-mcp-catalog:latest`,
240 servers scanned 2026-05-30) selected for AgentArmy's two goals: a **DevSecOps CI/CD**
pipeline and **layered local-host optimization** of the container fleet.

Environment assumption: **Docker Desktop on Windows 11 (WSL2)** — no Proxmox, no Firewalla,
no standalone Kubernetes. Those catalog servers (Proxmox VE 286 tools, Firewalla 28, k8s 23)
are intentionally excluded; revisit if home-lab hardware changes.

## How the Toolkit works (so Gordon places things correctly)

- Each server runs as a **sandboxed container**; the **gateway** (`docker mcp gateway run`)
  aggregates them behind one endpoint. This mirrors our `tools/mcp-local-fleet/` posture.
- Secrets live in the **OS keychain** (`docker mcp secret set`), never in env files — aligns
  with our Key Vault discipline (don't paste tokens into the repo).
- Servers are scoped to a **profile**; Gordon is a first-class client (`--connect gordon`).
- Catalog reference form: `catalog://mcp/docker-mcp-catalog/<server-name>`; combine with `+`.

---

## Step 1 — Create the profile, connect Gordon

```powershell
docker mcp profile create --name agentarmy-devsecops --connect gordon
docker mcp profile ls    # confirm the ID — it is slugified: agentarmy-devsecops -> agentarmy_devsecops
```

> ⚠️ **Verified gotcha:** `docker mcp` slugifies the profile **name** (dashes) into an **id**
> (underscores). `profile server add` and `gateway run --profile` take the **id**
> (`agentarmy_devsecops`), NOT the dashed name — passing the dashed name fails with
> "profile not found". The commands below use the underscore id form.

## Step 2 — Tier 1: zero-secret, low-risk (enable immediately)

One command adds all five:

```powershell
docker mcp profile server add agentarmy_devsecops `
  --server catalog://mcp/docker-mcp-catalog/npm-sentinel+ramparts+inspektor-gadget+node-code-sandbox+neo4j-data-modeling
```

| Server | name | Goal | Why |
|---|---|---|---|
| NPM Sentinel | `npm-sentinel` | DevSecOps (SCA) | Supply-chain: `npmDeprecated`, `npmLicenseCompatibility`, `npmVulnerabilities`, `npmScore` across Node spokes. No key. Feeds `dependency-manager`. |
| Ramparts | `ramparts` | DevSecOps (MCP supply-chain) | Scans *our own* MCP servers (local-fleet, abstraction-mcp) with YARA + static analysis. Tools: `scan`, `scan-config`. |
| Inspektor Gadget | `inspektor-gadget` | Local-host optimize + harden | eBPF: `profile_cpu`, `profile_blockio`, `top_file`, `advise_seccomp`, `advise_networkpolicy`. Finds the hot tier container *and* generates hardening. **WSL2 caveat below.** |
| Node.js Sandbox | `node-code-sandbox` | Local-host (safe exec) | Disposable Docker containers for arbitrary JS — keeps agent code-exec off the host. |
| Neo4j Data Modeling | `neo4j-data-modeling` | Ontology / RDF↔LPG | **Design-time only, no DB.** `validate_data_model`, `export_to_owl_turtle`, `export_to_pydantic_models`, `get_node_cypher_ingest_query`, arrows.app + mermaid + GraphRAG projections. Serves the RDF↔LPG projection track ([ARC-ADR-041](../docs/decisions/ARC-ADR-041-pace-layered-projection-and-graduation.md)). See the *Neo4j vs ArcadeDB* section below. |

## Step 3 — Tier 2: DevSecOps deep scanners (mostly secret-gated)

Set the secret (keychain), then add the server. Run only the rows you want.
**Exception:** `aws-terraform` needs **no secret** — it's grouped here as a DevSecOps scanner
(Checkov IaC) but you can also fold it into the Tier 1 command if you prefer.

```powershell
# SonarQube — SAST + quality gate (Community edition can self-host as a container in local-stack)
"<sonarqube-token>" | docker mcp secret set SONARQUBE_TOKEN
docker mcp profile server add agentarmy_devsecops --server catalog://mcp/docker-mcp-catalog/sonarqube

# Vuln NIST / NVD — CVE intelligence for /security-review
"<nvd-api-key>" | docker mcp secret set MCP_API_KEY
docker mcp profile server add agentarmy_devsecops --server catalog://mcp/docker-mcp-catalog/vuln-nist-mcp-server

# Docker Hub — image hardening for our 17 image.json builds (dockerHardenedImages, tag/repo scan)
"<dockerhub-pat>" | docker mcp secret set HUB_PAT_TOKEN
docker mcp profile server add agentarmy_devsecops --server catalog://mcp/docker-mcp-catalog/dockerhub

# StackHawk — DAST against the tunnel'd frontend (:3000). Needs a StackHawk SaaS account.
"<stackhawk-api-key>" | docker mcp secret set STACKHAWK_API_KEY
docker mcp profile server add agentarmy_devsecops --server catalog://mcp/docker-mcp-catalog/stackhawk

# AWS Terraform — Checkov IaC scan (RunCheckovScan; Checkov itself is cloud-agnostic). No secret.
docker mcp profile server add agentarmy_devsecops --server catalog://mcp/docker-mcp-catalog/aws-terraform
```

## Step 4 — Verify

```powershell
docker mcp profile server ls
docker mcp secret ls
docker mcp gateway run --profile agentarmy_devsecops   # gateway Gordon talks to (MUST name the profile; bare `run` uses `default`)
```

---

## Neo4j vs ArcadeDB — hub default + BYO lane

The catalog ships five Neo4j servers. The split is **design-time tool** (run in hub) vs
**database connectors** (never run in hub — offered as **BYO** to users/spokes via the
credentials broker, [ARC-ADR-037](../docs/decisions/ARC-ADR-037-byo-credentials-secrets-broker.md)).

| Neo4j server | name | Secret | Placement |
|---|---|---|---|
| Neo4j Data Modeling | `neo4j-data-modeling` | none | **Tier 1 — runs in hub.** No DB; pure modeling/projection. |
| Neo4j (core) | `neo4j` | `NEO4J_PASSWORD` | **Tier 3 — BYO opt-in.** `read/write-cypher`, `get-schema`, `list-gds-procedures`. |
| Neo4j Cypher | `neo4j-cypher` | `NEO4J_PASSWORD` | **Tier 3 — BYO opt-in.** Minimal Cypher surface. |
| Neo4j Memory | `neo4j-memory` | `NEO4J_PASSWORD` | **Tier 3 — BYO opt-in.** Graph-backed agent memory. |
| Neo4j Cloud Aura | `neo4j-cloud-aura-api` | `NEO4J_AURA_CLIENT_SECRET` | **Tier 3 — BYO opt-in.** Aura instance lifecycle (create/pause/resume). |

**Why BYO, not excluded:** AgentArmy is a Hub→Spoke template that *abstracts* third-party
systems (ADR-036) and lets users register their own keys (ADR-037, "raw keys stay
server-side"). A spoke or user that brings their own Neo4j / Aura is a deliberate, isolated
choice — the **hub itself never runs Neo4j**, so there is no split-brain with ArcadeDB.
ArcadeDB remains the hub-default graph DB; Neo4j is a first-class **BYO lane**.

**Guardrail:** don't run a hub-side Neo4j *alongside* ArcadeDB for the **same data in the
same layer** — that's the only real duplication. BYO (a user's external Neo4j/Aura, scoped
by broker creds) is fine and is the intended pattern.

`neo4j-data-modeling` (Tier 1) stays the upstream bridge regardless of backend: author a
property-graph model → `validate_data_model` → project to `export_to_owl_turtle` (Fuseki /
ontology side), `export_to_pydantic_models` (typed clients), and the Cypher ingest queries.
Squarely on the RDF↔LPG track ([ARC-ADR-041](../docs/decisions/ARC-ADR-041-pace-layered-projection-and-graduation.md)), `12-knowledge-ontology`.

**Validated dialect caveat** (see [`tools/selfmodel/validate-neo4j-modeling.mjs`](selfmodel/validate-neo4j-modeling.mjs)
+ [the validation report](selfmodel/NEO4J-MODELING-VALIDATION.md)): the **node-ingest** Cypher
(`UNWIND $records … MERGE`) is portable openCypher and runs on ArcadeDB. The **constraint** DDL
it emits (`CREATE CONSTRAINT … IS NODE KEY`) is **Neo4j-5 dialect** that ArcadeDB does *not*
implement — projecting to ArcadeDB needs a constraint→`CREATE INDEX`/type-schema shim. Don't
assume the whole Cypher bundle is ArcadeDB-portable.

## Step 5 — Tier 3: BYO graph connectors (opt-in, OFF by default)

Enable only for a user/spoke that brings their own Neo4j or Aura. Use a **separate, dedicated
profile** (`agentarmy-byo-neo4j`) so these never co-mingle with the hub-default DevSecOps
profile.

### Two distinct credential flows — don't conflate them

The Docker MCP Toolkit resolves secrets from the **local OS keychain** (`docker mcp secret
set`); it does **not** natively call the Azure-backed ADR-037 broker. So there are two paths,
and this wire-up is the *first* one:

- **Local-dev BYO (this wire-up):** the operator sets *their own* Neo4j/Aura secret into the
  Docker MCP local keychain. Single-operator, local-only — fine for the trusted solo stage.
  The keychain `secret set` below **is** the source of the credential here.
- **Brokered (hub/spoke, multi-user — ADR-037):** raw key is registered in `akv01-agentarmy`
  as `cred-{user}-neo4j` / `cred-{user}-aura` and resolved **server-side by backend-core**,
  which injects it into the outbound call. The MCP tool never holds the raw key, and the
  Docker keychain is **not** in this path. Bridging the broker into a Docker MCP secrets
  engine (so the gateway pulls from the broker instead of the local keychain) is follow-up
  work tracked in the Enabler — until then, brokered BYO runs through backend-core, not Gordon.

```powershell
# Dedicated BYO profile — isolated from agentarmy-devsecops
docker mcp profile create --name agentarmy-byo-neo4j --connect gordon

# Self-hosted / external Neo4j (operator's own local-dev secret -> local keychain)
"<users-neo4j-password>" | docker mcp secret set NEO4J_PASSWORD
docker mcp profile server add agentarmy_byo_neo4j `
  --server catalog://mcp/docker-mcp-catalog/neo4j+neo4j-cypher+neo4j-memory

# Neo4j Aura (managed cloud) — instance lifecycle + data
"<users-aura-client-secret>" | docker mcp secret set NEO4J_AURA_CLIENT_SECRET
docker mcp profile server add agentarmy_byo_neo4j `
  --server catalog://mcp/docker-mcp-catalog/neo4j-cloud-aura-api

docker mcp gateway run --profile agentarmy_byo_neo4j
```

> Consider a **separate profile** (e.g. `agentarmy-byo-neo4j`) per user/spoke so BYO creds
> and connectors stay isolated from the hub-default DevSecOps profile.

## Risk / placement notes (do not skip)

- **Inspektor Gadget** runs eBPF in the Docker Desktop WSL2 VM — it observes the Linux
  container layer, not the Windows host directly. Good enough to profile/harden the fleet;
  it will *not* tune Windows itself.
- **Node.js Sandbox** spawns ephemeral Docker containers — it needs Docker socket access.
  Acceptable (it's the point), but it is a code-execution surface; keep it profile-scoped.
- **Desktop Commander** (catalog: `desktop-commander`) was **deliberately excluded** — broad
  local terminal/process/file exec that duplicates Claude Code's own tools and widens the
  attack surface for marginal gain.
- **Skipped, platform mismatch:** CircleCI / Buildkite / Testkube (we're on GitHub Actions);
  GitHub Official MCP (redundant with `gh` CLI). Azure/Cloudflare/Postman/Stripe/BigQuery
  already connected via other MCP servers — do not re-add from this catalog.

---

## Machine-readable manifest

```json
{
  "catalog": "mcp/docker-mcp-catalog:latest",
  "profile": { "name": "agentarmy-devsecops", "connect": ["gordon"] },
  "servers": [
    { "name": "npm-sentinel",         "image": "mcp/npm-sentinel",         "tier": 1, "secret": null,              "goal": "devsecops-sca" },
    { "name": "ramparts",             "image": "mcp/ramparts",             "tier": 1, "secret": null,              "goal": "devsecops-mcp-supplychain" },
    { "name": "inspektor-gadget",     "image": "mcp/inspektor-gadget",     "tier": 1, "secret": null,              "goal": "localhost-optimize-harden" },
    { "name": "node-code-sandbox",    "image": "mcp/node-code-sandbox",    "tier": 1, "secret": null,              "goal": "localhost-safe-exec" },
    { "name": "neo4j-data-modeling",  "image": "mcp/neo4j-data-modeling",  "tier": 1, "secret": null,              "goal": "ontology-rdf-lpg-projection" },
    { "name": "sonarqube",            "image": "mcp/sonarqube",            "tier": 2, "secret": "SONARQUBE_TOKEN", "goal": "devsecops-sast" },
    { "name": "vuln-nist-mcp-server", "image": "mcp/vuln-nist-mcp-server", "tier": 2, "secret": "MCP_API_KEY",    "goal": "devsecops-cve" },
    { "name": "dockerhub",            "image": "mcp/dockerhub",            "tier": 2, "secret": "HUB_PAT_TOKEN",   "goal": "devsecops-image-hardening" },
    { "name": "stackhawk",            "image": "mcp/stackhawk",            "tier": 2, "secret": "STACKHAWK_API_KEY","goal": "devsecops-dast" },
    { "name": "aws-terraform",        "image": "mcp/aws-terraform",        "tier": 2, "secret": null,                       "goal": "devsecops-iac-checkov" },
    { "name": "neo4j",                "image": "mcp/neo4j",                "tier": 3, "secret": "NEO4J_PASSWORD",            "goal": "byo-graph", "default": "off", "broker": "ADR-037 cred-{user}-neo4j" },
    { "name": "neo4j-cypher",         "image": "mcp/neo4j-cypher",         "tier": 3, "secret": "NEO4J_PASSWORD",            "goal": "byo-graph", "default": "off", "broker": "ADR-037 cred-{user}-neo4j" },
    { "name": "neo4j-memory",         "image": "mcp/neo4j-memory",         "tier": 3, "secret": "NEO4J_PASSWORD",            "goal": "byo-graph-memory", "default": "off", "broker": "ADR-037 cred-{user}-neo4j" },
    { "name": "neo4j-cloud-aura-api", "image": "mcp/neo4j-cloud-aura-api", "tier": 3, "secret": "NEO4J_AURA_CLIENT_SECRET", "goal": "byo-aura-lifecycle", "default": "off", "broker": "ADR-037 cred-{user}-aura" }
  ],
  "hub_default_graph_db": "arcadedb",
  "byo_guardrail": "do not run a hub-side Neo4j alongside ArcadeDB for the same data in the same layer; BYO external/Aura is fine",
  "excluded": {
    "desktop-commander": "broad local-exec, duplicates Claude Code tools",
    "proxmox-ve|firewalla|kubernetes|kubectl": "no matching home-lab hardware (Docker Desktop only)",
    "circleci|buildkite|testkube": "we use GitHub Actions",
    "github-official": "redundant with gh CLI",
    "azure|cloudflare|postman|stripe|bigquery": "already connected via other MCP servers"
  }
}
```
