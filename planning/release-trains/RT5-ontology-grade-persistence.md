# RT5 — Ontology-Grade Persistence ("Pinning")

Durable Epic plan for adding a **backend-neutral object-pinning layer** to `templates/middle-core`,
honoring the repo's UFO/reification/bitemporal ontology design, with ArcadeDB as the first adapter.

> **The [GitHub Projects board](https://github.com/users/nickpclarke/projects/1) is the source of truth
> for status, fields, and issue numbers.** This page holds the durable backlog decomposition (Epic →
> Features/Enablers/Spikes, acceptance criteria, dependencies, SAFE fields). Issue numbers are assigned
> at board population — see [backlog/board-population-checklist.md](../backlog/board-population-checklist.md).
> Stable local IDs (`PIN-*`) below survive until then.

## Theme

Make middle-core runtime objects **persistable** — "pin" an object so it is fixed in a store as an
**immutable, content-addressed, bitemporal record** (serialization timestamp + identity hash), with an
idempotent "live" view on top. Persistence is a **provider-neutral abstraction**; ArcadeDB is one adapter
wired underneath, not baked into the core.

Grounding (already in-repo):
- UFO/gUFO upper ontology — `model/middle-core/ontology/top-level-ufo-lite.ttl`, `middle-core.ttl`
  (7 `gufo:Kind` concepts under `mc:BusinessObjectKind`; endurant vs perdurant/event distinction).
- Reification & hyperedges — `obsidian/labs/AgentArmyLabs/Reification-and-Hyperedges.md`
  (relator-as-vertex + `RoleBinding`; the knowledge-drop `ingest-evidence` 4-role relator is the showcase).
- Bitemporal, append-only — `obsidian/labs/AgentArmyLabs/Ontology-Pipeline.md`
  (valid-time + transaction-time + `superseded_at`; never overwrite).
- PROV-O + content-addressing — `planning/ideas/Ontology.md` (`ProvenanceStamp`, sha256, prov IRI).

## Summary

| Epic | Features | Enablers | Spikes | PI | Sequencing |
|---|---|---|---|---|---|
| **PIN-E** Ontology-grade pinning for middle-core | PIN-F1…F4 | PIN-EN1, PIN-EN2 | PIN-S1, PIN-S2 | **PI-3 (candidate)** | Independent of RT1–RT4 template work; schedule at PI planning |

**Total:** 1 Epic + 4 Features + 2 Enablers + 2 Spikes = 9 board items.
**Session estimate:** ~3–4 sessions (implementation-heavy runtime + adapter work; compare RT2 velocity).

---

## Backlog items

> SAFE fields per item: `Type`, `PI`, `Size`, `Estimate` (Fibonacci pts), `Priority`. Definition of Ready =
> these set + acceptance criteria below. Definition of Done = PR merged with `Closes #N`, tests green under
> `TreatWarningsAsErrors`.

### PIN-E — Epic: Ontology-grade object pinning for middle-core
- **Type:** Epic · **PI:** PI-3 (candidate) · **Priority:** P1
- **Outcome:** middle-core can pin endurants, perdurants, and reified relators into a store as immutable,
  content-addressed, bitemporal records with provenance, behind a provider-neutral seam (in-memory +
  ArcadeDB adapters). No new mapping attributes — mapping is driven off `GeneratedModel.BusinessObjects` /
  `GeneratedModelValidator`.
- **Children:** PIN-F1, PIN-F2, PIN-F3, PIN-F4, PIN-EN1, PIN-EN2, PIN-S1, PIN-S2.

### PIN-F1 — Feature: Pinning core domain primitives (provider-neutral)
- **Type:** Feature · **Size:** M · **Estimate:** 5 · **Priority:** P1 · **Depends on:** — (foundation)
- **Scope:** `Runtime/Pinning/` — `CanonicalJson` (key-sorted snake_case for deterministic hashing),
  `OntologyIri` (URN scheme: endurant `urn:agentarmy:mc:{concept}/{objectType}/{id}`, perdurant
  `urn:agentarmy:mc:event:{stateMachine}/{objectId}/{trigger}`, relator
  `urn:agentarmy:mc:relator:{relatorType}/{sha256(sorted participant identity hashes)}`), `PinHash`
  (`Identity`, `Content`), `ISerializationClock` + `SystemSerializationClock`, `UfoStereotype` +
  `ConceptToUfo` (aligned to the `.ttl`), `ProvenanceStamp`.
- **Acceptance:** identity hash stable across payload change; content hash changes with payload/valid-time;
  **relator identity = deterministic hash of bound participant identities** (order-independent after
  role/ordinal sort); canonical JSON is key-order independent. Unit tests cover each.

### PIN-F2 — Feature: Reification + bitemporal PinnedElement model
- **Type:** Feature · **Size:** M · **Estimate:** 5 · **Priority:** P1 · **Depends on:** PIN-F1
- **Scope:** `RelatorInstance`, `RoleBinding`, `PinnedElement` (bitemporal record: `iri, identity_hash,
  content_hash, kind, object_type, object_id, ontology_concept, ontology_iri, ufo_stereotype, state,
  valid_from, valid_to, recorded_at, superseded_at, canonical_payload, provenance, schema_version`),
  `OntologyPinner` (`ModelObject`/`RelatorInstance` → `PinnedElement`, validate via
  `GeneratedModelValidator`, resolve concept/UFO/provenance from metadata).
- **Acceptance:** serialization timestamp comes from injected clock; unknown objectType throws; endurant
  vs perdurant classification correct; the 4-role `ingest-evidence` relator builds with bound participants.

### PIN-F3 — Feature: Backend-neutral pin store + seam (in-memory default)
- **Type:** Feature · **Size:** M · **Estimate:** 5 · **Priority:** P1 · **Depends on:** PIN-F2
- **Scope:** `IPinStore` (`PinObjectAsync`, `PinRelatorAsync`, `PinGraphAsync`, `GetHistoryAsync`,
  `GetLiveAsync`), `IPinBackend` (neutral ops — no DB types), `PinStore` orchestrator, `InMemoryPinBackend`.
- **Acceptance:** first pin → live + 1 immutable ledger entry; re-pin identical content → ledger no-op
  (idempotent); mutated payload → 2nd immutable entry + prior superseded; `GetHistoryAsync` ordered by
  `recorded_at`; `PinGraphAsync` pins all knowledge-drop objects, binary relationships, **and** the
  `ingest-evidence` relator with role bindings + provenance.

### PIN-F4 — Feature: ArcadeDB adapter (`ArcadeDbPinBackend`)
- **Type:** Feature · **Size:** L · **Estimate:** 8 · **Priority:** P2 · **Depends on:** PIN-F3, PIN-S1
- **Scope:** `Runtime/Pinning/Adapters/ArcadeDb/ArcadeDbPinBackend.cs` — maps neutral ops to ArcadeDB
  HTTP/JSON command API; DDL for `OntologyElement`⟵`HyperNode`/`HyperEdge`, `BINDS_ROLE`, `ProvenanceVertex`
  + `WAS_GENERATED_BY`, immutable `PinLedgerEntry`; UNIQUE indexes on `ontology_iri` + `content_hash`,
  composite `(type, valid_from, valid_to)`, hash index on `role_name`; `UPDATE…UPSERT` live + guarded
  `INSERT` ledger. Credentials server-side (`ARCADEDB_PASSWORD_FILE`) per
  `extensions/arcadedb-cockpit/BACKEND_CONTRACT.md`. ArcadeDB is persistence only — **not** the reasoner.
- **Acceptance (live ArcadeDB):** `EnsureReadyAsync` DDL is idempotent; unchanged object pinned twice →
  1 live row + 1 ledger row; `ingest-evidence` persists as a `HyperEdge` vertex with `BINDS_ROLE` edges.

### PIN-F5 → folded into PIN-EN1 (endpoints/DI live with the wiring enabler)

### PIN-EN1 — Enabler: HTTP endpoints + DI wiring + backend selection
- **Type:** Enabler · **Size:** S · **Estimate:** 3 · **Priority:** P1 · **Depends on:** PIN-F3
- **Scope:** `Program.cs` — register `ISerializationClock`, `IPinStore`→`PinStore`,
  `IPinBackend`→`InMemoryPinBackend` by default / `ArcadeDbPinBackend` when configured
  (`PIN_BACKEND=arcadedb` + `ARCADEDB_URL`). Endpoints `POST /pins/scenarios/knowledge-drop`,
  `GET /pins/{identityHash}/history`. Reuse existing snake_case/kebab JSON.
- **Acceptance:** in-memory smoke: POST pins the graph, GET returns a time-ordered immutable series with
  stable identity hash, per-version content hashes, serialization timestamps, UFO stereotypes, relator.

### PIN-EN2 — Enabler (follow-up): Generate `ConceptToUfo` + ArcadeDB DDL from modelgen
- **Type:** Enabler · **Size:** M · **Estimate:** 5 · **Priority:** P2 · **Depends on:** PIN-F1, PIN-F4
- **Scope:** Emit the UFO map and ArcadeDB schema DDL from `tools/modelgen/` (drift-gated like other
  `.g.cs`), removing the hand-written v1 map. Later PI; not required for first delivery.
- **Acceptance:** regenerating the model produces the UFO map + DDL deterministically; drift check passes.

### PIN-S1 — Spike: ArcadeDB transaction/UPSERT/idempotency semantics
- **Type:** Spike · **Size:** S · **Estimate:** 3 · **Priority:** P2 · **Time-box:** ½ session
- **Question:** Confirm against a live ArcadeDB how `UPDATE…UPSERT`, unique-index-guarded `INSERT`, and
  HTTP command batching behave, so PIN-F4 idempotency is correct. **Output:** short findings note + the
  exact SQL shapes PIN-F4 should use.

### PIN-S2 — Spike: bitemporal "pin/snapshot" query patterns
- **Type:** Spike · **Size:** S · **Estimate:** 2 · **Priority:** P2 · **Time-box:** ½ session
- **Question:** Define the queries for "what was the graph state at pin X" (filters on `recorded_at` /
  `valid_to` / `superseded_at`). **Output:** query templates + any extra index needs feeding back to PIN-F4.

---

## Dependency graph

```
PIN-F1 (core primitives)
  └─ PIN-F2 (reification + PinnedElement)
       └─ PIN-F3 (store + seam + in-memory)        ← keystone
            ├─ PIN-EN1 (endpoints + DI)
            └─ PIN-F4 (ArcadeDB adapter)  ← PIN-S1 (semantics), PIN-S2 (queries)
                 └─ PIN-EN2 (generate UFO map + DDL)  [follow-up PI]
```

**Keystone:** PIN-F3 — once the provider-neutral store + in-memory backend exist, endpoints and the
ArcadeDB adapter proceed in parallel, and the abstraction is provable via backend-contract tests.

## Ready for the board

When scheduled, create these 9 issues (labels: `Epic`/`Feature`/`Enabler`/`Spike`), set `Type`, `PI`,
`Size`, `Estimate`, `Priority` per item above, link PIN-F*/PIN-EN*/PIN-S* as sub-issues of **PIN-E**, then
add to project 1 — follow [backlog/board-population-checklist.md](../backlog/board-population-checklist.md).
The full implementation design is captured in the approved session plan (ontology-grade backend-neutral
pinning) and mirrors the file list in PIN-F1…F4 / PIN-EN1.

## Notes

- **Not yet implemented.** This is backlog; no `templates/middle-core` code ships in this planning step.
- **No live board writes yet.** Issue numbers are assigned at board population, not here.
- Scheduling vs RT1–RT4: this track touches the middle-core runtime, not template routing/ops, so it can
  run independently; confirm PI/session placement at PI planning.
