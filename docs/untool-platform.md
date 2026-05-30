# Untool.ai — Platform Brief (for AI agents)

> **Read this first if you are an agent working anywhere in this fleet.** It is the
> canonical orientation to *what we are building* and *why*. It is deliberately short;
> it routes you to the authoritative ADRs, labs notes, and live docs for depth. Where
> this brief and an ADR disagree, the **ADR wins** — and please flag the drift.
>
> Status discipline: this brief separates **built** from **planned** explicitly. Do not
> claim a capability is shipped unless the ledger below (or the cited ADR/contract) says so.

---

## TL;DR — the 60-second model

**AgentArmy** is the *foundry*: a GitHub-native, agent-driven template (this hub repo) that
manufactures and governs **spoke** repos. **Untool.ai** is the *product* the foundry builds —
an **ontology-first, model-driven, agentic data platform**.

The one bet everything rests on:

> **One canonical model** describes the platform's objects, relationships, scenarios, policy,
> and projections. Everything else — C# contracts, ArcadeDB schema, OpenAPI, agent tools, the
> ontology itself — is a **projection** of that model. **Code is disposable; the model is the asset.**
> *(`obsidian/labs/AgentArmyLabs/vision/Model-Driven Platform.md`)*

The deeper philosophy — the reason this exists in an agent world:

> **Proof, not plausibility.** "An LLM that is the arbiter of truth will always drift toward
> plausibility. The **structure of the system, not the prompt, must guarantee correctness.**"
> *(ARC-ADR-032)* — Agents **propose**, the runtime **disposes**, **evidence proves**.

This is the exact inverse of emergent-schema tools (e.g. RushDB push-JSON-infer-types). We do not
infer meaning from data shape; we derive data from a certified model, and we let nothing into the
canonical graph that hasn't passed a machine proof.

---

## AgentArmy (foundry) vs Untool.ai (product)

| | **AgentArmy** (this hub) | **Untool.ai** (the product) |
|---|---|---|
| What it is | Meta-template: workflows, agents, governance, contract registry | The model-driven data platform built *with* the foundry |
| Deliverables | `.github/workflows/`, `.claude/agents/`, `docs/`, `templates/*-image/` | Spoke implementations: `frontend-core`, `middle-core`, `backend-core` |
| Mental model | "A platform for making platforms" | "Make the tool disappear" — a thin lens over a typed model |
| You are here if… | editing templates, ADRs, fleet tooling, agent packs | implementing a layer (UI / API / worker / ontology) |

Spokes integrate **only through versioned contracts** (the hub owns the inter-layer surface) —
never by importing each other's private code. The registry is [docs/contracts.md](contracts.md).

---

## The brand: "make the tool disappear"

The product identity (`frontend-core/docs/brand/UNTOOL.md`) is a design philosophy, not feature copy,
and it is load-bearing for every UI/UX decision:

> "The point of a tool is not the tool. It is the work… the 'un' is active. Like unlock, unfold,
> uncover. **untool.ai — make the tool disappear.**"

