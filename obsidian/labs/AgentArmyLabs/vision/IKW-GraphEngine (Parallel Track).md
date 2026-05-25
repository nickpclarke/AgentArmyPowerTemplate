---
tags: [vision, prior-art]
---
# IKW-GraphEngine — a parallel track

> [!abstract] What it is
> [InKnowWorks/IKW-GraphEngine](https://github.com/InKnowWorks/IKW-GraphEngine) is an enhancement of **Microsoft Trinity / Graph Engine (TGE)** — a distributed, strongly-typed **in-memory** key-value + graph compute engine — extended along the dimension we care about most: **semantics and ontology**. MIT-licensed, C#/C++, .NET 6–10, C# 10–13.

We have **direct contact with the builder (InKnowWorks)**, so this is a *sibling project to learn alongside*, not just cold prior art. The call: **keep building on OntoUML/UFO as our primary path, learn from GE in parallel, and design so we can offer *both* upper ontologies.** See [[#Offer both — one IR, two upper-ontology projections]].

## What GE brings
- **TSL** (Trinity Specification Language): schema → generated C# (a C++ generator emitting C# 13 is on their roadmap, ETA Fall 2025).
- **Native hypergraph / multigraph** modeling — `GraphNodeType: Hyper`, hyperedges connecting many nodes.
- **Ontology grounding**: BFO 2020, CCO, IAO, RO, SKOS, with A-Box / T-Box / R-Box reasoning over **BFO 2020 Common Logic** axioms + Microsoft's **Guan** logic-programming library.
- **LIKQ** (Language Integrated Knowledge Query): fast graph traversal with embedded lambda expressions; Prolog-like traversal planned.
- Distributed Symmetric RPC (TCP/IP + gRPC) for the in-memory runtime.

## Map to our plan
GE overlaps hardest with the parts of the [[Ontology-Pipeline]] we have **not built yet**:

| Our north-star concept | State today | GE offers |
|---|---|---|
| Hyperedge-as-object (reified n-ary relations) | ◻ not yet — flagged "do before persistence hardens" | ✅ native hypergraph/multigraph TSL modeling |
| C# in-memory graph runtime (`ModelObjectGraph`) | ✅ binary edges only, single-process | ✅ battle-tested **distributed** in-memory engine |
| Schema → deterministic generated C# | ✅ `model.yaml` → `*.g.cs` | TSL → C# (prior art for the codegen projection) |
| OWL/gUFO/SHACL reasoning control plane | ◻ `.ttl` referenced only | A/T/R-box reasoning + Guan logic engine |
| Agent access surface | GraphQL `/graphql` | LIKQ (lambda + planned Prolog traversal) |

## Friction (why parallel, not foundation)
1. **Upper-ontology fork.** We author in **UFO / gUFO / OntoUML** (with SEON, gist, FIBO alignments); GE grounds in **BFO 2020 + CCO / IAO / RO**. These are *competing foundational lineages* — design-oriented (UFO/OntoUML stereotypes: kind/role/relator/phase) vs realist/applied (BFO + OBO-Foundry). Bridging is best-effort, not lossless.
2. **Reopens closed decisions.** GE is its own in-memory store with its own codegen DSL. Adopting it wholesale touches our **ArcadeDB-as-single-persistence** call and our **`model.yaml`-as-IR** call (TSL would be a second schema language → [[One Model, Many Projections|projection drift]], our #1 named risk). Same shape as the rejected **VelocityGraph / Orleans** calls in [[Ontology-Pipeline#Rejected alternatives]].
3. **Bus factor / maturity.** Self-described research project ("not an officially supported Microsoft product"); small fork; key codegen feature unshipped.
4. **Doesn't cover our spine.** Evidence / [[Evidence as a Primitive|PROV-O]], bitemporal event-sourcing, and deterministic-codegen guarantees get no treatment — those stay ours to build.

## Offer both — one IR, two upper-ontology projections
The clean way to "offer both" without forking the source of truth: **the upper-ontology alignment is just another [[One Model, Many Projections|projection]].** Keep one canonical IR (`model.yaml`, OntoUML-stereotyped) and emit **two alignment artifacts**:

- **gUFO / UFO projection** (OWL 2 DL) — our primary authoring + reasoning path (Level-3 reasoner target already in the pipeline).
- **BFO 2020 + CCO projection** (Common Logic / OWL) — the GE-compatible grounding.

> [!important] The payoff of dual projection
> The BFO/CCO projection is **exactly what GE consumes.** So the same model that runs our OntoUML world can be handed to the friend's engine as a reasoning/interop sidecar — OntoUML stays the design discipline, BFO becomes a real interop target instead of a fork. Authoring is single-source; only the *alignment* is dual.

> [!warning] This is best-effort, not a bijection
> UFO relators vs BFO relational qualities/roles, UFO anti-rigid `phase` vs BFO's lack of a phase stereotype — these diverge. Ship a documented **mapping table + divergence list** with the projections; don't pretend they round-trip losslessly.

## Concrete next step — a spike
Matches our `spike-researcher` / [[Prior Art]] build-vs-borrow pattern. Time-boxed:
1. Model one [[Scenarios|knowledge-drop]] relator (e.g. a `MitigationCase` with role bindings) in **TSL**, generate C#, and compare against our planned **hyperedge-as-object** representation + the LinkML/`model.yaml` path.
2. From the same IR element, hand-emit a tiny **BFO 2020 + CCO** alignment and confirm GE can reason over it (validates the "offer both" projection end-to-end).
3. Output: a build-vs-borrow recommendation for (a) reusing GE's hyperedge model and (b) standing up the dual upper-ontology projection.

Related: [[Model-Driven Platform]], [[Ontology-Pipeline]], [[Prior Art]], [[Open Questions and Risks]], [[Codegen vs Interpreted]], [[UFO & GraphEngine Ecosystem]].
