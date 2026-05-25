# UFO ↔ BFO — correspondence and divergence (the synthesis)

BFO and UFO are **rival foundational lineages**, not dialects of one ontology:

- **BFO** — *realist*: categories carve mind-independent reality; max one identity per entity; single inheritance; no modal meta-properties. Built for scientific description and data integration (OBO, CCO).
- **UFO** — *cognitive / conceptual-modeling-oriented*: categories are organized by **modal meta-properties** (rigidity, sortality, identity, dependence) to capture a stakeholder's conceptualization. Built for OntoUML diagrams and validation.

So the bridge is **best-effort, lossy, and directional**. The AgentArmy design ("offer both, one IR → two projections") treats BFO/CCO as an **interop sidecar**: author once in UFO/OntoUML, project to BFO/CCO, and **ship a mapping table + divergence list** — never claim a round-trip. This file is the BFO-side view (grounding an incoming UFO model). The mirror lives in `ufo-ontology/references/UFO_BFO_MAPPING.md`.

## Correspondence table

| UFO / OntoUML construct | Closest BFO (+CCO) category | Fidelity | Note |
|---|---|---|---|
| **Endurant** | Continuant (`BFO_0000002`) | high | clean top-level match. |
| **Substantial** (object) | Independent Continuant / Material Entity (`BFO_0000040`) → Object (`BFO_0000030`) | high | the bearer. |
| **«kind»** (rigid sortal, provides identity) | a universal under Material Entity / Object; often a CCO mid-level class | high | identity principle has no BFO counterpart but the *class* maps. |
| **«subkind»** (rigid sortal) | `is_a` subclass of the kind's BFO class | high | straightforward subsumption. |
| **«collective»** | Object Aggregate (`BFO_0000027`) | high | members ↔ `member_part_of`. |
| **«quantity»** (amount of matter) | Material Entity (a portion of matter) | medium | BFO has no "amount of matter" stereotype; model as material entity + `continuant_part_of`. |
| **«quality»** (intrinsic moment) | Quality (`BFO_0000019`); reuse PATO | high | values ↔ quality spaces / PATO. |
| **«mode»** (intrinsic moment, may bear qualities) | Realizable Entity (`BFO_0000017`) — Disposition (`BFO_0000016`) if dispositional; else a Quality-bearing SDC | medium | UFO modes are broader than BFO realizables; split by whether realized in a process. |
| **«relator»** (mediates participants) | **no single category** — use (a) Relational Quality (`BFO_0000145`), or (b) a bundle of interdependent roles/dispositions realized in one process, or (c) process + IAO ICE | **low — the headline divergence** | UFO's first-class relator fans out into 3 BFO patterns. |
| **«role»** (anti-rigid sortal, relational) | Role (`BFO_0000023`) borne by the participant | medium | *placement differs*: UFO role = anti-rigid type whose instances are the substantials; BFO role = a dependent-continuant entity the substantial *bears*. The diagram restructures. |
| **«roleMixin»** (anti-rigid non-sortal role) | Role borne across multiple bearer kinds | low | BFO has no non-sortal/mixin notion; emulate with a Role + multiple bearer classes. |
| **«phase»** (anti-rigid sortal, intrinsic change) | **no BFO counterpart** — model the phase-defining qualities/dispositions, or a defined class over a quality value | **low — second headline divergence** | BFO has no phase stereotype; phases become quality-conditioned defined classes or process stages. |
| **«phaseMixin»** | as phase, spanning kinds | low | same gap as phase + mixin. |
| **«category»** (rigid non-sortal) | a higher universal spanning object kinds | medium | maps as an abstract superclass; "non-sortal" meta-property is dropped. |
| **«mixin»** (semi-rigid non-sortal) | abstract superclass | low | semi-rigidity has no BFO analogue. |
| **«event»** / Perdurant (UFO-B) | Process (`BFO_0000015`) / Process Boundary (`BFO_0000035`) | high | instantaneous events ↔ process boundaries. |
| **«situation»** | **no direct counterpart** — a configuration of continuants + SDCs obtaining at a time; relate via process boundaries / `exists_at` | low | UFO situations (state-of-affairs that trigger dispositions) have no BFO category; reconstruct from participants at t. |
| **«type»** (high-order / powertype) | OWL punning / `owl:Class` of classes; no BFO category | low | BFO is first-order at the universal level. |
| **«datatype» / «enumeration»** | `rdfs:Datatype` / value partition | n/a | data-level, outside BFO's realist categories. |
| **Disposition / Capability** (UFO) | Disposition (`BFO_0000016`) / Function (`BFO_0000034`); CCO capability | high | strong alignment. |
| **Informational content** (UFO-C, social objects) | Generically Dependent Continuant (`BFO_0000031`) / IAO ICE | high | both treat content as copyable/generic. |
| **Commitment / Claim / social relator** (UFO-C) | bundle of roles + IAO deontic ICE; CCO Agent Ontology | low | UFO-C's rich social layer flattens onto roles + information artifacts. |

## The divergence list (ship this with every projection)

1. **Relator has no single BFO home.** Pick one of the three BFO patterns per relator and document which. Symmetric co-dependent bond → relational quality; role-differentiated → interdependent roles; documentary → process + ICE.
2. **Phase is unrepresentable as a stereotype.** BFO has no anti-rigid phase. Phases become defined classes over qualities or process stages — instances no longer carry "is currently in phase X" as a type membership.
3. **Rigidity / sortality / identity meta-properties vanish.** BFO classes don't record whether a type is rigid or carries identity; that information is lost in projection (keep it in the source IR).
4. **Non-sortals (category/mixin/roleMixin/phaseMixin) collapse** to ordinary abstract superclasses or borne roles.
5. **Role placement restructures the graph.** UFO role-as-type → BFO role-as-borne-entity changes which node is the instance.
6. **Situation has no counterpart**; reconstruct as a configuration at a time.
7. **BFO adds structure UFO lacks**: spatial/temporal/spatiotemporal regions, fiat boundaries, sites, GDC/SDC concretization are first-class in BFO and have no OntoUML stereotype — going *BFO→UFO* loses these.

## Worked example — "Employment" (UFO relator → BFO)

UFO: `Employment` «relator» mediating `Employee` «role» (played by `Person` «kind») and `Employer` «roleMixin» (played by `Person`/`Organization`).

BFO/CCO projection (pattern b — interdependent roles):
- `Person` `is_a` `cco:Person` `is_a` Object.
- `employee role` `is_a` Role (`BFO_0000023`), `inheres_in` the person.
- `employer role` `is_a` Role, `inheres_in` the person/organization.
- An `Employment Process` `is_a` Process that `realizes` both roles and `has_participant` both bearers.
- The contract/record `is_a` IAO information content entity (GDC) that `is_about` the employment.

Divergence captured: the single UFO relator became *two roles + a process + an ICE*; the anti-rigid `roleMixin` for employer became a Role borne by two bearer kinds; nothing records "Employee is anti-rigid".

> In the AgentArmy hyperedge-as-vertex persistence, **all of this is one relator vertex with role-binding edges** regardless of upper ontology — only the projection labels differ. The mapping table is the artifact that documents *which* BFO pattern each relator vertex projects to.
