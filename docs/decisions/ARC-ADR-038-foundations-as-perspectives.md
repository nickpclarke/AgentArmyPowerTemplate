# ARC-ADR-038 — Foundations as Perspectives (UFO ⊕ BFO via a DSRP Frame)

| Field | Value |
|---|---|
| ID | ARC-ADR-038 |
| Status | Accepted |
| Date | 2026-05-30 |
| Deciders | Hub owner (Nicky Clarke) — 2026-05-30 |
| Supersedes | — |
| Superseded by | — |
| Tags | ontology, foundations, ufo, bfo, dsrp, perspectives, divergence-registry, category-theory |

---

## Context and Problem Statement

The platform grounds its canonical concepts in two foundational ontologies — **UFO** (OntoUML / gUFO) for conceptual modeling and **BFO** (ISO/IEC 21838-2) for realist scientific interoperability. Early framing (e.g. the Platform Ontology doc §1.2) treated each concept as "grounded twice," carrying a `mid:bfoUpper` **and** a `mid:gufoArchetype` — a flat dual-label implying a clean 1:1 correspondence between the foundations.

Deep, adversarially-verified research (2026-05-30; full citations in the labs note *Foundations as Perspectives — UFO, BFO, and DSRP*) shows the flat dual-label is not faithful:

- **Opposing telos** — UFO is *descriptive* (conceptualizations; inter-worldview interoperability; Guizzardi et al., *Applied Ontology* 2022); BFO is *prescriptive realism* ("beyond concepts"; Smith, FOIS 2004).
- **Constructs do not correspond** — UFO's rigidity / sortality / identity machinery (kind, subkind, phase, role, relator, mode) has **no** BFO primitive; UFO «role» (an anti-rigid sortal whose instances *are* objects) ≠ BFO role (a realizable dependent continuant); a UFO relator has no native BFO kind.
- **No turnkey mapper** — foundational alignment is an open, benchmarked problem (OAEI); the only general interchange tool (SUGOI) covers DOLCE/BFO/GFO, **not UFO**, and clean equivalence captures ~36% of entities on average (as low as 2%). Even `bfo:Continuant ≡ dolce:Endurant` is **unsatisfiable** when merged. Alignment requires human-chosen subsumption + bridge axioms, not a lookup.

**The question: how should the platform reconcile UFO and BFO without asserting a correspondence that is logically false?**

## Decision Drivers

| # | Driver |
|---|---|
| D1 | **Honesty.** Do not assert a 1:1 mapping the literature shows merges into logical inconsistency. |
| D2 | **Each tradition sovereign.** Represent UFO and BFO on their own terms (originator-grade — the work may be read by the foundations' authors). |
| D3 | **Extensibility.** Adding a third foundation (CCO, DOLCE, gist) must not require an N×N mapping table. |
| D4 | **Coheres with platform mechanics.** The reconciliation should align with consensus-snap, `candidate-new`, and the holographic frontier already in the pipeline. |
| D5 | **Formal soundness.** Where bridging is asserted, it must be logically valid (partial maps + bridge axioms, never a false isomorphism). |

## Considered Options

### Option A — Foundations as DSRP-Perspectives + a divergence registry (recommended / chosen)

Hold each foundation as a **Perspective** (DSRP); record per-concept **commitments** where a faithful bridge exists and **divergences** where it does not; carry formal bridging on category-theoretic / institution-theoretic machinery.

### Option B — Flat dual-label (status quo)

Keep `bfoUpper` + `gufoArchetype` as co-equal coordinates. Rejected — implies a 1:1 mapping that merges into logical inconsistency (D1, D5).

### Option C — Pick one foundation

Standardize on UFO or BFO alone. Rejected — loses UFO's modeling fidelity *or* BFO's scientific interop; the platform needs both (D2).

### Option D — Automated alignment

Generate the mapping with an ontology matcher. Rejected — OAEI shows foundational matching is unsolved and tools "perform poorly" on it (D1, D5).

## Decision Outcome

**Accepted: Option A.** Concretely:

1. **Perspectives.** UFO is the **authoring** Perspective; BFO the **realist-interop** projection. The Perspective is declared per concept. **DSRP** (Cabrera) supplies the first-class **Perspective primitive** — an empirically-grounded meta-cognitive grammar used as the organizing frame.
2. **Per-concept commitments.** Where a faithful subsumption + bridge axiom between the Perspectives exists, record it as an explicit commitment.
3. **Divergence registry (first-class).** Where no faithful correspondence exists (UFO «role» ⊥ BFO role; UFO relator vs no BFO kind), record the **divergence** — the two Perspectives, the attempted mapping, the reason for irreducibility, the modeling decision. Divergences are information, not failures.
4. **Formal bridging** runs on partial maps + bridge axioms (cf. Spivak's functorial data migration, the DOL / Ontohub line). There is **no natural isomorphism** UFO ≅ BFO. *DSRP organizes; the logic layer bridges* — a division of labor (a grammar is not a logic).

### Consequences

**Positive**

- **Honest** — stops asserting a mapping that merges into inconsistency.
- **Extensible** — a third foundation is *another Perspective*, not an N×N table (D3).
- **Coheres with platform mechanics** — the canonical graph is objectivity-as-consensus across Perspectives; `candidate-new` is an unconverged Perspective; the holographic frontier holds the not-yet-converged (D4).
- **Originator-respecting** — each tradition stays sovereign within its Perspective (D2).

**Negative / cost**

- Requires building and governing the **divergence registry** (schema + lifecycle).
- The Perspective-meta-frame above two rival foundations is **novel** — no documented precedent — so it carries research risk.
- Bridge-axiom authoring is interpretive, per-concept work; it is not automatable.

## Grounding & Calibration

- UFO ⊥ BFO and the no-mapper findings are **high confidence** (primary sources).
- **DSRP** is **empirically grounded** as a meta-cognitive framework (Cabrera Research Lab; primary research, incl. AI-and-learning studies). An earlier automated literature pass mis-weighted this — it surfaced only a 2008 critique (since retracted by its author) and errored on the angle assigned to DSRP's positive corpus; that "contested" read was a search artifact, not a finding.
- The **Perspective-meta-frame above two foundations** and the **divergence-registry** pattern are **our synthesis** — well-reasoned, not documented prior art.

## References

- Labs note: `obsidian/labs/AgentArmyLabs/vision/Foundations as Perspectives — UFO, BFO, and DSRP.md` (full citations + well-grounded-vs-speculative ledger).
- [ARC-ADR-016](ARC-ADR-016-ontology-representation-reification-hyperedges.md) (reification / hyperedges) · [ARC-ADR-019](ARC-ADR-019-ontology-reasoning-layer.md) (reasoning) · [ARC-ADR-033](ARC-ADR-033-fsharp-ontology-compiler-core.md) (F# core).
- Guizzardi et al., *UFO*, Applied Ontology 2022 · Smith, *Beyond Concepts*, FOIS 2004 · OAEI · SUGOI / DOL · Cabrera, DSRP · Spivak, *Functorial Data Migration* (arXiv:1009.1166).