Heritage: Heidegger (*ready-to-hand*), Tufte (data-ink, small multiples), Dieter Rams ("as little
design as possible"). Voice = **calm, precise, useful**. Wordmark is lowercase `untool.ai`. This
aligns with the architecture: the UI is an honest lens over the model, never the product itself.

---

## Architecture at a glance

### 1. The model-driven core — one model, many projections

A single source model (`model.yaml` today; an OWL-shaped RDF vocabulary increasingly) is projected,
**never hand-edited**, into many targets: **C#** contracts (`*.g.cs`), **F#** IR + projection
functions, **OWL/SHACL**, **ArcadeDB** schema, **OpenAPI**, **agent tool-offerings (MCP)**,
**Agent Skills** (`SKILL.md`), TypeScript/Zod + Python/Pydantic clients, and the human-facing
Obsidian ontology. The make-or-break invariant: **structure is compiled; behavior wiring is
late-bound** — generated code is disposable (`*.g.cs`, `DO NOT EDIT`); hand-authored behavior lives
in partial classes / handlers, never in generated files. The headline risk is **projection drift**
(any hand-edited target collapses the "single source" claim); CI drift-gates enforce it.

### 2. Two pipelines (do not confuse them)

- **A — the data → ontology *authoring* loop** (ARC-ADR-030 / -032; **built & proven live**):
  `source (Tavily/file) → FRAME → PROPOSE (Cerebras, into the holographic graph) → SIFT (L1–L4) →
  REPAIR (≤K rounds) → SNAP (Fuseki sieve + competency questions) → CANONICAL graph → snapshot → forge`.
  The LLM only **proposes inside the box**; acceptance is a proof ladder, not LLM confidence.
- **B — the ontology → code *compiler*** (north-star; spine built, deep pieces pending):
  `OntoUML/UFO model → canonical IR → {OWL2, SHACL, C# hypergraph runtime, ArcadeDB persistence,
  PROV-O, (planned) Alloy/Z3}`.

### 3. The sieve, and the holographic ↔ canonical split (critical)

- **Holographic graph** = the **working/staging** LPG in ArcadeDB. Each candidate node carries the
  *whole context needed to judge it* (provenance, dual gUFO+BFO classifications, per-level validation
  status, repair count, lifecycle `state`). **Quarantine is a `state` here**, not a separate store.
- **Canonical graph** = **Fuseki RDF** — the authoritative semantic store. Material crosses
  holographic → canonical **only via the sieve** (`templates/fuseki-ontology-image/scripts/sieve.sh`:
  SHACL re-check; loads to Fuseki only on `sh:conforms true`, else exits non-zero).
- **Rule:** *"Do not make ArcadeDB 'be' the ontology. ArcadeDB proves nothing about semantic
  correctness."* (ARC-ADR-032). Validation is layered because each tool proves a different thing:
  L1 JSON-Schema · L2 OntoUML anti-patterns · L3 OWL reasoner (gUFO **∧** BFO must agree) · L4 SHACL ·
  prod sieve · competency questions.

### 4. The hypergraph runtime

An in-memory C# object graph (`ModelObjectGraph`) with **schema-validated** edges (`CanRelate`).
N-ary relations are modeled as **reified relators with role-binding edges** (*hyperedge-as-vertex*,
ARC-ADR-016) — bitemporal + PROV-O metadata lives **on the relator**. A reified relator is a **holon**:
a relation with its own identity/lifecycle (a *whole*) that can itself play a role in a further relator
(*nested reification* — a *part*). Nested relators form a **holarchy**, and that is the substrate for
**dynamic skill acquisition** (below): because capability is modeled *on* objects, an agent can acquire
skills by querying the graph rather than loading a static pack. Today this is **generated schema
metadata**; the *live* runtime still stores binary edges. An **F# functional core**
(ARC-ADR-033) makes correctness a *type*: `SiftOutcome = Snapped | Quarantined`, with `FS0025`
exhaustiveness as a build error — "snapped, not plausible" enforced by the compiler, not tests.
**Microsoft GraphEngine / Trinity / TSL is deliberately OUT** (kept as the IKW parallel track); the
only hedge in code is dual gUFO+BFO grounding in the F# IR, keeping a future BFO/CCO projection open.

### 5. Evidence & governance as primitives

- **Evidence:** nothing is "Done" without an `evidence-pack` — *evidence-driven, not just test-driven*.
  Determinism makes it reproducible (same model + inputs → identical evidence). `evidence-pack` +
  `decision-record` = the audit/trust backbone.
- **Governance is modeled, not bolted on:** DMN (decisions/routing/gates) + SHACL (valid-shape
  constraints) live *alongside* objects and scenarios. *"You can only safely let agents act if the
  rules are explicit, enforced, and evidenced."* (`vision/Governance in the Model.md`)

### 6. The agent access surface — **MCP, governed by an abstraction layer**

This is the part most easily misremembered. The **governed agent path is MCP tool-offerings**, not
GraphQL:

- Agents invoke only `mcp_eligible` **`tool-offering`s** — modeled, governed, evidenced scenarios.
  *Agents don't touch ArcadeDB or raw capabilities.* Surfaced via the **A2A + MCP agent gateway**
  (ARC-ADR-028, `/a2a/v1/`).
- The **abstraction layer** (ARC-ADR-036) is an **MCP-exposed anti-corruption / canonical-model
  meta-service** (Abstract / Validate / Vend), live at `mcp.untool.ai/abstract` with tools
  `abstract_schemas` + `build_adapter`. Its "snapped, not plausible" gate (coverage / confidence-floor
  / type-compat / round-trip / no-collision) **is** the "clean paths to certified data" guarantee.
- **GraphQL's real role:** (a) a middle-core `/graphql` *in-memory-graph read convenience* (not in the
  hub template, **not a registered contract**), and (b) a **planned human/dev product API**. It is
  *not* the governed agent surface and *not* the abstraction API. (A third "GraphQL-ish" thing is just
  CopilotKit's internal SSE runtime, ARC-ADR-007 — unrelated.)
- **OpenAPI/REST** is the inter-layer plumbing; the browser reaches the platform through a same-origin
  **BFF** that injects JWT server-side (ARC-ADR-002), with **no LLM key in the browser** (ARC-ADR-003).

### 7. The monetization spine

> "Expose capabilities as **MCP tools behind HTTP-402 / x402**… agents that pay agents."
> *(`labs/API Strategy — Internal, External, Open & Monetized.md`)* — Open-core line: *"open the
> recipe… sell the kitchen."* Named threat: **Denial of Wallet**.

### The runtime object model (middle-core)

Business objects name **ontology concepts, not records**. Lifecycle:
`scenario-template` (recipe) → instantiated as `capability-exercise` (a run) → produces an
`evidence-pack` + `knowledge-graph-snapshot`; evidence attaches to a `work-packet`, routed by a
`decision-record`; the scenario is safely exposed as a `tool-offering` (the MCP-eligible unit).
Knowledge substrate: `knowledge-source` → `knowledge-chunk` → `knowledge-graph-snapshot`.

---

## Built vs planned — the honesty ledger

| Capability | State | Anchor |
|---|---|---|
| Data→ontology sift-sort authoring loop (pipeline A) | **Built & proven live** | ARC-ADR-032; `docs/ontology-pipeline.md` |
| Fuseki sieve (`sieve.sh`), `doctor.py`, F# sift core | **Built** | `templates/fuseki-ontology-image/`, `tools/ontology-sift/` |
| Forge multi-target codegen (C#/TS/Py), deterministic, golden-gated | **Built (v0–v2)** | ARC-ADR-029; `templates/forge-image/` |
| Forge as standalone repo (`agentarmy-forge`) | **Built (seed)** | verbatim relocation, not yet diverged |
| Forge **displacing** middle-core's `modelgen` | **Not yet** — two generators coexist | ARC-ADR-029 |
| Forge vending (versioned artifact + flag-gated adopt) | **Planned (v2.5)** | ARC-ADR-029 |
| F# IR + projections, `FS0025`-exhaustive | **Built but not runtime-wired** (test-only ref) | ARC-ADR-033 |
| In-memory C# object graph (binary edges) | **Built** | `middle-core/.../Runtime/ModelGraph.cs` |
| True hyperedge-as-vertex in the **live** graph | **Not yet** (schema metadata only) | ARC-ADR-016 |
| Scenario runtime + evidence + transition guards | **Built (shape)** | `ScenarioRuntime.cs` + xUnit suites |
| Behavior **auto-derived** from the model | **Aspirational** — handlers hand-written; model drives order/guards | `vision/Codegen vs Interpreted.md` |
| OWL reasoning layer (type propagation, inverses, disjointness) | **Spike complete / proposed** | ARC-ADR-019 |
| Arrow/ADBC canonical value vocabulary | **Accepted** | ARC-ADR-009 |
| Abstraction/Validation meta-service (ADR-036) | **Partial** — Abstract+Validate built; Vend/MCP/board-sync pending | ARC-ADR-036 |
| Agent gateway (A2A + MCP) | **Producer shipped** | ARC-ADR-028 |
| Holonic unified board (UNTOOL MCP, `utl_*`) | **Proposed** | ARC-ADR-035 |
| GraphQL as a **governed** agent/contract surface | **Not built** (dev read-surface + planned human API only) | — |
| Microsoft GraphEngine / Trinity / TSL | **Out** (parallel track only) | `vision/IKW-GraphEngine (Parallel Track).md` |
| Real ArcadeDB persistence + bitemporal snapshots | **Deferred** | ARC-ADR-016 / -032 |
| Frontend: `/objects`, `/cockpit`, `/search`, `/ingest`, CopilotKit agent | **Built (working screens)** | `frontend-core` |
| Fleet Console UI (`/fleet`, 5 surfaces) + `fleet-console` BFF (`/api/fleet/*`) | **Built** | `frontend-core` (#105/#106) |
| Spoke `/diagnostics` → fleet-console contract shape (secret-safe) | **Built** | backend-core #146, middle-core #120 |
| Fleet admin agent — AG-UI/SSE, tools execute server-side | **Built (planner brain)** | `frontend-core` #106 |
| **Holon `/holons` projection** (hypergraph → ToolOffering[]) | **Built (slice, seed-backed)** | middle-core #121; Labs *Holonic Skill Acquisition* |
| **Runtime skill-acquisition** — agent acquires holons per-turn | **Built (surfaced, not executed)** | `frontend-core` #106 |
| Execute acquired affordances + the acquisition governance gate | **Planned** | Labs *Holonic Skill Acquisition* (open Qs) |
| Graph-backed holon projection (live ArcadeDB, not seed) | **Not yet** | ARC-ADR-016 / -032 |

---

## Vocabulary — use these words

- **Model** — the single source of truth (`model.yaml` / OWL-shaped RDF). Everything else is a projection.
- **Projection** — any generated artifact (C#, F#, OWL, SHACL, OpenAPI, ArcadeDB schema, SKILL.md, MCP tool).
- **Holographic graph** — the *staging* LPG in ArcadeDB; candidates self-carry their judgment context.
- **Canonical graph** — the *authoritative* Fuseki RDF store; only proven assertions live here.
- **Sieve** — the SHACL gate (`sieve.sh`) that promotes holographic → canonical.
- **Snap / snapped** — to pass the proof ladder into the canonical graph ("snapped, not plausible").
- **Quarantine** — a *state* on a candidate that failed proof; retained, never auto-promoted, re-drivable.
- **Relator / hyperedge-as-vertex** — a reified n-ary relation carrying bitemporal + PROV-O metadata.
- **Holon** — a concept that is at once a whole and a part: a reified relator has its own identity yet
  can play a role in a further relator. Capability is modeled *on* holons → skills are a face of an object.
- **Holarchy** — the nesting of holons; the part-whole structure a relator-holon's capability composes along.
- **Dynamic skill acquisition** — binding capability-holons projected from the live hypergraph at request
  time (the "Skills as a Projection" functor evaluated lazily over the graph), instead of a static pack.
- **Scenario / tool-offering** — a modeled capability; the `mcp_eligible` form is the agent-callable unit.
- **Evidence-pack** — the first-class proof output of every scenario run; "Done" requires one.
- **Abstraction layer** — the ADR-036 MCP anti-corruption meta-service (Abstract / Validate / Vend).
- **Foundry / spoke** — AgentArmy (the template) / a generated layer repo.

---

## Where the canonical truth lives

- **Vision (the "why"):** `obsidian/labs/AgentArmyLabs/vision/` — *Model-Driven Platform*, *One Model
  Many Projections*, *Codegen vs Interpreted*, *Governance in the Model*, *Evidence as a Primitive*,
  *Skills as a Projection*, *Holonic Skill Acquisition*, *Reification-and-Hyperedges*, *Scenarios as
  Agent Tools*, *UFO & GraphEngine Ecosystem*, *Prior Art*, *Open Questions and Risks*.
- **Architecture views (L0–L4):** `obsidian/labs/AgentArmyLabs/arch-views/` and
  `Architecture Atlas — Conceptual to Contract.md`.
- **Live pipeline doc:** [docs/ontology-pipeline.md](ontology-pipeline.md).
- **Decisions (the "what/how"):** [docs/decisions/](decisions/) — load-bearing for this brief:
  ARC-ADR-009 (Arrow CDM), -016 (reification/hyperedges), -019 (reasoning), -023 (container tiering),
  -028 (agent gateway A2A+MCP), -029 (forge), -030 (data→ontology ingestion), -032 (sift/sort loop),
  -033 (F# core), -034 (cross-repo contract distribution), -035 (holonic board), -036 (abstraction).
- **Contract registry:** [docs/contracts.md](contracts.md).
- **Brand:** `frontend-core/docs/brand/UNTOOL.md` + `VOICE.md`.

---

## How to work on this (guidance for agents)

1. **Change the model, not the projection.** If you find yourself hand-editing a `*.g.*` file, stop —
   edit the model and regenerate. Generated files are disposable by design.
2. **Prove, don't assert.** New ontology assertions must pass the sieve; new capabilities must emit an
   `evidence-pack`. "It looks right" is not acceptance here.
3. **Respect the holographic ↔ canonical boundary.** Propose into the staging graph; let the gate promote.
4. **Expose to agents only via `mcp_eligible` tool-offerings** through the gateway / abstraction layer —
   never wire an agent directly to ArcadeDB, Fuseki, or a raw capability.
5. **Integrate across spokes by contract** (registry + Postman mock), never by importing private code.
6. **Match the brand:** calm, precise, useful; the tool disappears.
7. **When the brief is stale, fix it** (and the ADR it cites). This doc is itself a projection of reality —
   keep it honest.
