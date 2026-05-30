# untool.ai — Platform Functionality & Derived Ontology

> A reference for collaborators (incl. Claude Code) working on the platform. It states what the
> platform *does* and the *terminology we derived* to talk about it. The vocabulary here is not
> invented for the doc — it is the canonical concept set the platform's own surfaces already
> express (grounded in `contract/fleet-interface/api-interface.ttl`, ARC-ADR-032), plus the
> product surfaces built on top.

---

## 0 · Thesis

**The moat is the derivation, not the storage.** Most systems start from a hand-modelled schema.
We start from a *corpus* — unstructured prose, semi-structured docs, and structured schemas — and
**derive** an ontology from it, grounded in a foundational upper ontology. From that one derived
ontology we materialize, in lockstep, three parallel stores — a **knowledge graph**, a **vector
index**, and a typed **object model** — all queryable by the agent armies.

The pipeline, in our terminology:

```
Corpus ──▶ Ground ──▶ Derive ──▶ Materialize ──▶ { Knowledge Graph · Vector DB · Object Model }
 (mess)   (BFO/gUFO   (cosine     (one ontology)        the agent-queryable substrate
          + packs)    snap)
```

Everything downstream — the conversational swarm, the fleet ops — consumes that substrate.

---

## 1 · The ontology we derived (the terminology)

### 1.1 Foundations are Perspectives, not a dual-label

A concept is **not** "grounded twice" as if BFO and UFO were interchangeable coordinates. **BFO**
(realist reference ontology; ISO/IEC 21838 — *what exists*, for scientific interop) and **UFO / gUFO**
(a conceptual-modeling foundation — *how we conceptualize*) carve reality differently and are **not
trivially inter-mappable**: there is no turnkey UFO↔BFO mapper, and foundational alignment is an open
research problem (naively equating even superficially-identical top categories is logically unsatisfiable).

Each foundation is therefore held as a **Perspective** (DSRP — Distinctions · Systems · Relationships ·
Perspectives): **UFO is the authoring Perspective, BFO the realist-interop projection**. The
`MidLevelMapper` reads `mid:bfoUpper` and `mid:gufoArchetype` as **two Perspectives reconciled by
explicit per-concept commitments + a divergence registry** — where they genuinely differ (e.g.
UFO «role» ≠ BFO role; a UFO relator has no native BFO kind), the divergence is *recorded*, not forced.
See [ARC-ADR-038 — Foundations as Perspectives](../decisions/ARC-ADR-038-foundations-as-perspectives.md).

| Perspective | Roots / carving |
|---|---|
| **BFO** — realist projection | IndependentContinuant · GenericallyDependentContinuant · SpecificallyDependentContinuant · Occurrent |
| **UFO / gUFO** — authoring | Kind · Role · Relator · Mode · Event — carved by rigidity / sortality / identity (no BFO counterpart) |

### 1.2 Mid-level packs — the canonical concepts (the integration vocabulary)

Concepts cluster into **packs**. Each concept carries a label and **two Perspectives** — a BFO projection and a UFO/gUFO archetype.
These are the canonical targets every API surface maps onto (so `InvokeRequest`, `runAgentInput`,
and `ChatCompletionRequest` all resolve to the same concept).

> **Two Perspectives, not a 1:1 map.** The `BFO upper` and `gUFO archetype` columns below are two
> *Perspectives* on each concept, not interchangeable coordinates. Clean rows are correspondences that
> hold; irreducible differences (e.g. UFO «role» vs BFO role) live in the **divergence registry** —
> see §1.1 and [ARC-ADR-038](../decisions/ARC-ADR-038-foundations-as-perspectives.md).

| Pack | Concept | BFO upper | gUFO archetype |
|---|---|---|---|
| **Information Artifacts** | Agent | IndependentContinuant | Kind |
| | Tool | IndependentContinuant | Kind |
| | Skill | GenericallyDependentContinuant | Kind |
| | Document | GenericallyDependentContinuant | Kind |
| | EvidencePack | GenericallyDependentContinuant | Kind |
| **Agentic Process** | Invocation | Occurrent | Event |
| | ToolCall | Occurrent | Event |
| | Task | Occurrent | Event |
| | AgentState | SpecificallyDependentContinuant | Mode |
| **Provenance (PROV-O)** | Entity | GenericallyDependentContinuant | Kind |
| | Activity | Occurrent | Event |
| | prov:Agent | IndependentContinuant | Role |
| **Knowledge / Semantic** | KnowledgeChunk | GenericallyDependentContinuant | Kind |
| | KnowledgeSource | GenericallyDependentContinuant | Kind |
| | GraphSnapshot | GenericallyDependentContinuant | Kind |
| | Embedding | SpecificallyDependentContinuant | Quality |
| **Organization & Roles** | Organization | IndependentContinuant | Kind |
| | Authority | SpecificallyDependentContinuant | Relator |

