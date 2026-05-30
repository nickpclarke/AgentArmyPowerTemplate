---
tags: [vision, ontology, middle-core, agents]
---
# Holonic Skill Acquisition over the Object Hypergraph

> [!abstract] The thesis
> An agent's capabilities should be a **runtime projection of the live reified hypergraph**, not a static pack. middle-core serves the object graph; each domain object — and each **relator** (reified n-ary relation) — is a **holon**: simultaneously a usable capability *and* a part that composes into larger capabilities. The agent **acquires skills on demand** by querying the graph for the holons in scope, projecting each to a `tool-offering`, and binding them for the turn. Domain expertise stops being authored and starts being *grown*.

This is the third corner of a triangle the fleet already drew two sides of:

- [[Skills as a Projection]] — a `tool-offering` in `model.yaml` projects to `SKILL.md` / MCP tool / OpenAPI / UI. **Build-time.** Versioned, evidenced, generated.
- [[Reification-and-Hyperedges]] — n-ary relations become first-class **relator vertices** in ArcadeDB; relators can *play roles in other relators* (nested reification).
- **This note** — close the loop: project skills at **runtime** from the **live graph**, with relators-as-holons as the unit of composition.

## Why "holon," precisely

Koestler's holon = a whole that is also a part. Our reified hypergraph already *is* holonic and we didn't plan it that way:

- A **relator vertex** (e.g. `ingest-evidence` binding source + chunks + exercise + evidence) is a *whole* — it has identity, lifecycle, bitemporal validity, provenance.
- That same relator can **play a role in a further relator** ([[Reification-and-Hyperedges]], TypeDB row) — so it is also a *part*.
- A holon's **affordances** (what you can *do* with it) are its `tool-offering` projection. The capability and the object are the same entity viewed two ways.

So a **capability-holon** = an object/relator that carries both its data *and* its affordances, and composes recursively via role-bindings. The "holarchy" is the role-binding DAG over the graph.

## The mechanism (request-time)

```
intent ──▶ holon.query(intent, env-scope)         # middle-core, over ArcadeDB
        ──▶ {holons}  (relevant objects + relators, ranked)
        ──▶ project each → tool-offering            # the Skills-as-a-Projection functor, at runtime
        ──▶ agent binds the offerings for THIS turn # dynamic acquisition (MCP tool-factory, #347)
        ──▶ execute ──▶ evidence-pack proves it     # capability-exercise / Evidence-as-a-Primitive
```

The fleet-console agent we just shipped (`/api/fleet/agent/chat`) has a **static** tool list (`fleet.status`, `probe.run`, …). That's the degenerate case — a fixed holon set. The evolution: its tool list becomes whatever `holon.query` returns for the user's intent in the current env. Same AG-UI wire shape; the *suite* is now graph-sourced.

## The category-theory lens (kept top-of-mind, per ADR-032/033 lineage)

- **Skills-as-a-Projection is a functor** `P : Model → CapabilitySurface`. [[One Model, Many Projections]] is the statement that *many* such functors share one source. Runtime projection is the same functor evaluated lazily on the live graph instead of eagerly at build.
- **Holonic composition is the relator-plays-role recursion** — an **operad** of capabilities: a holon's affordance can be *composed* from sub-holons' affordances along role-bindings. Resolving an intent into a bound tool-suite is a **catamorphism** over the holarchy (fold the part-whole tree → one capability set).
- **Projection commutes with composition** is the law worth enforcing: `P(compose(h₁,h₂)) ≅ compose(P h₁, P h₂)` — i.e. acquiring the skill of a composite holon equals composing the skills of its parts. If that congruence holds, dynamic acquisition is *sound*: no capability appears that the graph didn't license.

## Why this beats static skill packs

| Static skill pack | Holonic runtime projection |
|---|---|
| Authored + curated by hand | **Grown** from the modeled/ingested graph |
| Drift between pack and reality | Capability *is* a view of current reality (bitemporal) |
| Flat list, global | **Scoped** to intent + env + holon-neighborhood |
| Adding a skill = write + publish | Adding a skill = a holon enters the graph |
| No provenance on "why this skill" | Every offering traces to its holon + evidence-pack |

## Smallest end-to-end proof (additive, doesn't disturb the shipped agent)

1. **Seed graph:** reuse the one `ingest-evidence` relator from the [[Reification-and-Hyperedges]] first slice (already binds source/chunks/exercise/evidence).
2. **`GET /holons?intent=&scope=` on middle-core** — return the relevant holons as **`ToolOffering[]`** (the *exact* shape already in `contract/fleet-console/fleet-console.contract.ts`). One projection function, evaluated on the live graph.
3. **Dynamic-acquire in the fleet agent:** before planning, the agent calls `holon.query`, merges the returned offerings into its tool suite for that turn, and streams them as the same `toolCall*` AG-UI chips. *No change to the wire protocol — only the source of the suite.*
4. **Prove it:** the turn emits a `capability-exercise` verdict + evidence-pack (the loop is already specified). Done is the verdict, not the dispatch.

Leave the static fleet tools in place as the fallback suite; the graph-sourced offerings are *additive*. Migrate fully once the round-trip is proven — same discipline as the reification slice.

## Open questions

- **Governance of acquired skills** ([[Governance in the Model]]): a runtime-projected tool can *act*. What gates a holon's affordance from becoming a callable tool — model-declared `mutating` + env read-only (we already gate this in the BFF), plus an allowlist by holon type? Acquisition must be **monotone in authority** (acquiring never escalates).
- **Ranking `holon.query`**: embedding similarity over the chunk graph, role-binding distance, or a learned policy? Start with graph-neighborhood + type match; defer learned ranking.
- **Where does projection run** — middle-core (owns the graph, allowed inference) projecting to `ToolOffering`, with frontend-core/BFF binding them? That keeps ARC-ADR-003 intact (the [[Skills as a Projection]] functor lives next to the graph).
- **Holon identity vs. version**: a bitemporal relator has many versions — which version's affordance is acquired? (Lean: "as-of now," with the relator's `recorded_at` on the evidence-pack.)
- **Operadic soundness**: do we actually enforce `P(compose) ≅ compose(P)`, or just trust it? A generator-time check (the projection congruence) is the analogue of the ORM ≥(n-1) smell check from the reification slice.

## Relationship to what's built

- The **MCP registry + reconcile + tool-factory** (#347) is the delivery rail: a holon's projected offering registers as an MCP tool and reconciles — "add-and-use loop" (project memory: *Serve capabilities via MCP*).
- The **fleet-console agent** (`/api/fleet/agent/chat`, just shipped) is the first consumer that could swap its static suite for `holon.query`.
- **`capability-exercise` + Evidence-as-a-Primitive** close the proof loop so a dynamically-acquired skill is still evidenced.

Related: [[Skills as a Projection]] · [[Reification-and-Hyperedges]] · [[One Model, Many Projections]] · [[Ontology-Pipeline]] · [[Scenarios as Agent Tools]] · [[Governance in the Model]] · [[Evidence as a Primitive]].

## Sources (holon / operad / dynamic capability lineage)
- Koestler, *The Ghost in the Machine* (1967) — holons & holarchy.
- Guizzardi et al., *Relations in Ontology-Driven Conceptual Modeling* (2019) — relators as endurants (the holon substrate).
- Leinster, *Higher Operads, Higher Categories* — operadic composition (capability-of-parts → capability-of-whole).
- TypeDB, *The case for a structured hypergraph* — relations playing roles in relations (nested holons).
- Anthropic Agent Skills / MCP tool specs — the `tool-offering` projection target (standard, real).
