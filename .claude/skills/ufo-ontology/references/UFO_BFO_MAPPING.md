# UFO → BFO/CCO — the interop projection (synthesis)

You authored in UFO/OntoUML (the design discipline). This file is how you **project** that model to **BFO 2020 + CCO** as an interop sidecar — the "offer both, one IR → two upper-ontology projections" design. The BFO-side mirror lives in `bfo-ontology/references/UFO_BFO_MAPPING.md`; keep the two in sync.

## First principle: best-effort, directional, lossy

- **BFO** is *realist* (carves reality; single inheritance; no modal meta-properties).
- **UFO** is *conceptual* (organized by rigidity / sortality / identity / dependence).

So projection **loses** UFO's modal information and **fans out** some UFO constructs into several BFO patterns. **Never claim a round-trip.** Always emit a **mapping table + divergence list** beside the projection (the pipeline rule).

## Projection table (UFO/OntoUML → BFO + CCO)

| UFO / OntoUML | BFO target (+ CCO mid-level) | Fidelity | Projection action |
|---|---|---|---|
| Endurant | Continuant (`BFO_0000002`) | high | direct. |
| Substantial / «kind» | Material Entity → Object (`BFO_0000030`); align to CCO (`cco:Person`, `cco:Organization`, `cco:Artifact`) | high | `is_a` under Object; reuse CCO where a universal exists. |
| «subkind» | `is_a` subclass of the kind's BFO class | high | direct subsumption. |
| «collective» | Object Aggregate (`BFO_0000027`) | high | members → `member_part_of`. |
| «quantity» | Material Entity (portion of matter) | medium | no BFO "amount of matter"; use material entity + parthood. |
| «quality» | Quality (`BFO_0000019`); reuse PATO | high | values → quality/PATO. |
| «mode» | Realizable Entity (`BFO_0000017`): Disposition (`BFO_0000016`) if realized in a process; else a quality-bearing SDC | medium | split by realizability. |
| **«relator»** | **choose one:** (a) Relational Quality (`BFO_0000145`); (b) bundle of interdependent Roles/Dispositions realized in one Process; (c) Process + IAO information content entity | **low — headline divergence** | pick per relator; **record the choice** in the mapping artifact. |
| «role» | Role (`BFO_0000023`) **borne by** the participant (via `bearer_of`/`has_role`), realized in a process | medium | restructure: UFO role-as-type → BFO role-as-borne-entity. |
| «roleMixin» | Role borne across multiple bearer kinds | low | non-sortal meta-property dropped. |
| **«phase»** | **no BFO stereotype** — defined class over a quality value, or a process stage | **low — headline divergence** | model the phase-defining quality/disposition; "in phase X" stops being type membership. |
| «phaseMixin» | as phase, spanning kinds | low | same gap. |
| «category» | higher universal over object kinds (abstract superclass) | medium | non-sortality dropped. |
| «mixin» | abstract superclass | low | semi-rigidity has no analogue. |
| «event» / Perdurant | Process (`BFO_0000015`) / Process Boundary (`BFO_0000035`); CCO Act/Event | high | instantaneous → boundary. |
| «situation» | configuration of continuants + SDCs at a time (no BFO category) | low | reconstruct via `exists_at` / process boundaries. |
| «type» (powertype) | OWL punning; no BFO category | low | BFO universals are first-order. |
| «datatype»/«enumeration» | `rdfs:Datatype` / value partition | n/a | data-level. |
| Mode: Disposition/Capability | Disposition (`BFO_0000016`)/Function (`BFO_0000034`); CCO capability | high | strong alignment. |
| Informational content (UFO-C) | Generically Dependent Continuant (`BFO_0000031`) / IAO ICE | high | both are copyable/generic. |
| Commitment/Claim/social relator (UFO-C) | bundle of Roles + IAO deontic ICE; CCO Agent Ontology | low | rich social layer flattens. |

## Divergence list (the artifact you must ship)

1. **Relator → 3 possible BFO patterns.** Record which pattern each relator uses (relational quality vs interdependent roles vs process+ICE).
2. **Phase is not projectable as a stereotype** — becomes a quality-defined class; instance-level phase membership is lost.
3. **Rigidity / sortality / identity meta-properties are dropped** — keep them in the source IR; they cannot live in BFO.
4. **Non-sortals collapse** to abstract superclasses / borne roles.
5. **Role placement restructures the instance graph** (type → borne entity).
6. **Situation has no BFO home** — reconstruct as a timed configuration.
7. **BFO-only structure** (spatial/temporal/spatiotemporal regions, fiat boundaries, sites, GDC/SDC concretization) has no OntoUML source — these are *added* in projection, not derived.

## Why this is worth it (the payoff)

The BFO/CCO projection is **exactly what the IKW-GraphEngine consumes** (BFO 2020 + CCO + IAO + RO, A/T/R-box reasoning + Guan). So the same model that runs the OntoUML/gUFO world is handed to GE as a reasoning/interop sidecar — **OntoUML stays the design discipline; BFO becomes a real interop target instead of a fork.** Authoring is single-source (the `model.yaml` IR); only the *alignment* is dual.

## Mechanics in this repo

- Project from the canonical IR, not from a diagram — both gUFO OWL and BFO/CCO are **generated projections**, drift-gated.
- A relator vertex (hyperedge-as-vertex) persists identically regardless of upper ontology; the projection only changes the *labels/axioms* attached. The mapping table records, per relator type, which BFO pattern it projects to.
- Run the BFO projection through an OWL reasoner (Level 3) just like gUFO; reserve genuinely time-indexed claims for the Common Logic form (see `bfo-ontology/references/BFO_RELATIONS.md`).
