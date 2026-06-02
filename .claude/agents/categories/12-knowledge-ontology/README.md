# Knowledge & Ontology Subagents

Knowledge & Ontology subagents own the **semantic layer** — the formal meaning behind the data. They design foundational and applied ontologies, organize vocabularies, and build the knowledge graphs and reasoning systems that turn a conceptual model into something machines can query and infer over. This is the discipline behind AgentArmy's north-star **ontology-derived generative pipeline** (UFO/OntoUML authoring + a BFO/CCO interop projection; see the Labs vault and `docs/release-trains/RT5-ontology-grade-persistence.md`).

These agents are arranged on a **formality gradient** so routing is unambiguous: from non-axiomatized vocabularies (taxonomist) up through applied OWL/SHACL (ontologist-generalist) to foundational commitment (ontologist-ufo, ontologist-bfo), with knowledge-engineer operationalizing the result.

## When to use Knowledge & Ontology Subagents

- Design a **foundational conceptual model** (UFO/OntoUML) or a **realist ontology** (BFO/CCO).
- Build **applied OWL/RDFS/SHACL** ontologies, reuse/align vocabularies, or write competency questions.
- Organize **taxonomies, thesauri, controlled vocabularies, facets, tag schemes** (SKOS).
- **Populate and reason over a knowledge graph** — rules, reasoners, SPARQL, KB lifecycle.
- Produce a **dual upper-ontology projection** (gUFO OWL + BFO/CCO) from a single source model.

## Available Subagents

### [**ontologist-ufo**](ontologist-ufo.md) — UFO / OntoUML conceptual modeler *(primary authoring discipline)*
Designs ontologically well-founded models with stereotypes (kind/role/phase/relator/…), reasons about rigidity/sortality/identity, reifies n-ary relations as relators, catches anti-patterns, and projects to gUFO OWL. **Loads the `ufo-ontology` skill.** `model: opus`.

### [**ontologist-bfo**](ontologist-bfo.md) — BFO / realist ontologist
Classifies into BFO 2020 (ISO/IEC 21838-2), authors OBO-Foundry-style ontologies with Aristotelian definitions, reuses RO/IAO/PATO/CCO, and produces the realist BFO/CCO interop projection (e.g. for IKW-GraphEngine). **Loads the `bfo-ontology` skill.** `model: opus`.

### [**ontologist-generalist**](ontologist-generalist.md) — foundation-agnostic ontology engineer *(mid-tier default + cluster router)*
Applied OWL 2 / RDFS / SHACL modeling, ontology reuse & alignment, competency questions, evaluation — and routes foundational decisions to the specialists. `model: sonnet`.

### [**knowledge-engineer**](knowledge-engineer.md) — KR&R / knowledge-graph builder
Operationalizes ontologies: knowledge acquisition, KG construction & population, rules (SWRL/SHACL-AF/Datalog), reasoner selection & runs, SPARQL/OBDA, KB lifecycle. `model: sonnet`.

### [**taxonomist**](taxonomist.md) — knowledge-organization specialist
Taxonomies, controlled vocabularies, thesauri (SKOS), faceted classification, metadata/tag schemes, term governance — the non-axiomatized layer. `model: sonnet`.

## Quick Selection Guide

| If you need to… | Use this subagent |
|---|---|
| Model with UFO/OntoUML stereotypes & relators | **ontologist-ufo** |
| Ground in BFO 2020 / OBO / CCO; realist interop | **ontologist-bfo** |
| Build applied OWL/SHACL, reuse/align, write CQs | **ontologist-generalist** |
| Populate & reason over a knowledge graph | **knowledge-engineer** |
| Build taxonomies / thesauri / SKOS / facets | **taxonomist** |

## Delegation map (acyclic, down/lateral only)

```
ontologist-generalist  (mid-tier router / entry point)
   ├─▶ ontologist-ufo  ◀───coordinate (dual projection)───▶  ontologist-bfo
   │        │                                                     │
   │        └──────────────┬──────────────────┬─────────────────┘
   │                       ▼                  ▼
   ├─▶ taxonomist ───▶ knowledge-engineer ───▶ data-engineer / nlp-engineer (other categories)
   └─▶ knowledge-engineer
```

- The two foundational specialists **coordinate** (they do not delegate to each other — avoids a cycle) on the UFO↔BFO dual projection.
- `knowledge-engineer` **consumes** the ontology; modeling defects go back via `error-coordinator`, never by delegating up.
- No agent delegates **up** to catch-all generalists. All escalate failures to `error-coordinator` and feed learnings to `knowledge-synthesizer`.

## Boundaries vs neighbouring agents

- **`information-architect` (11-enterprise-architecture)** — owns enterprise *data* architecture (CDM/LDM/PDM, MDM, DAMA governance, lineage, regulatory). This cluster owns *formal semantics / knowledge*. Data-as-asset → information-architect; meaning-as-logic → here.
- **`knowledge-synthesizer` (09-meta-orchestration)** — learns patterns from *agent interactions* for organizational learning. `knowledge-engineer` builds *domain* knowledge graphs about the world. Different "knowledge."
- **`nlp-engineer` (05-data-ai)** — extracts entities/relations from *text*. `knowledge-engineer` integrates and reasons over them in the ontology-grounded KG.

## Skills

| Skill | Loaded by | Carries |
|---|---|---|
| [`ufo-ontology`](../../../skills/ufo-ontology/SKILL.md) | ontologist-ufo (+ generalist, knowledge-engineer) | UFO-A/B/C theory, full OntoUML profile, anti-patterns, gUFO OWL, UFO→BFO mapping |
| [`bfo-ontology`](../../../skills/bfo-ontology/SKILL.md) | ontologist-bfo (+ generalist, knowledge-engineer) | BFO 2020 hierarchy + IDs, relations & time-indexing, OBO/CCO/IAO/RO, UFO↔BFO mapping |

## Common Patterns

**Dual upper-ontology projection (the "offer both"):**
- **ontologist-ufo** authors the OntoUML/gUFO source → **ontologist-bfo** grounds the BFO/CCO sidecar → ship mapping + divergence list → **knowledge-engineer** reasons over both.

**New domain knowledge base:**
- **ontologist-generalist** scopes + competency questions → **ontologist-ufo**/**ontologist-bfo** for foundational rigor → **taxonomist** for vocabularies → **knowledge-engineer** populates & reasons.

**Vocabulary → ontology graduation:**
- **taxonomist** builds the SKOS scheme → **ontologist-generalist** formalizes to OWL/SHACL → **knowledge-engineer** operationalizes.
