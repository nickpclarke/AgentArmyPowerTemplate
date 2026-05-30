# ARC-ADR-043 — Ontology-Driven Generative Programming Pipeline ("the Factory"): an AOT-compiled, LLM-elaborated, self-refining alternative to runtime ontological-hypergraph platforms

| Field | Value |
|---|---|
| ID | ARC-ADR-043 |
| Status | Proposed |
| Date | 2026-05-30 |
| Deciders | Hub owner (Nicky Clarke) |
| Supersedes | — |
| Superseded by | — |
| Tags | generative-programming, ontology, hypergraph, state-machines, forge, codegen, llm, factory, patent-distinct |

## Context and problem statement

We want the platform to **generate itself** from a specification, with the human (and the LLM) authoring *meaning*, not boilerplate. Today the split is measured (this session): of the code we own, ~16% is deterministically generated (the typed data objects, from the forge) and ~84% is hand-written — split between **the generator/runtime kernel** (the forge emitter, protocol drivers, the hydration planner algorithm) and **per-contract logic** (routes, transports, tests).

The goal is to push the *marginal* hand-code **per new contract toward zero** — the compiler property — while using generative LLM AI exactly where deterministic generation cannot reach, and to have the platform **continuously refine, decorate, and elaborate** the ontology and the generators over time.

**Prior art / constraint.** EnterpriseWeb achieves "100% generative programming" via a **patented runtime ontological-hypergraph + state-machine engine** (JavaScript, late-bound dynamic composition). We must **invent our own, non-infringing path**. This ADR chooses a mechanism that is materially different (ahead-of-time compilation, not runtime interpretation) and records the distinction.

We already hold the load-bearing pieces:
- **Ontological hypergraph** — [ARC-ADR-016](ARC-ADR-016-ontology-representation-reification-hyperedges.md) (reification + hyperedges: relator-vertex + typed role-binding).
- **The compiler** — [ARC-ADR-029](ARC-ADR-029-agentarmy-forge-codegen-container.md) (agentarmy-forge: ontology → IR → deterministic multi-target emit; Rust emitter + IR list/state extensions added this session).
- **State machines** — every data object in `data-platform-contract.g.json` carries a lifecycle state machine; middle-core's runtime is a graph/state model.
- **Conformance gate** — the Fuseki **sieve** ([ARC-ADR-019](ARC-ADR-019-ontology-reasoning-layer.md)): SHACL in, SPARQL CONSTRUCT/SELECT out.
- **Continuous loop** — `tools/fleet-heartbeat.mjs` + `/loop`.
- **Runtime hydration** — the UDA (backend-core `docs/adr/0001-universal-data-adapter.md`) + the cost-based hydration planner (rust-api-v2 `uda.rs`).

## Decision drivers

- **Marginal determinism:** a new contract / data object should ship with ~0 hand-written lines.
- **Optimal mix:** deterministic generation for everything spec-derivable; LLM for spec authoring/elaboration and the irreducible escape hatch; never ad-hoc LLM code in the generated path.
- **Patent-distinct** from EnterpriseWeb's runtime-hypergraph method.
- **Continuous self-refinement:** the platform elaborates the ontology and the generators over time, under governance.
- **Determinism ≠ correctness:** byte-identical + drift-guarded output is the goal; spec review + tests remain the correctness guarantee.

## Considered options

1. **Runtime ontological-hypergraph interpreter + state-machine engine** (EnterpriseWeb-style late-bound composition). — **Rejected:** direct patent-infringement risk, and we prefer typed, compilable, multi-language artifacts over a single dynamic runtime.
2. **Status quo — hand-write per contract.** — **Rejected:** does not scale; drifts; no single source of truth.
3. **AOT ontology→IR→multi-target deterministic emit + a thin hand-written runtime stdlib + an LLM spec-elaboration loop** (chosen). — Compiler model: the ontology is the source; the forge is the compiler; the runtime is a small reusable stdlib; the LLM authors/elaborates the source and fills escape hatches; a governed loop refines it.

## Decision outcome — the Factory (five layers)

### 1. Spec layer — the ontology *is* the program
The single source of truth is the **ontological hypergraph + state machines** (ARC-ADR-016): entities, reified n-ary relations (relator-vertices) with typed role-binding, and per-object / per-process **state machines**. The ontology is **decorated** with the facets a generator needs:
- **type facet** — fields + types (have it).
- **state facet** — lifecycle state machines (have it).
- **binding facet** — object ↔ each backend's physical schema + retrieval pattern (the next missing piece).
- **policy facet** — access pattern per object, RBAC, and the backend capability/cost model.

These facets are ontology **decorations**, not separate files of code. Authoring/elaborating the ontology is the act of programming.