### 1.3 Hyperedges (relations that bind 2+ concepts)

The object model is a **hypergraph**: an edge can incident on more than two concepts. The relations
that glue the canonical concepts:

| Hyperedge | Members |
|---|---|
| `routes` | Agent · Task · ToolCall |
| `invokes` | Agent · Tool · Invocation |
| `wasGeneratedBy` | Entity · Activity · prov:Agent |
| `ingests` | KnowledgeSource · KnowledgeChunk · Embedding |
| `proves` | ToolCall · EvidencePack · Entity |
| `memberOf` | prov:Agent · Organization · Authority |

**Hyperedges are holons.** A relation that binds 2+ concepts is *reified* — it becomes a first-class
concept (a gUFO **Relator**) with its own identity, lifecycle, and provenance, not just a line between
nodes. So it is at once a **whole** (a thing you can name, evidence, and query) and a **part** (it can
itself be a member of a further hyperedge — *nested reification*). A concept that is simultaneously
whole and part is a **holon**; the nesting of holons is a **holarchy**. The object model is therefore
not merely a hypergraph of *data* but a holarchy of *capability* — the basis for how the swarm
acquires skills (§3.4).

A holon lives in the **authoring (UFO) Perspective** (§1.1): it *is* the Relator. The realist (BFO)
Perspective has no native kind for a reified relation, so a holon is reconciled through the divergence
registry — *recorded*, not forced into a BFO category. The holarchy is thus a UFO-side structure that
the BFO projection observes but does not own.

### 1.4 DSLs (compatibility-gated by the packs present)

| DSL | Requires | Purpose |
|---|---|---|
| `api-interface` | Information Artifacts | map OpenAPI/AsyncAPI surfaces onto canonical concepts (ARC-ADR-032) |
| `AG-UI events` | Agentic Process | streaming run / tool-call event grammar |
| `model.yaml` | Knowledge/Semantic | project the ontology into an ArcadeDB schema |
| `SHACL shapes` | Provenance | constraints + integrity over the derived graph |
| `hyperquery` | Knowledge + Agentic | query language over the hypergraph object model |

### 1.5 Epistemics (how the platform talks about truth)

These terms are pervasive and non-negotiable in the product language:

- **Verdict** — `passed | failed | inconclusive | pending | running`. *Done is a verdict the system
  emits, never the click that requested it.*
- **EvidencePack** — the signed proof-of-work for any capability-exercise: artifact refs (each
  hashed) + a **provenance** chain (`model@N → scenario@V → exercise (agent)`). Schema `evidence-pack@2.1`.
- **candidate-new** — a derived concept whose best cosine to the scaffold is below threshold
  (< 0.45). It is surfaced, never force-fit; it becomes a candidate for a new canonical concept or
  a new bridge.
- **cosine** — the embedding similarity that drives every snap (concept → canonical, JSON field →
  fragment, surface concept → canonical). Confidence is always shown, never hidden.
- **presence-only secrets** — secret *values* never cross the wire; only `present` + `source`.
- **holon** — a concept that is at once a *whole* and a *part*: a reified relation (Relator) has its
  own identity yet can be a member of a further relation. **Skills are holons** — each carries an
  affordance, so a capability is a *face* of a domain object, not a hand-written pack. **holarchy** —
  the nesting of holons (a relator playing a role in another relator); a capability composed from its
  participants' capabilities along role-bindings.

---

## 2 · The core capability — Corpus → Ground → Derive → Materialize

