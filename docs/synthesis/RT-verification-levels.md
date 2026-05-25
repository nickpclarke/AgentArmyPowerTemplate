# Verification Levels — spike plan for L3-DL, L5 (Alloy), L6 (Z3)

Companion to the roadmap in `obsidian/labs/AgentArmyLabs/Factory-Loop-Test-Infrastructure.md`
(north-star Levels 1–6). This note scopes the *later* levels so we can stand each up
when — and only when — a concrete invariant needs it, rather than speculatively.

## Where we are (2026-05-25)

| L | Level | Status |
|---|---|---|
| 1 | Syntactic (JSON-Schema) | ~ validator does this ad-hoc |
| 2 | OntoUML/UFO (validator rules) | ~ partial |
| 3 | Semantic (OWL) | ✅ **structural** — `tools/modelgen/owl_check.py` (pure `rdflib`) in CI |
| 4 | Constraint (SHACL) | ✅ shipped (#123) — `pyshacl` in CI |
| 5 | Structural (Alloy) | ◻ later — this note |
| 6 | Arithmetic/temporal (Z3) | ◻ later — this note |

Each level is **a projection of the IR** (`model/middle-core/model.yaml`) plus a checker.
The generator already emits the L3/L4 projections (`model-runtime.owl.ttl`,
`model-runtime.shacl.ttl`) next to the RDF ABox fixture (`model-runtime.fixture.ttl`).
The pattern for every new level is identical: **add an emitter to
`generate_middle_core.py`, add a checker under `tools/modelgen/`, gate it in
`middle-core-model.yml`, and let the drift gate lock the new artifact to the model.**

## L3-DL — full OWL 2 DL reasoner (upgrade to today's structural check)

**What today's check does NOT do.** `owl_check.py` is a pure-`rdflib` structural pass
over the OWL RL subset the projection encodes: it catches an individual asserted into two
disjoint classes, and object-property triples that violate `rdfs:domain`/`rdfs:range`
(honouring the subclass hierarchy). It does **not** prove *class satisfiability*
(is some class necessarily empty given the axioms?) or *subsumption* (does class A
necessarily imply class B?). Those need a real DL reasoner.

**Trigger to build it.** The first time the model gains axioms whose *consistency is not
obvious by inspection* — e.g. an object type that is simultaneously a subclass of two
classes declared disjoint (an unsatisfiable class), property characteristics
(`owl:FunctionalProperty`, `owl:inverseOf`, transitive roles), or cardinality
restrictions (`owl:maxCardinality`) that can contradict each other. Reification
(`relators:` + roles, see `[[Reification-and-Hyperedges]]`) is the likely first source:
role-filler constraints + relator disjointness are exactly the shape where a silent
unsatisfiable class can slip in.

**How.** `owlready2` (bundles the HermiT and Pellet reasoners; needs a JVM — Java 24 is
already on the dev box and `actions/setup-java` in CI). Load `model-runtime.owl.ttl`,
call `sync_reasoner()`, and fail if `Nothing` gains subclasses (unsatisfiable classes)
or if the ontology is inconsistent. Keep it a **separate CI step / nightly** — it is
slow (JVM warmup + reasoning) relative to the per-PR `rdflib` pass, which stays as the
fast gate. Alternative without a JVM: the ELK reasoner via ROBOT, but ELK only covers
OWL 2 EL — fine for subsumption, not for the full DL the cardinality cases need.

**Effort.** S–M. The emitter already produces the TBox; the work is the reasoner step
+ JVM provisioning + a deliberately-unsatisfiable fixture to prove the gate bites.

## L5 — Alloy (structural, finite-scope)

**What it proves that L3/L4 can't.** "*Can a model instance like this even exist?*"
Alloy searches a finite scope for a structure satisfying all constraints (or a
counterexample to an asserted property). It is the right tool for **relational
invariants** that are awkward in OWL/SHACL: "every relator binds exactly the roles its
type declares", "no role is played by two fillers in the same relator", "the
state-machine transition relation has no unreachable state and no sink that isn't
terminal". These are *existence/reachability* questions, not per-instance data checks.

**Trigger.** When state machines or relators grow structural invariants we want to prove
hold for *all* small instances, not just the one fixture — i.e. when a hand-written
fixture stops being convincing evidence. The state-machine reachability check is the
cheapest first win and is model-derived.

**How.** Emit an `.als` projection from `model.yaml`: `sig` per object type / relator,
`fact`s for cardinalities and role bindings, `pred`/`assert` + `check ... for N` for the
invariants. Run headless via the Alloy CLI (`java -jar org.alloytools.alloy.dist.jar
exec model-runtime.als`). On-demand / nightly, not per-PR (scope search is exponential).
Counterexamples are the payload — Alloy prints the offending instance.

**Effort.** M. New emitter (`alloy_model()` in the generator) + a checker that parses the
CLI result. The transition-table and role-binding facts are mechanical from the IR.

## L6 — Z3 / SMT (arithmetic & temporal)

**What it proves that L5 can't.** Alloy is finite-scope and relational; it is weak at
**unbounded arithmetic** and **temporal/ordering** math. Z3 handles: cardinality
arithmetic that must hold for *any* N ("sum of allocations ≤ capacity"), time-window
logic (bitemporal `valid_from ≤ valid_to`, no overlapping validity for the same key —
see `[[RT5-PIN-S2-bitemporal-queries]]`), ordering/scheduling, and the "time-series
pulse" alignment invariant (every reified edge shares a common temporal axis).

**Trigger.** When the model carries **numeric or temporal constraints** whose correctness
is arithmetic, not structural — concretely, the bitemporal validity rules and any
capacity/allocation cardinality once reification lands. This is the natural partner to
the bitemporal spike work already in this folder.

**How.** Emit SMT-LIB2 (or build constraints via `z3-solver` Python bindings, pure-pip,
no JVM) from the IR's cardinality/temporal facts; `check-sat` per asserted invariant,
report any `sat` model that witnesses a violation (or `unsat` of the negation as proof).
On-demand. `z3-solver` is the lightest of the three to provision (no Java).

**Effort.** M. Emitter for the arithmetic/temporal slice + a Z3 driver. Scope it to the
bitemporal + cardinality invariants first; don't try to encode the whole model.

## Sequencing recommendation

1. **L3-DL** when reification introduces the first non-obvious satisfiability question
   (likely next, and the emitter already exists — lowest marginal cost).
2. **L6 Z3** alongside bitemporal/cardinality enforcement (pure-pip, no JVM, and there is
   already concrete temporal invariant work to anchor it).
3. **L5 Alloy** when we want all-small-instances structural proofs (state-machine
   reachability is the cheap first target).

Hold the line from the roadmap: **don't stand up a prover until a concrete invariant
needs it.** Each level above is a projection + checker + CI step + drift-locked artifact —
the same four moves L3 and L4 already made.
