# Validation — neo4j-data-modeling on the platform self-model (#373)

Live build + validation of the Docker MCP Toolkit `neo4j-data-modeling` server against the
real AgentArmy platform self-model, proving the RDF↔LPG round-trip ([ARC-ADR-041](../../docs/decisions/ARC-ADR-041-pace-layered-projection-and-graduation.md)).

- **Date:** 2026-05-30 · **Host:** Docker Desktop 29.4.2 (WSL2)
- **Harness:** [`validate-neo4j-modeling.mjs`](validate-neo4j-modeling.mjs) — drives `mcp/neo4j-data-modeling` over MCP stdio (no DB, no secret). Reproducible: `node tools/selfmodel/validate-neo4j-modeling.mjs roundtrip`.
- **Input:** [`ontology/platform-self-model/semantic/model.gufo.ttl`](../../ontology/platform-self-model/semantic/model.gufo.ttl) (gUFO OWL projection)

## Results — RESULT: PASS

| Step | Tool | Result |
|---|---|---|
| OWL Turtle → property-graph model | `load_from_owl_turtle` | PASS — **22 nodes**, 0 relationships |
| validate model | `validate_data_model` | PASS — `true` |
| constraints Cypher | `get_constraints_cypher_queries` | PASS — **24 statements** |
| node ingest Cypher | `get_node_cypher_ingest_query` | PASS — `UNWIND $records as record … MERGE` |
| round-trip back to OWL | `export_to_owl_turtle` | PASS — 3261 chars |

Generated artifacts (in [`ontology/platform-self-model/generated/`](../../ontology/platform-self-model/generated/)):
`selfmodel.neo4j-datamodel.json`, `selfmodel.ingest.cypher`, `selfmodel.roundtrip.ttl`.

The 22 nodes include the self-model's **reified relators** (`governed_by_decision`,
`partner_engagement`) — the hyperedge-as-vertex pattern (ARC-ADR-016) survives the projection
as first-class node labels. Good signal: the bridge preserves our modeling intent.

## Key finding — Cypher dialect is NOT fully ArcadeDB-portable

- **Node ingest** (`UNWIND $records … MERGE`) = portable openCypher → runs on ArcadeDB. ✅
- **Constraint DDL** (`CREATE CONSTRAINT … IS NODE KEY`) = **Neo4j-5 dialect** → ArcadeDB does
  **not** implement it (ArcadeDB uses its own type/index schema). ⚠️ Needs a
  constraint→`CREATE INDEX`/type-schema shim before the projection targets ArcadeDB.

This is the actionable output for the `12-knowledge-ontology` cluster: the RDF↔LPG projection
(ADR-041) can reuse `neo4j-data-modeling` for modeling + ingest, but must own a small dialect
adapter for schema/constraints when the backend is ArcadeDB rather than Neo4j.

## Acceptance criteria (#373)

- [x] `agentarmy-byo-neo4j` / `agentarmy-devsecops` profile creation reproducible — **and fixed a
      doc bug:** `docker mcp` slugifies the profile *name* (dashes) to an *id* (underscores);
      `profile server add` / `gateway run --profile` need the **id** form. Doc updated.
- [x] `neo4j-data-modeling` round-trips the platform-self-model (load → validate → Cypher →
      export). Live PASS above.
- [x] Cypher generation verified; **portability nuance documented** (ingest portable; constraint
      DDL is Neo4j-dialect).
- [x] Guardrail (no hub-side Neo4j alongside ArcadeDB) documented in the wire-up + ADR-037.
- [x] Routed to `12-knowledge-ontology`.
- [ ] **Gated / follow-up:** execute the portable ingest Cypher against the live ArcadeDB
      (Azure ACI `rg-arcadedb-test`) — not run here (no local ArcadeDB; not writing to a shared
      test instance from a validation). Pairs with building the constraint-DDL shim.

## Reproduce

```bash
docker pull mcp/neo4j-data-modeling
node tools/selfmodel/validate-neo4j-modeling.mjs list        # tool schemas
node tools/selfmodel/validate-neo4j-modeling.mjs roundtrip   # full round-trip, exit 0 = PASS
```