| Stage | Input | What happens | Output |
|---|---|---|---|
| **Corpus** | unstructured + semi + structured | intake of all data kinds (PDFs/transcripts; ADRs/READMEs; OpenAPI/AsyncAPI/TTL/DDL) | a signal pool |
| **Ground** | — | choose foundation (BFO/gUFO), stack compatible mid-level packs + DSLs | the scaffold |
| **Derive** | corpus + scaffold | surface concepts, snap each onto the scaffold by **cosine**, flag **candidate-new** | a grounded ontology |
| **Materialize** | the ontology | project in lockstep | graph + vectors + object model |

The Derive stage *is* the schema-abstraction tool (`app/ontology/schema_abstract.py`) made
visible — the same mapping that produced `FLEET-INTERFACE-MAP.md`.

---

## 3 · Products (functionality + use cases, in our terms)

### 3.1 Crucible — *corpus → ontology* (flagship)
Runs the full four-stage pipeline. **Use it when** you have a domain to model from scratch: point it
at a messy corpus and get a grounded, materialized ontology. Nodes in the resulting hypergraph are
explorable — clicking a concept reveals its grounding, the **corpus evidence** bound to it (raw
concept · source · cosine), its hyperedges, and where it materialized.

### 3.2 Refinery — *JSON → types* (light tier)
No corpus, no derivation. Paste structured JSON; each field is **snapped to the nearest published
fragment** (e.g. `agent → iface:Agent · IAO`, `birthDate → TimeInstant`) with a confidence; unknowns
become **candidate types**. Output is a typed schema + object model. **Use it when** you already have
structured data and just want it typed against fragments you already own. Has a *promote-to-Crucible*
path when JSON alone is insufficient.

### 3.3 Registry — the purveyor of ontologies (admin)
The supply side. Admins **ingest** any ontology or standard, **assay** its BFO/gUFO alignment, and
**bridge** the gaps with versioned plugins — so the whole bridged ecosystem becomes snappable. From
the bridged set, a **harvesting pipeline** can be derived across any domain.

- *Native* (snap directly): CCO, IAO, GO (BFO), OntoUML (UFO).
- *Bridged* (plugin maps foreign class → BFO upper + gUFO archetype): PROV-O, FIBO, FHIR, FOAF,
  schema.org, SKOS, Dublin Core.
- *Candidate* (bridge in progress): Gist.
- *Unbridged* (no semantics — route to Crucible): raw OpenAPI / JSON-Schema.

Bridges are **versioned plugins**: author the alignment once, every downstream derivation inherits it.

### 3.4 Workspace — conversational swarm intelligence
Where the materialized substrate pays off. A user states a **purpose**; agents **assemble** around the
ask, each carrying a **domain, skills, and abilities** drawn from the ontology (Router, Cartographer,
Prover, Archivist, Sentinel, Synthesist). The swarm **profiles the work** (intent · domain · who you
are · what it grounded on), then responds with per-agent contributions and a synthesized answer whose
every claim carries a **SourcePill** (provenance), signed by Prover. Work shares across **human +
machine networks**. Scoped per **org › instance** (instances align to fleet environments).

Those skills are not a static pack. Each agent **acquires** its capability-holons at request time — a
*runtime projection* of the live hypergraph: the same projection that emits `SKILL.md` / MCP tools at
build time, evaluated lazily over the graph for the purpose at hand. Because holons nest (§1.3), a
relator-holon's capability **composes** from its participants' — so new abilities *emerge* from the
graph's shape rather than from new code. This is the difference between a skills *catalog* and a
**fountain of domain expertise**: the swarm gets more capable as the derived ontology gets richer,
with no new packs to write. *(Emerging: the projection is proven end-to-end on a seed holarchy today;
the fountain widens as the canonical graph fills — see the honesty note in the platform brief.)*

### 3.5 Fleet Console — ops & diagnostics (internal, phone-first)
Monitors the hub-and-spoke fleet that runs all of the above. Surfaces: **Fleet** (layer health +
live SLO probes), **Rig** (capability-exercise + endpoint-probe runner with evidence packs), **Uptime**
(90-day availability + incidents), **Pulse** (DORA, metered-gateway spend, container tiers, secrets),
**Agent** (admin chat over the fleet tool suite). Environment-aware: `local-dev / cloud-dev / cloud-prod`
(prod read-only). Has a vendored endpoint contract (`fleet-console.contract.ts`).

---

## 4 · The materialized substrate (one ontology, three stores)

