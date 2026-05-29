# F# ontology compiler core (ARC-ADR-033)

The **functional core** of the sift-sort loop. The Python implementation
(`tools/ontology-sift/` here, and the live service in `backend-core`) is the
*imperative shell* — it does IO (HTTP, Cerebras, Cohere embeddings, ArcadeDB,
Fuseki). This F# project is the pure, provable core: the IR-to-RDF projection and
the L1–L4 sift ladder, where the category-theory structure earns compile-time
guarantees the Python version can only assert with tests.

```
dotnet run --project tools/ontology-sift/fsharp
```

Runs the **F# sift doctor**: it sifts the same risk/control fixtures as the Python
doctor and proves parity — the conformant fragment **snaps** (projected to canonical
RDF), the two violators **quarantine** at the same levels (L3 reasoner, L4 SHACL).

## Why F# (the category theory, made concrete)

| Concept | In the code | What it buys |
|---|---|---|
| **Coproduct** | `Stereotype` / `BfoClass` discriminated unions (`Ir.fs`) | A projection *out* of the union must define every arm. |
| **Functor** | `project : Fragment -> Triple list` (`Project.fs`) | Structure-preserving IR→RDF; total over the unions. |
| **Catamorphism** | `project` folds the fragment to triples | One canonical fold; `snap` is just this on a proven fragment. |
| **Result monad** | L1 in `sift` (`Sift.fs`) | An ill-formed fragment short-circuits — it can't be projected. |
| **Validation applicative** | L2–L4 accumulate violations | Independent checks gather *all* failures, not just the first. |
| **Coproduct (outcome)** | `SiftOutcome = Snapped \| Quarantined` | Every consumer must handle both — no silent "maybe promoted". |

The headline guarantee is **`FS0025`-as-error** (see `OntologySift.fsproj`): add a
case to the `Stereotype` coproduct and the build **fails** until every projection
(`gufoIri`, the continuant check, …) handles it. "Snapped, not plausible" stops
being a runtime property you test for and becomes one the compiler enforces.

## Boundary with the Python shell

This core is deliberately IO-free. It does not embed, call the gateway, or touch a
database — those stay in `backend-core` (the live `/api/v1/ontology/*` routes). The
intended integration is functional-core / imperative-shell: the shell parses input
and performs effects; the core decides *snap vs quarantine* and *what the canonical
triples are*. Wiring the shell to call this core (vs. the generator emitting it) is
the next ADR-033 increment.
