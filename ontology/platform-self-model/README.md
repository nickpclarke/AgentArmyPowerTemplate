# Platform Self-Model — AgentArmy describing itself

A **digital twin of the AgentArmy fleet**, authored as an ontology and compiled into a
graph. The same UFO/gUFO pipeline you point at external domains (risk-mitigation, the
`knowledge-drop` scenario, FIBO) — turned on **the platform itself**. Repos, contracts,
containers, platforms, partners, agents, decisions, and how they bind become a typed,
queryable, provenance-tracked graph.

> **Why:** to *visualise what we're doing*, *communicate it* (to ourselves and to partners
> at Anthropic, Microsoft, Cerebras), *make better decisions* from a single source of truth,
> and — eventually — *simulate and act* on changes (drag-drop modules, flip feature flags)
> against the model before touching the running fleet.

This is the **direct-authoring path** of the ontology pipeline ([docs/ontology-pipeline.md](../../docs/ontology-pipeline.md)):
the architecture is *known*, so it's hand-authored structural knowledge, not Cerebras-sifted
from documents. It reuses the IR spec, the hyperedge-as-vertex design (ARC-ADR-016), and the
"offer both" gUFO + BFO/CCO dual projection.

## Layout

```
platform-self-model/
├── model/
│   ├── model.yaml        ← T-Box (the system ontology): 26 types, 4 relators. SOURCE OF TRUTH.
│   └── instances.yaml    ← A-Box: real fleet snapshot (74 instances, 36 n-ary facts).
├── generated/            ← C# object model (records + hypergraph base). Never hand-edit.
├── persistence/          ← ArcadeDB DDL (hyperedge-as-vertex, ARC-ADR-016).
├── semantic/             ← gUFO OWL projection (parses: 89 triples). BFO/CCO sidecar = future slice.
├── instances/            ← fragments.json: the A-Box as ARC-ADR-016 fragments (loader input).
├── viz/                  ← Mermaid views + self-model-graph.html (interactive Cytoscape viewer, offline).
└── provenance/           ← build-manifest.json (input/output content hashes).
```

## Run it

```bash
python -m pip install pyyaml jsonschema        # validation deps (httpx only for live load)

python tools/selfmodel/validate.py             # L1: well-formed IR, unique ids, valid stereotypes
python tools/selfmodel/emit.py                 # compile IR + instances -> all projections above
python tools/selfmodel/load.py --dry-run       # build the load plan (no DB, pure stdlib)
python tools/selfmodel/load.py                 # load into ArcadeDB (needs a live :2480 — see below)
```

The Mermaid views (`viz/*.mmd`) render in Obsidian, mermaid.live, or the frontend cockpit.
**Interactive graph:** open `viz/self-model-graph.html` in any browser — a self-contained
Cytoscape view of the whole fleet (drag / zoom / click-for-details / filter by type / search),
generated from `fragments.json`, no DB or network needed. (Cytoscape 3.30.2 vendored alongside, MIT.)

## Status (2026-05-30)

| Step | State |
|---|---|
| T-Box authored + **L1 validated** | done (26 types, 4 relators) |
| A-Box from real data | done (74 vertices, 36 relators, 15 edges) |
| Emitter: ArcadeDB DDL · C# object model · gUFO TTL · fragments · Mermaid · manifest | done (deterministic) |
| gUFO projection parses as RDF | done (89 triples) |
| Loader builds idempotent plan (64 DDL · 74 upserts · 179 relator ops) | done |
| **Live load into Azure ArcadeDB** | **done (2026-05-30)** — 110 OntologyElement vertices (74 objects + 36 relators) + 179 role-edges + 15 edges in the `selfmodel` db, loaded from inside the VNet via a Container Apps Job (`tools/selfmodel/_job/`) |

### Live load — Azure (in-VNet Container Apps Job)

The Azure `arcadedb` runs on a **private** ingress (only reachable inside `cae-arcade-platform`),
so the load runs *inside* the VNet rather than exposing the DB:

1. `az acr build` the loader image (`tools/selfmodel/_job/Dockerfile`) into `arcadeplatformacr` — cloud build, no local docker.
2. `az containerapp job create` a Manual job in `cae-arcade-platform`; the arcadedb root password is sourced from arcadedb's own config into a job secret; `ARCADEDB_URL=https://arcadedb.internal…` (port 443 — internal ingress redirects HTTP→HTTPS), `DB_NAME=selfmodel`.
3. `az containerapp job start` → the job reaches arcadedb over private ingress and upserts the graph (idempotent — safe to re-run).

This exercise also found a real bug in the reference scaffold's `arcadedb-schema.sql`: ArcadeDB
requires `IF NOT EXISTS` **before** `EXTENDS` (the reference had it after, and had never been run
against a live ArcadeDB). Fixed in `emit.py`.

## What this is **not** (the scope line)

The graph holds the **schema + slow-moving structural facts**. It deliberately does **not**
freeze fast-moving operational state (which issue is *In Progress* this minute) — that stays
**federated live from GitHub** via `tools/status.mjs` and the fleet-heartbeat. Ontology =
stable truth; dashboards = live truth. (See Labs "Open Questions and Risks" — the
"model-the-universe" trap.)

## How it plugs into the rest

- **Wardley** — every `SystemComponent` carries an `EvolutionStage` (Genesis→Commodity). The
  `/wardley` skill consumes a value chain; this model emits one. The map becomes a *projection
  of the graph*, not a redraw.
- **Partners** — the gUFO/OWL projection is W3C-standard and shareable with anyone (Anthropic);
  the BFO/CCO sidecar (next slice) is the lingua franca for Microsoft's IKW-GraphEngine. Cerebras
  is already the in-loop proposer.
- **The fleet's own tools** — `load.py` follows the proven `backend-core/app/ontology/arcade_schema.py`
  pattern, so the same graph the cockpit reads can hold the self-model. The forge (ARC-ADR-029)
  and the UDA connector layer (ADR-0001) are the production path for object-model generation and
  loading once this first cut graduates.

## First-cut caveat

`tools/selfmodel/emit.py` is a **deliberate first cut** of the "build the generator vs adopt
LinkML" open question — a working, deterministic Python emitter, not yet the full six-projection
compiler. It proves the dogfood end-to-end so the generator decision can be made on evidence.