### 2. Compiler — the forge (ARC-ADR-029)
A **total function**: ontology → IR → deterministic, **byte-identical**, **drift-guarded** multi-target emit (Rust / C# / TS / Python today; queries, routes, mappings, and conformance tests next). This is the deterministic generative-programming engine. It is hand-written **once** and amortized across every contract.

### 3. Runtime stdlib — small, hand-written, reused
The irreducible, contract-independent kernel: **protocol drivers** (Postgres/tokio-postgres, HTTP, SPARQL, Arrow Flight), the **hydration planner algorithm** (cost-based selection over a static backend profile — see `uda.rs`), the serving-framework glue, and a **narrow escape-hatch trait**. This is the "compiler's standard library." It grows slowly and is shared by all generated spokes.

### 4. LLM tier — generative AI where determinism cannot reach
The LLM (Claude / fleet agents) does exactly the work a compiler cannot:
- **author + elaborate the ontology** (draft entities, relations, state machines, bindings, policies from intent, docs, and existing schemas);
- **synthesize escape-hatch logic** for requirements outside the DSL's grammar;
- **propose decorations / refinements** to enrich the ontology over time;
- **review + repair**.

**Invariant:** every LLM contribution is funneled **into the spec** (where it becomes deterministic + drift-guarded) **or** into a **tested escape hatch** — never as ad-hoc code inside the generated path.

### 5. Continuous refinement loop — the heartbeat as the factory's flywheel
The platform cycles (driven by `fleet-heartbeat.mjs` / `/loop`), governed end-to-end:

```
intent / docs / usage signals
   → LLM proposes ontology decorations / refinements
   → SHACL sieve (ARC-ADR-019) validates conformance (reject non-conformant)
   → forge regenerates (byte-identical, multi-target)
   → tests gate: drift (golden) + contract-conformance + gated live
   → human freeze / merge
   → measure: marginal-hand-code, generated-coverage, escape-hatch count
   → feed back
```

The loop **decorates and elaborates** the ontology and the emitters over time. Nothing reaches `main` un-validated: the sieve guards conformance, golden tests guard determinism, live tests guard reality, and the human freezes the spec.

### The optimal-mix rule (deterministic ÷ LLM)
> Generate deterministically **everything derivable from the spec**. Use the LLM to **author/elaborate the spec**, to fill the **irreducible escape hatch**, and to **propose refinements**. A human reviews and freezes specs. Measure success as **marginal hand-code per contract → 0**, not as a percentage of the repo (the fixed kernel never shrinks).

## Patent-distinctness from EnterpriseWeb (explicit)

| Dimension | EnterpriseWeb (patented) | AgentArmy Factory (this ADR) |
|---|---|---|
| When | **Runtime** — interprets the hypergraph + state machines to compose apps dynamically (late binding) | **Ahead-of-time** — the forge **compiles** the ontology into static artifacts at build time |
| Artifact | A dynamic graph executed by their engine | Typed, **byte-identical**, multi-language **source code** that compiles to ordinary services |
| Verification | Runtime composition | **Golden (byte-identical) + SHACL conformance + live** tests at build time |
| Runtime decisioning | A general hypergraph interpreter | Only a **bounded cost-based selector** over a static profile table (the hydration planner) — not a general graph interpreter |

We **do not interpret the ontology at runtime**; we emit code from it at build time. This is a different mechanism, a different artifact, and a different verification model. **Action:** keep this distinction documented; avoid any runtime hypergraph-execution feature without IP counsel review.

## The spec-completeness ladder (what unlocks what)

| Generated output | Spec facet required | Status |
|---|---|---|
| Typed data objects (structs + state enums) | type + state facet (the contract) | **Done** |
| Per-backend **queries + row→object mappings** | **binding facet** (object↔backend schema) | **Phase 1 (next)** |
| Routes / handlers / serde / RBAC gating | policy facet (access + RBAC) | Phase 2 |
| Planner config (capabilities, cost, per-kind pattern) | cost/capability facet | Phase 2 |
| Conformance / drift / live tests | contract + bindings | Phase 3 |
| State-machine transition guards + effects | state facet + hyperedges | Phase 5 |
| Bespoke / novel logic | — (LLM escape hatch, tested) | Ongoing |

Each rung adds **one ontology decoration** and moves a band of code from hand-written to generated.

## Binding facet — formal schema (the P1 contract)

A `binding` decorates each data object with *where it physically lives* per backend. One file per
spoke (e.g. `contracts/bindings.yaml`), keyed by object then backend:

```yaml
KnowledgeSourceData:
  postgres:
    relation: factory.knowledge_source     # schema-qualified table / view
    columns:                                # canonical field -> physical column
      source_id: src_id
      display_name: name
      provider_ref: provider
      state: status
  arcadedb:
    vertex: KnowledgeSource
    columns: { source_id: cid }
```

**Emit semantics (Postgres):** `SELECT <physical> AS <canonical>, … FROM <relation>` — physical→canonical
aliasing so the generated row decoder always reads *canonical* field names (uniform across backends).
A field absent from `columns` defaults to identity (canonical == physical). An optional `select:` key
overrides with explicit SQL (a query-level escape hatch — e.g. a table-free `VALUES` source). The
binding is **validated against the contract**: every mapped key must be a real field of the object.

## Generation invariants (what keeps the mix honest)

1. **Generated files are sacrosanct** — every emitted file carries `@generated … DO NOT EDIT`, is
   **overwrite-only**, and CI fails on drift (re-emit must be byte-identical). Hand-editing a
   generated file is a build error, not a style nit.
2. **Hand-written code lives in exactly three places** — the kernel (forge + runtime stdlib),
   declared **escape-hatch modules**, and the **specs/ontology**. Nowhere else.
3. **Escape hatch = a hand-owned impl behind a stable, generated hook** — never code spliced into a
   generated file. The generator emits the call site + trait; a human/LLM fills the impl in a
   separate hand-owned module with its own tests. Keeps "the 10%" isolated and re-generation safe.
4. **LLM output lands in a spec or an escape-hatch module — never in the generated path.**

## Deterministic ÷ LLM — the decision checklist
For any unit of work, in order:
1. Derivable from the spec? → **generate** (extend the forge if the spec has it but the emitter doesn't).
2. Missing only a spec facet? → **add the facet** (LLM may draft; sieve + human freeze), then generate.
3. Outside the DSL's expressible grammar? → **escape hatch** (LLM may synthesize; tested + isolated).
4. About *whether the spec is right*? → **human/LLM review + tests** (never generated away).

## Loop metrics (so refinement is measurable)
- **Marginal hand-code per contract** (→ 0) — non-generated lines a *new* contract adds.
- **Generated coverage** — % of a spoke's serving code emitted by the forge.
- **Escape-hatch count + size** — stays small; growth signals a missing facet (grow the DSL, not the hatch).
- **Regen determinism** — re-emit is byte-identical (the golden gate).
- **Spec-conformance pass-rate** — SHACL sieve + contract tests green before any merge.

## Consequences

**Good**
- Marginal hand-code per contract → 0; output is byte-identical, drift-free, and multi-target.
- LLM contributions become **durable spec**, not throwaway code — captured, reviewable, regenerable.
- The platform **self-improves** under governance (the loop).
- **Patent-distinct** from EnterpriseWeb by construction (AOT vs runtime).

**Bad / risks**
- The **ontology becomes the critical asset** — it must be governed, versioned, and validated (the sieve does this; ARC-ADR-016/019).
- The **generator + runtime stdlib is a hand-maintained kernel** — a compiler you must maintain. This is the deliberate fixed cost.
- **DSL-creep:** an over-broad spec language becomes a general-purpose language (then "writing the spec" ≈ "writing the program"). Mitigation: keep the DSL to the 90% common shapes; keep the escape hatch **narrow and explicit**.
- **Generation ≠ correctness:** the forge faithfully compiles a wrong spec. Spec review + tests are the correctness guarantee and never disappear — they move *up* to guard the specs.
- **LLM-loop safety:** proposals must pass sieve + tests + human freeze; the loop never auto-merges un-validated generation.

## Phased roadmap

- **P0 (done):** forge multi-target emit; types generated; first live transport (DBOS/Postgres) behind the planner.
- **P1 (next):** **binding facet** → generate per-backend queries + row→object mappings (turn the hand-written transports into generated ones). Sketch:
  ```yaml
  # binding facet (an ontology decoration), per data object × backend
  KnowledgeSourceData:
    postgres:
      relation: knowledge_source
      columns: { source_id: src_id, display_name: name, provider_ref: provider, state: status }
    arcadedb:
      vertex: KnowledgeSource
      projection: { source_id: cid, ... }
  ```
  → forge emits the `SELECT`/SPARQL/AQL + the row decoder; the protocol driver stays in the stdlib.
- **P2:** policy facet → generate routes/handlers + RBAC; externalize planner config (capabilities/cost) as a facet.
- **P3:** generate conformance / drift / live tests from the contract + bindings.
- **P4:** the LLM elaboration **loop** (heartbeat-driven), with metrics (marginal-hand-code, generated-coverage, escape-hatch count).
- **P5:** generate state-machine transition guards + effects from the state facet + hyperedges.
- **Ongoing:** maintain the kernel (forge + drivers + planner); keep the escape hatch narrow; govern via the sieve + ADRs.

## More information
- [ARC-ADR-016](ARC-ADR-016-ontology-representation-reification-hyperedges.md) — the hypergraph (reification + hyperedges) this compiles from.
- [ARC-ADR-029](ARC-ADR-029-agentarmy-forge-codegen-container.md) — the forge (the compiler).
- [ARC-ADR-019](ARC-ADR-019-ontology-reasoning-layer.md) — the sieve (the conformance gate in the loop).
- backend-core `docs/adr/0001-universal-data-adapter.md` — the UDA + the Rust serving path the Factory hydrates.
- This session: `rust-api-v2/uda.rs` (planner + first live transport), `rust-api-v2/contracts/gen_data_objects.py` (the json→forge bridge), `agentarmy-forge/scripts/forge/emitters/rust.py` (the Rust emitter).
