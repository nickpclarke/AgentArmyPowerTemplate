---
tags: [vision, prior-art]
---
# UFO & GraphEngine Ecosystem — research learnings

> [!abstract] What this is
> Learnings from scanning the **InKnowWorks** GitHub org (the home of [[IKW-GraphEngine (Parallel Track)|IKW-GraphEngine]]) and the wider **OntoUML/UFO** tool ecosystem. Captured as research so the build-vs-borrow calls in [[Prior Art]] and the [[Ontology-Pipeline]] are grounded in what already exists.

> [!note] Caveat
> The InKnowWorks org is largely a curated set of **forks** of well-known projects. The list below is inferred intent from *what they chose to fork*; per-fork modifications aren't deeply verified here.

## InKnowWorks stack (what the fork-list reveals)
~59 repos. The shape: a **BFO + Common Logic + theorem-prover + .NET-graph** stack.

| Repo | What it is | Relevance to us |
|---|---|---|
| **RDF-Graph-and-Hypergraph** (C#) | RDF property + **hyper** data modeling on GraphEngine TSL + a computed DSL + LIKQ | Their hyperedge-as-object work in a tighter package — **best spike target** (smaller than the full engine) |
| **Guan** (C#) | Fork of Microsoft's logic-programming library (Service Fabric's Guan) | The reasoning engine they extend with ontology axioms |
| **RDFSharp** + **RDFSharp.Semantics** (C#) | Production .NET semantic-web library (OWL/SHACL/reasoner) | A **.NET-native** path for validation Levels 3–4 vs our Python lean (pyshacl, HermiT/ELK) |
| **Hets** (Haskell) | Heterogeneous Tool Set — multi-logic broker over OWL, **Common Logic**, FOL + many provers | Maps onto our "Levels 3–6, each tool proves a different thing" control plane |
| **FStar**, **hol-light**, **infer** (Infer.NET) | Proof-oriented language, theorem prover, Bayesian inference | Signals ambition past a graph DB: formal proofs + probabilistic reasoning alongside logic |
| **BFO** (HTML), **IAO** (Common Lisp) | The actual ontology sources | What GE grounds on (the BFO side of our [[IKW-GraphEngine (Parallel Track)#Offer both — one IR, two upper-ontology projections|offer-both]] design) |
| QuikGraph, language-ext, MessagePipe, MessagePack-CSharp, Prism, Windsor | .NET plumbing | Stack context |

> [!warning] Watch: Orleans / Service Fabric
> GE's refs + roadmap mention **Orleans** and **Azure Service Fabric**. Orleans is the actor runtime our [[Ontology-Pipeline#Rejected alternatives|pipeline explicitly rejected]] — note the divergence before going deeper.

## OntoUML/UFO ecosystem (the more actionable find)
A service-oriented OntoUML toolchain now exists that does several projections we were planning to hand-build.

| Project | What it does | Relevance to us |
|---|---|---|
| **OntoUML Server / OaaS** | Microservices: model verification, transform to **gUFO-based OWL**, transform to relational schemas, modularization | Almost exactly our "OWL/gUFO projection" + validation step — strong **build-vs-borrow** candidate |
| **ontouml-metamodel** + **ontouml-js** + **ontouml-models-lib** (Py) | Implementation-independent metamodel + canonical **JSON schema** | **Interop unlock:** align our `model.yaml` IR to the OntoUML JSON schema → plug into verification/transformation/catalog services |
| **Tonto** | A *textual* DSL for OntoUML (updated Oct 2025) | Directly relevant to the IR authoring choice (Tonto vs YAML vs LinkML for the OntoUML-stereotyped source) |
| **OntoUML/UFO Catalog** (`ontouml-models`) | Open catalog of real models in JSON + Turtle | Free **reference models + test corpus** for the generator/validators |
| **gufo2html** | gUFO → HTML docs | A ready-made "docs projection" |
| Editors | **Menthor** (deprecated) → **OntoUML Plugin for Visual Paradigm**; also **OLED** | The VP plugin is the maintained authoring path |

## Highest-value build-vs-borrow picks
1. **OntoUML Server (OaaS)** — borrow the OntoUML→gUFO-OWL + verification rather than build it.
2. **ontouml-metamodel / JSON schema** — align the IR to it for whole-ecosystem interop.
3. **RDF-Graph-and-Hypergraph** — cleanest spike target for hyperedge-as-object on TSL/LIKQ.
4. **Hets** + **RDFSharp.Semantics** — two routes for the proof/validation plane (multi-logic broker; .NET-native OWL/SHACL).

## Sources
- InKnowWorks org — `https://github.com/orgs/InKnowWorks/repositories`
- OntoUML/UFO Catalog — `https://github.com/OntoUML/ontouml-models`
- OntoUML metamodel — `https://github.com/OntoUML/ontouml-metamodel`
- ontouml-models-lib — `https://github.com/OntoUML/ontouml-models-lib`
- OntoUML tooling portal — `https://ontouml.org/ontouml/tooling/`
- gufo2html — `https://github.com/OntoUML/gufo2html`

Related: [[IKW-GraphEngine (Parallel Track)]], [[Prior Art]], [[Ontology-Pipeline]], [[Open Questions and Risks]], [[Model-Driven Platform]].
