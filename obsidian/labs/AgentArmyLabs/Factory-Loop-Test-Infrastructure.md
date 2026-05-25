---
tags: [vision, middle-core, testing]
---
# Factory Loop & Test Infrastructure

> **Status:** architecture + test plan for the middle-core generator factory. Companion to [[Ontology-Pipeline]] (the loop) and [[Reification-and-Hyperedges]] (the next feature). Defines a **test station per transform** and a convention that **assigns every change to a station**, so we never add a projection without a place to prove it.

> **Thesis:** the factory is `model → generate → output → run → project`. The test strategy mirrors it one-to-one. Coverage of *generated* artifacts is kept locked to the model; coverage of *hand-authored* runtime is unit-tested; the whole loop is gated **both** locally and in CI.

## Current reality (grounded 2026-05-24)

- The **local pipeline** (`scripts/middle-core/Test-MiddleCoreLocalPipeline.ps1`) runs: validate → generate → Python unit tests → `dotnet build` → `dotnet test` → catalog validate → API smoke → UI smoke → Playwright.
- **Gaps:**
  - **No CI workflow** runs the middle-core loop (24 workflows, none for the model/generator) → regressions gated only locally.
  - **`dotnet test` is a no-op** — no C# test project exists, so the runtime (graph guards, scenario branches, enforcement API, soon relators) is covered *only* end-to-end via Playwright.
  - **No generated-code drift gate**; a latent LF/CRLF mismatch on `*.g.cs` makes regeneration noisy.
  - Verification Levels 5–6 absent (L1–L2 in the validator; **L3 OWL** and **L4 SHACL** now shipped and CI-gated).

## Test stations (one per factory transform)

| Factory layer | Artifact | Station | Tool | Today |
|---|---|---|---|---|
| IR (input) | `model/middle-core/model.yaml` | syntactic + semantic validation | JSON-Schema (L1) + Python validator (L2) | ✅ validator · ◻ JSON-Schema |
| Generator | `tools/modelgen` | determinism + **drift gate** + negative-rule tests | pytest + diff gate | ~ partial · ◻ drift gate |
| Generated contracts | `templates/middle-core/generated/*.g.cs` | compile + **conformance** | `dotnet build` + xUnit conformance | ✅ build · ◻ conformance |
| Runtime (hand-authored) | `ModelGraph`/`ScenarioRuntime`/handlers | **unit** | xUnit (**missing**) | ◻ |
| Projections | ArcadeDB / dlt / OWL / SHACL | round-trip / validation | per-projection | ✅ OWL+SHACL · ◻ ArcadeDB/dlt |
| Service / API | endpoints + `/model/demo` | smoke + e2e | PS smoke + Playwright | ✅ |
| Verification | model | Levels 1–6 | see roadmap | ~ L1–L4 |

The same stations run **locally** (the PS pipeline) and in **CI** (new `middle-core-model.yml`).

## Feature → test assignment convention

**Rule:** no model/generator/runtime change merges without coverage at its station(s). Worked example — the [[Reification-and-Hyperedges]] slice:

| Change | Station(s) | Test |
|---|---|---|
| IR `relators:` + roles | IR | JSON-Schema + validator negative tests (bad role type, cardinality, RelOver overlap) |
| generated relator contract | Generated | drift gate + conformance test (relator/role counts match model) |
| C# `RelatorInstance` + role-binding + binary-as-2-role wrapper | Runtime | xUnit (build relator, role lookups, degenerate binary case) |
| ArcadeDB hyperedge-as-vertex | Projection | round-trip test (later, when real port replaces the fake) |
| `/model/relators/{id}` | Service | API smoke + Playwright |

## Build order — Foundation first

Stand up coverage **before** building reification on top.