| Store | Engine | Role | The armies use it for |
|---|---|---|---|
| **Knowledge Graph** | ArcadeDB (hypergraph) | typed, traversable | multi-hop reasoning |
| **Vector DB** | parallel index | every node embedded in lockstep | semantic recall over the *same* ontology |
| **Object Model** | typed SDK + DSLs | generated typed objects | the armies call it directly |

The invariant: **all three are projections of one ontology** and stay in lockstep — a graph node, its
vector, and its object class are the same concept seen three ways.

---

## 5 · The fleet (where it runs)

Hub-and-spoke: **AgentArmy** (hub — contracts, agents, skills, hub→spoke authority) over three spokes —
**frontend-core**, **backend-core**, **middle-core**. Each spoke exposes `/diagnostics`
(dependencies + secret *presence*). Surfaces speak a shared event grammar (**AG-UI**), and integrate
through the canonical vocabulary above. Cost is governed by a **metered gateway** (x402 / HTTP-402) —
a Denial-of-Wallet watch that shows spend *before* execution.

---

## 6 · Use-case catalog (in derived terminology)

1. **Model a new domain** → *Crucible*: Corpus → Ground(BFO + packs) → Derive → Materialize.
2. **Type an existing feed** → *Refinery*: JSON → fragment snap → typed object model.
3. **Onboard a standard** → *Registry*: ingest → assay alignment → author a **bridge plugin** → publish fragments.
4. **Bridge a non-BFO ontology** → *Registry*: author `untool/bridge-*@v` mapping foreign class → BFO upper + gUFO archetype; gaps tracked as `candidate-new`.
5. **Harvest a domain** → from the bridged set, derive a harvesting pipeline; outputs land as published fragments.
6. **Answer a purpose with evidence** → *Workspace*: assemble swarm → profile work → synthesize answer with **SourcePills** + signed **EvidencePack**.
7. **Run a capability-exercise** → *Fleet · Rig*: emit a **Verdict** + an EvidencePack (artifacts + provenance).
8. **Prove an outcome** → `agent-route-and-prove`: route intent → tool, then attach an outcome-proof.
9. **Watch spend** → *Fleet · Pulse*: metered gateway vs cap, by tool / by agent.
10. **Acquire a skill from the graph** → *Workspace*: an agent queries the hypergraph for the
    capability-holons relevant to a purpose and **binds them for the turn** — runtime skill-acquisition,
    no pack to install. Relator-holons bring their composition (the participants they fold together).

---

## 7 · Glossary (canonical terms)

- **Corpus** — the heterogeneous input (unstructured · semi-structured · structured) an ontology is derived from.
- **Ground** — bind a derivation to a foundation (BFO/gUFO) + mid-level packs + DSLs.
- **Derive** — surface concepts and snap them onto the scaffold by cosine.
- **Materialize** — project one ontology into graph + vectors + object model.
- **Fragment** — a published, snappable canonical concept (the unit the Registry purveys).
- **Bridge** — a versioned plugin mapping a foreign ontology's classes onto BFO/gUFO.
- **Capability-exercise** — a named, repeatable test of a platform capability that emits a Verdict + EvidencePack.
- **EvidencePack** — signed proof-of-work: hashed artifact refs + provenance chain.
- **Verdict** — passed / failed / inconclusive / pending / running. Done is a verdict, not a click.
- **candidate-new** — a sub-threshold concept surfaced rather than force-fit.
- **Swarm** — agents assembled around a purpose, each carrying ontology-derived domain/skills.
- **Holon** — a concept that is at once a whole and a part (a reified relation with its own identity
  that can be a member of a further relation). Skills are holons: a capability is a face of an object.
- **Holarchy** — the nesting of holons; the part-whole structure a relator-holon's capability composes along.
- **Skill-acquisition (dynamic)** — binding capability-holons projected from the live hypergraph at
  request time, instead of loading a static skill pack.
- **Hyperedge** — a relation incident on 2+ concepts in the object model (when reified, a holon).
- **Hub / Spoke** — AgentArmy (authority) over frontend-/backend-/middle-core.
- **Metered gateway** — x402 spend governance; the Denial-of-Wallet watch.

---

*Surfaces this maps to: `Crucible.html`, `Refinery.html`, `Registry.html`, `Swarm Workspace.html`
(product) and `fleet/Fleet Console.html` (ops). Contract: `fleet/contract/fleet-console.contract.ts`.*
