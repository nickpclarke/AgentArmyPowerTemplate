# BFO 2020 — Full Category Hierarchy

Every BFO 2020 universal with its elucidation, examples, and OBO/OWL identifier. Namespace: `http://purl.obolibrary.org/obo/` (e.g. `obo:BFO_0000001`). IDs are stable across releases but **verify against the official `bfo.owl`** you vendor before relying on them in generated artifacts.

> Elucidations below are faithful paraphrases of the BFO 2020 / ISO/IEC 21838-2 text, not verbatim. Use the official spec for normative wording.

## Entity — `BFO_0000001`
Anything that exists, has existed, or will exist. The root. Everything else `is_a` Entity (directly or transitively). Top split: **Continuant** and **Occurrent** (disjoint, jointly exhaustive).

---

## Continuant — `BFO_0000002`
An entity that **persists, endures, or continues to exist through time** while maintaining its identity, has no temporal parts, and is wholly present whenever it exists. Continuants can gain and lose parts and qualities over time. Disjoint with Occurrent.

### Independent Continuant — `BFO_0000004`
A continuant that is the **bearer** of qualities, roles, and dispositions, and which does not depend on any other entity to exist (it can exist on its own). Bearers of SDCs.

- **Material Entity — `BFO_0000040`** — an independent continuant that has **matter** (mass) as a part. Three subtypes:
  - **Object — `BFO_0000030`** — a maximally self-connected material entity that is causally unified and has a characteristic internal structure (an organism, a cell, a molecule, a chair, a planet). The paradigm material entity.
  - **Fiat Object Part — `BFO_0000024`** — a material part demarcated by a *fiat* (human-imposed) boundary, not by a bona fide physical discontinuity (the upper half of your body, the Western Hemisphere's landmass, a county).
  - **Object Aggregate — `BFO_0000027`** — a material entity made of a collection of objects as member parts (a swarm of bees, a pile of sand, a jury, a fleet). Identity via its members.
- **Immaterial Entity — `BFO_0000141`** — an independent continuant with **no matter** as part. Subtypes:
  - **Continuant Fiat Boundary — `BFO_0000140`** — a boundary of a material entity, of lower dimension, demarcated by fiat:
    - **Zero-dimensional continuant fiat boundary — `BFO_0000147`** — a fiat point (the North Pole; the apex of a cone where it's a fiat).
    - **One-dimensional continuant fiat boundary — `BFO_0000142`** — a fiat line (a coastline as idealized, the Equator).
    - **Two-dimensional continuant fiat boundary — `BFO_0000146`** — a fiat surface (the surface of your skin idealized; a property line plane).
  - **Site — `BFO_0000029`** — a three-dimensional immaterial entity that is (partly or wholly) bounded by material entities, or that is an unoccupied hollow (the interior of your mouth, the hold of a ship, a hole, a tunnel).
  - **Spatial Region — `BFO_0000006`** — a continuant part of space itself (independent of any occupant):
    - **Zero-dimensional spatial region — `BFO_0000018`** (a point of space)
    - **One-dimensional spatial region — `BFO_0000026`** (a line of space)
    - **Two-dimensional spatial region — `BFO_0000009`** (a plane of space)
    - **Three-dimensional spatial region — `BFO_0000028`** (a volume of space)

### Specifically Dependent Continuant (SDC) — `BFO_0000020`
A continuant that **inheres in** or is **borne by** exactly one (or, for relational qualities, several) specific independent continuant(s), and could not exist without that exact bearer. SDCs migrate to no other bearer.

- **Quality — `BFO_0000019`** — an SDC that, if it exists, is **fully exhibited/realized at every moment** it inheres; it is simply a way its bearer is (this ball's specific roundness, this object's mass, this surface's temperature). Qualities take values in quality spaces (cf. PATO).
  - **Relational Quality — `BFO_0000145`** — a quality that inheres in **several** bearers at once (a specific marital bond viewed as a quality, a specific distance between two bodies, a hue match between two surfaces).
- **Realizable Entity — `BFO_0000017`** — an SDC whose instances contain a **potential** that is *realized in* (manifested by) associated processes; not fully exhibited at all times (it can lie dormant).
  - **Role — `BFO_0000023`** — a realizable entity that the bearer has **contingently / externally**: it exists because of the bearer's place in some social, institutional, or contextual setting, and the bearer could lose it without changing intrinsically (the role of being a student, a defendant, a catalyst-in-this-reaction, a tool-for-this-job).
  - **Disposition — `BFO_0000016`** — a realizable entity grounded in the **internal physical makeup** of its bearer, such that the bearer would necessarily manifest it under appropriate triggering conditions (fragility of this glass, solubility of this salt, the disposition of this cell to divide).
    - **Function — `BFO_0000034`** — a disposition that exists because its bearer is the kind of thing it is *in order to* realize a particular process — i.e. it was designed-for or selected-for that end (the function of this heart to pump blood, of this knife to cut, of this protein to catalyze).

### Generically Dependent Continuant (GDC) — `BFO_0000031`
A continuant that **depends on one or more other entities generically** — it can be **copied/migrated** from one bearer to another and exist in multiple copies at once. The "pattern" or "information" layer. A GDC is **concretized by** SDCs in its bearers (the novel *Moby Dick* as a GDC is concretized by the specific arrangement of ink in each physical copy and by patterns in each reader's brain). Information content entities (IAO) are GDCs.

---

## Occurrent — `BFO_0000003`
An entity that **occurs, happens, unfolds, or develops in time** — it has temporal parts and is never wholly present at any single instant. Disjoint with Continuant. Occurrents do not change (they *are* the change); they have continuants as participants.

- **Process — `BFO_0000015`** — an occurrent that has temporal proper parts and depends on at least one material entity as participant; it is something that happens, unfolds, develops (a heartbeat, a fermentation, a courtship, an assembly run, a war).
  - **History — `BFO_0000182`** — the *totality* of processes occupying the spatiotemporal region of a material entity; the unique process that is the whole life/career of that entity.
  - **Process Profile — `BFO_0000144`** — a proper *part* of a process that captures one quantitative/structural dimension of it (the beat-frequency profile of a heartbeat process, the rate profile of a reaction), allowing two processes to be compared along that dimension.
- **Process Boundary — `BFO_0000035`** — the instantaneous temporal boundary of a process (its beginning or ending); a zero-temporal-extent occurrent (the moment a race starts, the instant of death).
- **Temporal Region — `BFO_0000008`** — an occurrent that is a part of time itself:
  - **Zero-dimensional temporal region / temporal instant — `BFO_0000148`** (a moment of time)
  - **One-dimensional temporal region / temporal interval — `BFO_0000038`** (a stretch of time)
- **Spatiotemporal Region — `BFO_0000011`** — a part of spacetime; the four-dimensional region a process occupies.

---

## Disjointness & exhaustiveness cheatsheet

- `Continuant ⊓ Occurrent = ⊥` (top-level disjoint, jointly exhaustive of `Entity`).
- Within continuants: `Independent ⊓ SDC ⊓ GDC` are pairwise disjoint.
- `Quality ⊓ Realizable = ⊥` within SDC.
- `Role ⊓ Disposition = ⊥`; `Function ⊑ Disposition`.
- `Material ⊓ Immaterial = ⊥` within independent continuant.
- A **bearer** is always an independent continuant; an SDC always `inheres_in` a bearer; a GDC is always `concretized_by` an SDC.

## Common modeling pitfalls

- **Putting a process under a continuant** (or vice versa): "diagnosis" is ambiguous — the *act* of diagnosing is a process; the *resulting* diagnosis-as-recorded is a GDC (information content entity). Split them.
- **Roles asserted as subtypes of the bearer:** "Student `is_a` Person" is wrong in BFO. Student is a **Role** (`BFO_0000023`) that a Person *bears*. (This is exactly where UFO's anti-rigid `role` stereotype diverges — see UFO_BFO_MAPPING.md.)
- **Confusing quality and disposition:** a *measured* temperature value is a Quality; *flammability* is a Disposition (only manifest when triggered).
- **Information modeled as a quality:** the content of a document is a **GDC** (IAO ICE), not a quality of the paper.
- **Asserting multiple `is_a` parents:** keep the asserted tree single-inheritance; let the reasoner infer the rest.