1. **Drift gate + EOL normalization.** Add `.gitattributes` so `templates/middle-core/generated/**` is LF (kills the CRLF noise); add a `regen` script + a CI/local check that regenerates into a temp dir and **fails on any diff** vs committed. *Acceptance:* editing the model without regenerating fails; hand-editing a `*.g.cs` fails; EOL stable cross-platform.
2. **`MiddleCore.Tests` (xUnit).** Hand-authored unit tests making `dotnet test` real: `ScenarioRuntime` (disabled handler at each index, unknown step, `Enabled=false`, handler-fault→failed step), `ModelGraph` (unknown objectType, duplicate id, dangling edge), enforcement API (`IsValidState`/`CanTransition`/`InitialState`/`IsTerminalState` + `ToModelString` round-trip). *Acceptance:* `dotnet test` runs N>0 tests covering the guard/branch logic the #101 review flagged.
3. **`middle-core-model.yml` CI gate.** On PRs touching `model/`, `tools/modelgen/`, `templates/middle-core/`: validate → drift-check → Python tests → `dotnet build`+`test` → catalog validate. *Acceptance:* the loop gates PRs in CI, not just locally. *Caveat:* the `@claude` app token can't push workflow files; this lands via a local PR the human merges.

Then: reification slice rides on real coverage.

## Tests as a projection — decision deferred to implementation

- **Option A — generate conformance tests.** The generator emits xUnit conformance tests from the model (enum members per machine, object/relator counts, transition tables). *Pro:* generated-artifact coverage can never drift from the model. *Con:* generator complexity; mild circularity (generated tests over generated code) — mitigate by asserting against an independent source (`model.yaml` / the fixture), not the `*.g.cs`.
- **Option B — hand-authored only.** Simpler generator; risk of test/model drift.
- **Leaning (decide when we build it):** *hybrid* — **generate conformance** tests (model↔contract), **hand-author behavior** tests (runtime logic). Behavior tests are exactly what shouldn't be generated; conformance is exactly what should.

## Verification roadmap (north-star Levels 1–6)

Each level is a **projection of the IR** (shapes/axioms generated from `model.yaml`), run at the noted cadence.

| L | Level | Tool | Proves | Where | Status |
|---|---|---|---|---|---|
| 1 | Syntactic | JSON-Schema (`check-jsonschema`) | well-formed model, unique IDs, valid stereotypes | validate step + CI | ~ (validator does this ad-hoc) → formalize as schema · **near** |
| 2 | OntoUML/UFO | `ontouml-js` / validator rules | sound stereotypes, anti-patterns (RelOver, FreeRole) | validate step | ~ partial · **near** |
| 3 | Semantic | OWL TBox + `rdflib` structural check (`owl_check.py`); full DL via HermiT/`owlready2` later | disjointness, domain/range respect (RL subset); satisfiability/subsumption on the DL upgrade | CI per-PR | ✅ **shipped** — `owl_check.py` (rdflib) in CI · ◻ DL reasoner upgrade |
| 4 | Constraint | **SHACL (`pyshacl`)** | closed-world business rules, data quality | CI | ✅ **shipped (#123)** — `pyshacl` in CI |
| 5 | Structural | Alloy Analyzer (CLI) | finite-scope counterexamples ("can this model exist?") | on-demand/nightly | ◻ **later** — see [[RT-verification-levels]] |
| 6 | Arithmetic/temporal | Z3 / SMT-LIB2 (`z3-solver`) | cardinality math, ordering, allocation, time windows | on-demand | ◻ **later** — see [[RT-verification-levels]] |

Sequencing: **L1 JSON-Schema** + **L4 SHACL** + **L3 OWL** gate cheaply per-PR (all generated from the model). L2 hardens with reification (relator/role anti-patterns). The L3 OWL gate today is a pure-`rdflib` structural pass (no Java) so it runs reliably in CI; a full OWL 2 DL reasoner (HermiT) that proves satisfiability/subsumption is a deliberate upgrade. **L5 Alloy** and **L6 Z3** stay *later* — don't stand up a prover until a concrete invariant needs it. Spike plan for the L3-DL upgrade + L5/L6: [[RT-verification-levels]] (`docs/synthesis/RT-verification-levels.md`).

## Open questions
- Cardinality enforcement home: generate-time (Python) vs runtime (C#) vs DB (ArcadeDB) — lean generate-time + runtime, DB as backstop.
- Should the drift gate live in its own workflow or inside `middle-core-model.yml`? (Lean: one workflow, a step.)
- Conformance tests: assert against `model.yaml` directly or the generated `model-runtime.fixture.json`? (Lean: the fixture — it's already the model's data projection.)

## Tracking
Board issues (Epic + Enablers) assign the Foundation work and the verification roadmap — see the linked issues from this note's PR.
