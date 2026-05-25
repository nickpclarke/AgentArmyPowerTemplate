# Ontology Project — reference scaffold & IR spec

A worked, end-to-end example of the **ontology-derived generative pipeline**: one canonical IR (`model/model.yaml`) that compiles into many projections. Use it as the folder template when an ontology/knowledge agent starts a new model, and as the contract the generators target. Grounded in the Labs vault design ([Ontology-Pipeline](../../obsidian/labs/AgentArmyLabs/Ontology-Pipeline.md), [Reification-and-Hyperedges](../../obsidian/labs/AgentArmyLabs/Reification-and-Hyperedges.md)) and the `ufo-ontology` / `bfo-ontology` skills.

> **The one rule:** never collapse semantic ontology, runtime graph, DB schema, and proofs into one representation. Author once in the IR; emit explicit projections with a deterministic generator. Everything under generated dirs is **never hand-edited**.

## Folder structure

```
ontology-project/
├── ontology.ir.schema.json     ← THE SPEC: JSON Schema (draft 2020-12) for the IR (validation Level 1)
├── model/
│   └── model.yaml              ← THE SOURCE OF TRUTH: humans + agents edit here (OntoUML-stereotyped)
├── source/                     ← optional OntoUML authoring export (model.ontouml.json) aligned to ontouml-metamodel
├── semantic/                   ← GENERATED: gUFO OWL (primary) + BFO/CCO sidecar + alignments  [Level 3]
├── constraints/                ← GENERATED: SHACL shapes / ShEx (closed-world rules)             [Level 4]
├── verification/               ← GENERATED: Alloy (.als) + SMT (.smt2) + solver reports          [Levels 5–6]
├── generated/                  ← GENERATED: C# hypergraph runtime (.g.cs), never hand-edited
├── persistence/                ← GENERATED: ArcadeDB DDL (hyperedge-as-vertex)
├── provenance/                 ← GENERATED: PROV-O + build/hash manifest (DLT anchors hashes only)
└── docs/
    └── mapping-rules.md        ← UFO→BFO mapping table + divergence list (ship with every projection)
```

## The IR (`model/model.yaml`)

The "nervous system." A LinkML-like YAML the whole pipeline reads. Its `stereotype` vocabulary **is** the OntoUML profile (`kind`, `subkind`, `role`, `phase`, `relator`, `quality`, `mode`, `category`, `mixin`, `event`, `situation`, …). Key shapes:

- **`types[]`** — object/aspect/event types with stereotype, identity, rigidity, and (for projection) `gufo_type` + best-effort `bfo_class`.
- **`relators[]`** — n-ary relationships reified with **typed roles** (hyperedge-as-vertex). Bitemporal validity (`valid_from`/`valid_to`/`recorded_at`) lives **on the relator**. A binary relation is a degenerate 2-role relator. `bfo_pattern` records which of the three BFO patterns the realist projection uses.
- **`relations[]`** — non-reified `material` (derived from a relator), `formal`, parthood, `characterization`, `mediation`.
- **`constraints[]`** — rules tagged by prover language (`shacl`/`alloy`/`smt`/`owl`).
- **`projections{}`** — which outputs to emit.

## The spec (`ontology.ir.schema.json`)

The JSON Schema that defines and validates the IR — this is validation **Level 1** (well-formed model, unique IDs, valid stereotypes). Validate any model with:

```bash
python - <<'PY'
import json, yaml
from jsonschema import Draft202012Validator
s = json.load(open("ontology.ir.schema.json")); m = yaml.safe_load(open("model/model.yaml"))
errs = list(Draft202012Validator(s).iter_errors(m))
print("OK" if not errs else [ (list(e.path), e.message) for e in errs ])
PY
```

## Validation levels (each tool proves a different thing)

| Level | Tool | Artifact dir | Proves |
|---|---|---|---|
| 1 Syntactic | JSON Schema | (this spec) | well-formed IR, unique IDs, valid stereotypes |
| 2 OntoUML/UFO | stereotype + anti-pattern checks | — | sound conceptual modeling (RelOver, FreeRole, …) |
| 3 Semantic | gUFO/OWL reasoner (HermiT/ELK) | `semantic/` | satisfiability, disjointness, subsumption |
| 4 Constraint | SHACL (pyshacl) | `constraints/` | closed-world business rules |
| 5 Structural | Alloy | `verification/` | finite-scope counterexamples |
| 6 Arithmetic/temporal | Z3 / SMT | `verification/` | cardinality math, ordering, time windows |

## Dual upper-ontology projection ("offer both")

`semantic/` carries **two** alignments from the same IR: `model.gufo.ttl` (UFO/gUFO — primary authoring + reasoning) and `model.bfo-cco.ttl` (BFO 2020 + CCO — interop sidecar, e.g. for IKW-GraphEngine). They are **not** a lossless round-trip: `docs/mapping-rules.md` ships the correspondence table + divergence list. See the `ufo-ontology` and `bfo-ontology` skills.

## How agents use this

- `ontologist-ufo` authors `model.yaml` + emits `semantic/model.gufo.ttl`; `ontologist-bfo` emits `semantic/model.bfo-cco.ttl` + `docs/mapping-rules.md`.
- `ontologist-generalist` writes `constraints/` (SHACL) and runs Levels 1–4; `knowledge-engineer` populates a graph from the schema, runs reasoners, and owns `persistence/` + `provenance/`.
- `taxonomist` supplies enumerations/controlled vocabularies referenced by `model.yaml`.
