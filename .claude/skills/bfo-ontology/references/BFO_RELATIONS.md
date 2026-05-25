# BFO Relations — catalog, arity, and the OWL binarization trap

BFO's relations come from BFO core + the **Relation Ontology (RO)**. The defining feature: **continuant relations are time-indexed**. Treat this as the central modeling fact, because it determines whether you can express what you mean.

## Why time-indexing matters

A continuant can be part of different wholes at different times (a cell is part of one organism, then not). So the *true* relation is ternary:

```
continuant_part_of(c1, c2, t)        "c1 is part of c2 at time t"
```

Occurrents already contain their time (a temporal part is just a part), so occurrent relations are ordinary binaries:

```
occurrent_part_of(o1, o2)            no time index needed
```

### The two axiomatizations handle this differently
- **Common Logic (CLIF)** — the *normative* ISO/IEC 21838-2 form. Keeps the genuine **ternary** relations with explicit time arguments. Full first-order; supports temporal reasoning faithfully.
- **OWL 2 DL (`bfo.owl`)** — must use **binary** object properties (OWL has no n-ary predicates). It therefore **binarizes**: the time index is dropped (the "atemporal" reading) or pushed into temporalized constructs/reified relation instances. This is decidable and tooling-friendly but **loses the temporal qualification** — a known, documented trade-off, not a bug.

> Practical rule: if your reasoning needs "part of *at a time*", you need the CL projection (or a reified temporal pattern in OWL). If you only need subsumption/disjointness/satisfiability, the binarized OWL is enough. In the AgentArmy pipeline, OWL handles validation Level 3; push genuinely temporal claims to the Common Logic projection or to the bitemporal relator layer.

## Mereology (parthood)

| Relation | Domain → Range | Arity | Notes |
|---|---|---|---|
| `continuant_part_of` / `has_continuant_part` | Continuant → Continuant | ternary (+t) | `BFO_0000176` / `BFO_0000178`. Reflexive, antisymmetric, transitive at each t. |
| `occurrent_part_of` / `has_occurrent_part` | Occurrent → Occurrent | binary | `BFO_0000132` / `BFO_0000117`. |
| `member_part_of` / `has_member_part` | Object → Object Aggregate | ternary (+t) | RO; membership in an aggregate. |
| `proper continuant part of` | Continuant → Continuant | ternary (+t) | irreflexive variant. |

## Spatial / temporal / spatiotemporal location

| Relation | Domain → Range | Notes |
|---|---|---|
| `located_in` / `location_of` | IndependentContinuant → IndependentContinuant | ternary (+t); e.g. a person located in a room. |
| `occupies_spatial_region` | MaterialEntity → SpatialRegion | ternary (+t). |
| `occupies_temporal_region` | Occurrent → TemporalRegion | binary. |
| `occupies_spatiotemporal_region` | Occurrent → SpatiotemporalRegion | binary. |
| `spatially_projects_onto` | SpatiotemporalRegion → SpatialRegion (at t) | derives the spatial footprint. |
| `temporally_projects_onto` | SpatiotemporalRegion → TemporalRegion | derives the time span. |

## Participation (continuant ↔ occurrent — the bridge)

| Relation | Domain → Range | Notes |
|---|---|---|
| `participates_in` / `has_participant` | Continuant → Occurrent | `RO_0000056` / `RO_0000057`. How endurants take part in processes; the *only* clean bridge between the two top categories. Ternary (+t) on the continuant side. |
| `has_agent` / `agent_in` | (CCO/RO) Agent → Process | CCO specialization of participation. |
| `realizes` / `is_realized_in` | Process ↔ RealizableEntity | `RO_0000055`. A process realizes a role/disposition/function (the heartbeat realizes the heart's function). |

## Dependence & inherence (the SDC/GDC machinery)

| Relation | Domain → Range | Notes |
|---|---|---|
| `inheres_in` / `bearer_of` | SDC → IndependentContinuant | `RO_0000052` / `RO_0000053`. An SDC inheres in its bearer; ternary (+t). |
| `specifically_depends_on` | SDC → IndependentContinuant | `BFO_0000195` (s-depends-on). The general dependence under inherence. |
| `generically_depends_on` | GDC → IndependentContinuant | `RO_0002502` / `BFO_0000084`. A GDC g-depends on its bearer(s). |
| `concretizes` / `is_concretized_by` | SDC ↔ GDC | `RO_0000059` / `RO_0000058`. A specific arrangement concretizes a pattern (this PDF's bytes concretize the document's content). |
| `has_role` | IndependentContinuant → Role | shorthand for `bearer_of` restricted to Role. |
| `has_disposition` | MaterialEntity → Disposition | shorthand for `bearer_of` restricted to Disposition. |
| `has_function` | MaterialEntity → Function | shorthand for `bearer_of` restricted to Function. |
| `has_quality` | IndependentContinuant → Quality | shorthand for `bearer_of` restricted to Quality. |
| `has_material_basis` | Disposition → MaterialEntity | the physical makeup grounding a disposition. |

## Temporal ordering (occurrents)

| Relation | Notes |
|---|---|
| `precedes` / `preceded_by` | `BFO_0000063` / `BFO_0000062`. Ordering of occurrents/temporal regions. |
| `has_first_instant` / `has_last_instant` | `BFO_0000222` / `BFO_0000224`. Boundaries of a 1-D temporal region. |
| `simultaneous_with`, `during`, `starts`, `finishes`, `overlaps` | Allen-style interval relations (often via OWL-Time alignment). |
| `exists_at` | Entity → TemporalRegion | `BFO_0000108`. When an entity exists. |

## Instantiation & subsumption (the meta level)

| Relation | Relates | Notes |
|---|---|---|
| `is_a` (`rdfs:subClassOf`) | universal → universal | the asserted single-inheritance backbone. |
| `instance_of` | particular → universal | ternary (+t) for continuants: a thing can instantiate a defined class only at some times. |

## Reifying n-ary relations the BFO way

BFO has **no native relator**. To express an n-ary material relationship (a marriage, an employment, a mitigation case) you have three BFO-sanctioned options:

1. **Relational quality** (`BFO_0000145`) — one SDC inhering in *all* participants jointly (good for symmetric, co-dependent bonds).
2. **A bundle of interdependent roles/dispositions** — each participant bears its own realizable entity, all realized in the same process (good for asymmetric, role-differentiated relations: employer-role + employee-role realized in the employment process).
3. **A process + an information content entity (IAO GDC)** that records the arrangement (good when the relationship is really an event with a documentary trace — e.g. a contract).

This is precisely where UFO's single `relator` construct fans out into several BFO patterns — see [UFO_BFO_MAPPING.md](UFO_BFO_MAPPING.md). In the AgentArmy pipeline, the hyperedge-as-vertex relator persists physically the same way; only the *upper-ontology label* differs between the gUFO and BFO/CCO projections.
