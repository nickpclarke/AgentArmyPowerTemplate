# ARC-ADR-033 — F# for the Ontology IR → Projections Compiler Core

| Field | Value |
|---|---|
| ID | ARC-ADR-033 |
| Status | Accepted |
| Date | 2026-05-28 |
| Deciders | Hub owner (Nicky Clarke) — "F# yes" 2026-05-28 |
| Supersedes | — |
| Superseded by | — |
| Tags | fsharp, dotnet, compiler, ontology, ir, projections, category-theory, functional-programming, middle-core, forge |

---

## Context and Problem Statement

The [Ontology-Pipeline north-star](../../obsidian/labs/AgentArmyLabs/Ontology-Pipeline.md) is, at its heart, a **multi-representation compiler**: one OntoUML/gUFO IR compiles into many projections (OWL 2 DL, SHACL, the C# hypergraph runtime, ArcadeDB DDL, Alloy/Z3, PROV-O). Its load-bearing rule is *congruence-first*: each projection must stay **structurally faithful** to the IR, via a **deterministic generator**. forge ([ADR-029](ARC-ADR-029-agentarmy-forge-codegen-container.md)) is explicitly a *pure, deterministic, golden-checkable* generator. The sift-sort authoring loop ([ADR-032](ARC-ADR-032-ontology-sift-sort-authoring-loop.md)) reuses the same projections.

Today the generator is C# (middle-core) and the sift slice is Python (where the reasoners live). **The question: what language is the right fit for the compiler *core* — the IR datatype and the projection functions — given that correctness here means "no silent gaps, structure-preserving, deterministic"?**

---

## Decision Drivers

| # | Driver |
|---|---|
| D1 | **No silent projection gaps.** Adding a stereotype must *force* every projection to handle it — a compile error, not a runtime surprise or a missed test. |
| D2 | **Structure preservation = correctness.** "Congruence-first" is precisely *functoriality*: a projection is correct iff it preserves the IR's structure (identity + composition). The language should make total, structure-preserving maps natural to write and hard to get wrong. |
| D3 | **Determinism.** Generators must be pure and golden-checkable (forge's whole premise). |
| D4 | **Category-theory expressivity.** FP makes the right vocabulary first-class — sum/product types, folds, monads — so the compiler can be *expressed as* functors, catamorphisms, and natural transformations rather than approximating them. (Hub-owner steer: "FP lets you use category-theory math; keep that top of mind.") |
| D5 | **Low fleet cost.** No new runtime, container tier, or alien toolchain if avoidable. Interop with the existing C# (middle-core) host matters. |

---

## Considered Options

### Option A — F# on .NET (recommended / chosen)

Write the IR datatype + projection functions in **F#**, in the same .NET solution as middle-core's C#. Discriminated unions model the stereotype space; exhaustive pattern matching makes every projection total; records + immutability make generators pure. F# and C# interoperate freely (same CLR), so the F# projection layer is consumed by the existing C# host with zero new runtime.

### Option B — Stay in C#

Keep everything C#. Possible, but C# has no exhaustiveness guarantee for type hierarchies (no compile error on an unhandled subtype), ADTs are verbose (class hierarchies + visitor), and the category-theory constructs (sum types, folds, monadic composition) are awkward — D1/D2/D4 all weaken.

### Option C — Rust

Rust has sum types + exhaustive `match` (satisfies D1/D2) and is already entering the fleet at the `/api/v2` tier. But it's a *separate* runtime from middle-core's .NET (fails D5 interop), and is heavier than F# for a pure transform/compiler (ownership ceremony where we want plain immutable data).

### Option D — Standalone Haskell / OCaml

Maximal purity and category-theory ergonomics, but introduces a brand-new toolchain, CI lane, container tier, and agent-support burden the fleet must carry (fails D5 decisively) for a benefit F# already delivers on the existing runtime.

---

## Decision Outcome

**Accepted: Option A — F# for the compiler core**, on the existing .NET runtime alongside middle-core's C#. C# stays the runtime/host; Python stays the reasoner-bound sift loop (rdflib/pyshacl/owlrl); F# owns the **IR datatype + the projection functions**.

### The category-theory framing (why this is rigour, not decoration)

| Compiler concept | Category-theory reading | F# mechanism |
|---|---|---|
| IR → a representation (OWL/SHACL/C#/ArcadeDB) | a **functor** | a total function over the IR types |
| "congruence-first" | **functoriality** (preserves structure) | the projection is total + structure-preserving by construction |
| the deterministic generator | a **catamorphism / initial-algebra homomorphism** (the unique structure-preserving map out of the IR) | a `fold` over the IR |
| add a stereotype ⇒ every projection must handle it | the **coproduct universal property** (a map out of a sum = a map out of each summand) | exhaustive `match` → **FS0025** fails the build |
| gUFO ⟷ BFO dual grounding (ADR-032 B) | a **natural transformation**; the "divergence list" = where naturality fails | a function between two projection outputs that commutes with the IR |
| the sift validate→repair loop + evidence ladder | **Kleisli / monadic** composition | `Result`/`Option` bind; PROV-O accrual = a `Writer` |

### Evidence (runnable, in-repo)

- `tools/ontology-sift/spikes/ontouml-ir.fsx` — the IR as a discriminated union; reproduces the doctor's L3 gUFO∧BFO cross-check; **`error FS0025` fails the build** when a stereotype is unhandled (D1 proven).
- `tools/ontology-sift/spikes/ir-to-shacl.fsx` — a real **IR → SHACL** functor: emits valid SHACL Turtle (the `Relator` correctly yields `gufo:mediates minCount 2` + named role paths), **validated cross-language by Python rdflib** (24 triples, 4 NodeShapes). The compiler core produces artifacts the existing toolchain consumes.

---

## Affected Layers / Repos

| Layer | Repo | Impact |
|---|---|---|
| middle-core | nickpclarke/middle-core | The existing Python multi-language generator (`generate_middle_core.py` — emits C#/JS/Rust/SHACL/OWL) is **not** migrated. Instead: (1) F# is an **output target** of that generator (state machines → discriminated unions, #112); (2) F# for **new hand-authored** surfaces (the IR datatype + the sift-loop/projection work). The C# host consumes the F# lib. |
| forge | nickpclarke/agentarmy-forge | The deterministic emitters become F# catamorphisms (golden tests unchanged). |
| hub | nickpclarke/AgentArmy | The F# spikes + this ADR; CI gains an F# build lane (the .NET SDK is already present — `dotnet fsi`). |
| (agents) | hub `.claude/agents/` | No dedicated F# specialist yet — OQ below. |

---

## Open Questions

1. **F#/C# boundary.** Does F# own only the IR + projections (consumed by a C# host), or grow further into the runtime? Lean: F# core library, C# host — smallest blast radius.
2. **CI + warnings-as-errors.** Wire the F# build with `--warnaserror:25` (treat incomplete matches as errors) so D1 is enforced in CI, not just locally.
3. **Agent support.** Do the cloud coding agents (Codex/Copilot) handle F# idiomatically? May need an `fsharp`/`dotnet` specialist agent or guidance.
4. **Scope creep guard.** Keep F# to the compiler core; resist rewriting the FastAPI/ArcadeDB I/O shells (Python/C#) into F# without a separate decision.

---

## Related Decisions

- **[ARC-ADR-032](ARC-ADR-032-ontology-sift-sort-authoring-loop.md):** the sift-sort loop whose projections this compiler core serves.
- **[ARC-ADR-029](ARC-ADR-029-agentarmy-forge-codegen-container.md):** forge — the deterministic generator that becomes a catamorphism.
- **Labs north-star:** *Ontology-Pipeline* — the multi-representation compiler, congruence-first.

---

## Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-28 | Claude Code (assisted) | Accepted on hub-owner "F# yes" — F# for the IR→projections compiler core, on .NET alongside middle-core C#; category-theory framing + two runnable F# spikes as evidence |
| 0.2 | 2026-05-28 | Hub owner | Scope clarified: do **not** migrate the working Python generator to F#. F# is (a) an **output target** of the generator — state machines as discriminated unions (middle-core #112) — and (b) the language for **new** hand-authored surfaces (sift-loop discipline, IR→SHACL spikes). Supersedes the "migrate projections incrementally" framing in 0.1. |
