---
tags: [vision, platform, data, ontology, pace-layering]
track: vision
---
# Pace-Layering & the Dreaming Ontology

> **Status:** living design note — the conceptual frame behind [ARC-ADR-038](https://github.com/nickpclarke/AgentArmy/blob/main/docs/decisions/ARC-ADR-038-pace-layered-projection-and-graduation.md). Sits under [[Ontology-Pipeline]] (the compiler) and [[Reification-and-Hyperedges]] (the representation); it adds the *down-projection*, the *operational frontier*, and the *slow-layer evolution model*.

> **One-line thesis** — The ontology is the **slow** layer (meaning, rules, rigor — changes rarely); the LPG is the **fast** layer (operations, speed, dynamic metadata that needs *no* ontological rigor). *Fast learns, slow remembers; fast proposes, slow disposes.* The fast layer **notes drift and emergence**; the slow layer occasionally **dreams** it into clean structure.

## Pace layering, applied to meaning

Stewart Brand's insight: a healthy system is built in layers that move at different speeds, loosely coupled, so the fast layers can innovate and absorb shocks while the slow layers provide constraint and memory. Map it onto the knowledge stack:

| Layer | Pace | Rigor | Holds | Changes by |
|---|---|---|---|---|
| Upper ontology (UFO / BFO) | geological | maximal | categories of being | ~never |
| **Domain T-box + rules** (OWL/SHACL) | **slow** | high, proof-gated | **meaning** — classes, relations, axioms, shapes | governed authoring (the ratchet / a dream) |
| Canonical A-box | medium | conforms to T-box | the facts | world events, ingestion ([ARC-ADR-030](https://github.com/nickpclarke/AgentArmy/blob/main/docs/decisions/ARC-ADR-030-data-to-ontology-ingestion-pipeline.md)) |
| **LPG canon projection** | fast | derived & enforced | speed-optimized *shadow* of the rules | re-projection |
| **LPG telemetry / metadata** | **fastest** | **none — dynamical** | **measurements of value & meaning-change** | continuous, GC'd |

> [!note] Coupling discipline — this is what makes pace layering *work*
> - **Down = constraint.** The slow layer projects its strict schema + rules; the fast layer *enforces* them on live data (data objects reinforce the rules). Only A-box crosses; T-box axioms stay slow.
> - **Up = a slow ratchet.** Only proof-gated, stable, high-value signal crosses upward into meaning. *Fast proposes, slow disposes.*
> - **Shear is buffered.** Fast churn must never whipsaw the slow layer — the telemetry layer *absorbs* the volatility; only durable signal propagates.

## The fast layer is semantic telemetry

The LPG's dynamic properties are not a junk drawer. Their job is to **measure the value of, and changes in, meaning** — to instrument *meaning-in-use*. There are three roles, with different lifecycles:

| Role of a fast property | Example | Graduates? | Function |
|---|---|---|---|
| **Operational** | cache hint, ACL, shard key, UI flag | never (GC'd) | pure ops — *noise* to the ratchet |
| **Measurement** | usage freq, centrality, drift score, SHACL-strain, observed cardinality | **never** — but **drives** the ratchet | the *control signal* |
| **Latent structure** | `ops:verified_by` (a foreign-key smell), a recurring qualified edge | candidate | the *payload* that may graduate |

> [!important] Why rigor-free is *correct*, not a shortcut
> A realist (BFO) reading confirms the instinct: `confidence`, `score`, `tenant`, `drift`, `usage` are **Information Content Entities about the record** (IAO) — *information about* the slow layer's meaning, not universals that carve reality. Putting `pagerank=0.7` into the T-box is a category error. So the measurements **belong** in the fast layer and must **stay** there: the pace boundary *is* an ontological boundary (domain WD vs IAO ICE). The fast layer is information *about* the slow layer.

### What "value" and "change" decompose into

- **Value of meaning** → *which meaning matters* (where to invest the slow layer; what to deprecate): frequency, traversal centrality, query participation, dependent-contract count, demand, cost-to-serve.
- **Change in meaning (drift)** → definition↔use divergence (observed vs declared cardinality/domain/range; **rising SHACL-strain** — the enforcement surface *is* the drift sensor), emergent structure (co-occurrence, latent subkind/role/phase clusters), sense drift / polysemy, participant-type shift, volatility / staleness.

## We just note drift and emergence

The fast layer does not *decide*, and need not even *nominate* aggressively. It **notices** meaning moving and **writes it down**. Whether a pattern is ever *harvested for attention* is a separate, optional, budgeted act. This single restraint sidesteps the whole class of over-eager auto-ontologising failures — there is no automatic promotion to go wrong; there is only observation, and occasional, deliberate consolidation.

> **Popularity nominates; classification decides.** A fast statistical signal may *flag* a candidate. Only the slow **ontological classifier** may assign a category (datum / intrinsic moment / relation / occurrent / ICE / admin). Letting a fast signal make a slow commitment is a *pace violation* — and the root cause of every anti-pattern the naïve ratchet would mint.

## The dreaming ontology

The slow layer mostly **sleeps**, and periodically **dreams**: OWL and the reasoners are *"an annealing, dreaming, graph-re-sparsifying thing."* Each poetic term lands on real machinery:

- **dreaming** → offline batch consolidation over an attention-selected *replay* of the noted drift/emergence (cf. the wake-sleep algorithm; complementary learning systems — hippocampus fast, neocortex consolidates).
- **annealing** → stochastic search with a *cooling schedule* over candidate restructurings (Kirkpatrick); the temperature lets it escape local minima before it settles.
- **re-sparsifying** → parsimony pruning — merge duplicate universals, drop redundant axioms, deprecate dead structure (synaptic homeostasis: sleep *downscales*; MDL compression of the graph).

```text
FAST (awake) ── note value + drift + emergence → time-series + hysteresis → (optional) harvest
        │ attention-selected replay
        ▼
SLOW (asleep) ── DREAM CYCLE
   harvest ─▶ heat / expand (entailment · recombination — denser with possibility)
           ─▶ cool / anneal (settle toward low energy: consistent + parsimonious + category-sound)
           ─▶ re-sparsify (merge dupes · prune redundancy · deprecate dead structure)
           ─▶ wake (re-project the cleaner, sparser canon DOWN)
```

> [!abstract] The energy under the metaphor
> Minimise **description length** (the most parsimonious axiomatisation) while maximising **explanatory coverage** (competency questions + harvested patterns), subject to **hard consistency + category well-formedness**. Drift is *prediction error*; the dream updates the generative model — the ontology — to reduce future surprise. It is free-energy minimisation on a cooling schedule.

What the dream model gives "for free":

- **Thrash resistance** — the cooling schedule *is* the hysteresis; temperature is the deadband. You consolidate periodically, you don't react to spikes.
- **Demotion / GC** — that's just the re-sparsify phase; pruning is a phase of sleep.
- **Category soundness** — the [[Reification-and-Hyperedges|UFO/BFO]] well-formedness rules stop being a checkpoint and *become the energy landscape*: relator-as-kind, occurrent-fossilised-as-continuant, duplicate universals are **high-energy states the anneal rolls away from**. The dream simply won't crystallise into ill-formed structure.

> [!warning] Dreaming is free; crystallisation is gated and recorded
> A dream may *imagine* any restructuring, but only **consistent, category-sound** configurations crystallise into canon — and every consolidation is itself a **PROV-O event** (this dream merged X,Y→Z, pruned W, because…). You keep the memory of what sleep pruned, or the system forgets its own history and you can't audit why meaning moved. And the sleeper must restructure slowly enough that the waking fast layer rebinds its CANON zone gracefully ([[Evidence as a Primitive|evidence]] + bitemporal, no whiplash). This is [ARC-ADR-032](https://github.com/nickpclarke/AgentArmy/blob/main/docs/decisions/ARC-ADR-032-ontology-sift-sort-authoring-loop.md)'s *propose/dispose*, lifted to whole-graph scale.

## What wakes the dreamer

The open knob is no longer "what drives promotion" — it is **what wakes the dreamer**:

- **clock** — sleep on a cadence;
- **pressure** — sleep when accumulated drift / free-energy crosses a threshold (sleep when *tired*);
- **attention** — sleep only when something spends the budget on a harvested pattern.

That schedule is the system's whole temperament. The current lean: **just note drift and emergence; harvest for attention** — observation-first, consolidation optional and deliberate.

## Related

- [[Ontology-Pipeline]] — the compiler (ontology → many projections); this note adds the down-projection + the frontier + the dream.
- [[Reification-and-Hyperedges]] — relator-vertex representation reused for CANON and for the relational graduation branch.
- [[Evidence as a Primitive]] — provenance/evidence is the substrate that makes drift measurable and dreams auditable.
- [[Governance in the Model]] — SHACL/DMN/decision-record; the strain signal lives here.
- [[One Model, Many Projections]] — the CANON zone is one more governed projection.
- [[Open Questions and Risks]] — projection drift, authoritativeness, governance capture.
- ADRs: [ARC-ADR-038](https://github.com/nickpclarke/AgentArmy/blob/main/docs/decisions/ARC-ADR-038-pace-layered-projection-and-graduation.md) (this decision), [ARC-ADR-016](https://github.com/nickpclarke/AgentArmy/blob/main/docs/decisions/ARC-ADR-016-ontology-representation-reification-hyperedges.md), [ARC-ADR-019](https://github.com/nickpclarke/AgentArmy/blob/main/docs/decisions/ARC-ADR-019-ontology-reasoning-layer.md), [ARC-ADR-030](https://github.com/nickpclarke/AgentArmy/blob/main/docs/decisions/ARC-ADR-030-data-to-ontology-ingestion-pipeline.md), [ARC-ADR-032](https://github.com/nickpclarke/AgentArmy/blob/main/docs/decisions/ARC-ADR-032-ontology-sift-sort-authoring-loop.md).
