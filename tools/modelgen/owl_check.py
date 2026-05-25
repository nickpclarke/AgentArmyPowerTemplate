#!/usr/bin/env python3
"""L3 verification — OWL consistency check for the generated middle-core model.

Loads the generated OWL TBox (`model-runtime.owl.ttl`) and the RDF fixture
(`model-runtime.fixture.ttl`, the ABox) and checks the consistency invariants the
TBox encodes:
  * no individual is asserted into two mutually-disjoint classes
    (owl:AllDisjointClasses / owl:disjointWith), and
  * every object-property triple respects its rdfs:domain / rdfs:range
    (honouring the rdfs:subClassOf hierarchy).

Pure rdflib (no Java reasoner) so it runs reliably in CI; this covers the OWL 2
RL subset the projection encodes. A full OWL 2 DL pass (e.g. HermiT) that also
proves class satisfiability/subsumption is a planned upgrade (see
planning/synthesis/RT-verification-levels.md). Diagnostics go to stderr.

Exit 0 = consistent, 1 = inconsistent, 2 = rdflib missing.
"""
from __future__ import annotations

import sys
from pathlib import Path

GENERATED = Path(__file__).resolve().parents[2] / "templates" / "middle-core" / "generated"


def main() -> int:
    owl_path = GENERATED / "model-runtime.owl.ttl"
    fixture_path = GENERATED / "model-runtime.fixture.ttl"
    try:
        from rdflib import Graph, RDF, RDFS, OWL
        from rdflib.collection import Collection
    except ImportError:
        print("owl_check: rdflib not installed (pip install rdflib)", file=sys.stderr)
        return 2

    tbox = Graph().parse(owl_path, format="turtle")
    abox = Graph().parse(fixture_path, format="turtle")

    # subClassOf closure
    supers: dict = {}
    for child, _, parent in tbox.triples((None, RDFS.subClassOf, None)):
        supers.setdefault(child, set()).add(parent)

    def ancestors(cls):
        seen, stack = set(), [cls]
        while stack:
            for parent in supers.get(stack.pop(), ()):
                if parent not in seen:
                    seen.add(parent)
                    stack.append(parent)
        return seen

    def is_a(individual_types: set, cls) -> bool:
        return cls in individual_types or any(cls in ancestors(t) for t in individual_types)

    # disjoint class sets
    disjoint_sets: list[set] = []
    for node in tbox.subjects(RDF.type, OWL.AllDisjointClasses):
        members = tbox.value(node, OWL.members)
        if members is not None:
            disjoint_sets.append(set(Collection(tbox, members)))
    for a, _, b in tbox.triples((None, OWL.disjointWith, None)):
        disjoint_sets.append({a, b})

    # domain/range per object property
    domains = {p: d for p, _, d in tbox.triples((None, RDFS.domain, None))}
    ranges = {p: r for p, _, r in tbox.triples((None, RDFS.range, None))}

    # asserted individual types
    types: dict = {}
    for subj, _, obj in abox.triples((None, RDF.type, None)):
        types.setdefault(subj, set()).add(obj)

    errors: list[str] = []

    for individual, tset in types.items():
        for ds in disjoint_sets:
            clash = tset & ds
            if len(clash) > 1:
                errors.append(f"{individual} is in disjoint classes {sorted(str(c) for c in clash)}")

    for prop in set(domains) | set(ranges):
        dom, rng = domains.get(prop), ranges.get(prop)
        for subj, _, obj in abox.triples((None, prop, None)):
            if dom and subj in types and not is_a(types[subj], dom):
                errors.append(f"{subj} {prop} {obj}: subject violates domain {dom}")
            if rng and obj in types and not is_a(types[obj], rng):
                errors.append(f"{subj} {prop} {obj}: object violates range {rng}")

    if errors:
        print("OWL INCONSISTENT: fixture violates the model TBox:", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        return 1

    print(
        f"OWL consistent: {len(types)} individuals checked against "
        f"{len(disjoint_sets)} disjoint set(s) and {len(set(domains) | set(ranges))} object propert(ies)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
