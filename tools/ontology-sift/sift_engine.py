"""ARC-ADR-032 — the sift-sort engine (reference implementation / thin slice).

The thesis: an LLM (Cerebras) only PROPOSES; the formal layer DISPOSES. A candidate
fragment is admitted to the canonical graph only when it is *proven* — schema-valid
(L1), free of OntoUML anti-patterns (L2), reasoner-consistent across the dual
gUFO+BFO grounding (L3), and SHACL-conformant (L4) — and then re-checked by the
authoritative Fuseki sieve. Anything that cannot be proven within the repair budget
lands in QUARANTINE (a state on the holographic graph), never in canonical.

This module is deterministic and offline: the proposer is pluggable (see
proposer.py). The production loop lives in backend-core and swaps in the live
Cerebras proposer + the ArcadeDB holographic LPG + the Fuseki gate; the validation
ladder here is the same one it reuses.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

from jsonschema import Draft202012Validator
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, RDFS, OWL
import owlrl
import pyshacl

HERE = Path(__file__).resolve().parent
DISCIPLINE = HERE / "discipline"

EX = Namespace("https://agentarmy.dev/ontology-sift/data#")
GUFO = Namespace("http://purl.org/nemo/gufo#")
BFO = Namespace("http://purl.obolibrary.org/obo/bfo#")
PROV = Namespace("http://www.w3.org/ns/prov#")
SIFT = Namespace("https://agentarmy.dev/ontology-sift/prov#")

# Lifecycle states a candidate occupies on the holographic graph (ADR-032 facet C/D).
PROPOSED, SIFTING, SNAPPED, QUARANTINED = "proposed", "sifting", "snapped", "quarantined"


def _local(uri) -> str:
    s = str(uri)
    return s.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


@dataclass
class LevelResult:
    level: str
    ok: bool
    detail: str = ""


@dataclass
class Candidate:
    """A node in the holographic graph: the fragment plus the whole context needed
    to judge it (state, per-level results, violations, repair history)."""
    fragment_id: str
    state: str
    levels: list = field(default_factory=list)
    violations: list = field(default_factory=list)
    repair_round: int = 0
    snapped_to: str | None = None

    def as_dict(self) -> dict:
        d = asdict(self)
        return d


class Discipline:
    """The 'box' the proposer must stay inside: the IR schema, the merged upper
    ontology (gUFO-lite + BFO-lite, incl. the cross-grounding + disjointness), and
    the SHACL shapes. ADR-032 facet B (dual grounding)."""

    def __init__(self, root: Path = DISCIPLINE):
        self.schema = json.loads((root / "ir-fragment.schema.json").read_text(encoding="utf-8"))
        self._schema_validator = Draft202012Validator(self.schema)
        self.upper = Graph()
        self.upper.parse(root / "upper" / "gufo-lite.ttl", format="turtle")
        self.upper.parse(root / "upper" / "bfo-lite.ttl", format="turtle")
        self.shapes = Graph()
        self.shapes.parse(root / "shapes" / "gufo.shapes.ttl", format="turtle")

    # ---- L1 syntactic -------------------------------------------------------
    def l1_schema(self, fragment: dict) -> LevelResult:
        errs = sorted(self._schema_validator.iter_errors(fragment), key=lambda e: e.path)
        if errs:
            msg = "; ".join(f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errs[:5])
            return LevelResult("L1-schema", False, msg)
        return LevelResult("L1-schema", True, "well-formed IR; valid stereotypes")

    # ---- L2 OntoUML anti-patterns (structural, what the schema can't express) ----
    def l2_antipatterns(self, fragment: dict) -> LevelResult:
        ids = {e["id"] for e in fragment["entities"]} | {r["id"] for r in fragment["relations"]}
        problems = []
        for r in fragment["relations"]:
            for role in r["roles"]:
                if role["filler"] not in ids:
                    problems.append(
                        f"relator '{r['id']}' role '{role['role']}' binds undeclared entity '{role['filler']}'"
                    )
        if problems:
            return LevelResult("L2-antipattern", False, "; ".join(problems))
        return LevelResult("L2-antipattern", True, "role bindings reference declared entities")


def project(fragment: dict) -> Graph:
    """Project an IR fragment to RDF so the reasoner + SHACL can judge it. Dual
    typing (gUFO + BFO); relations reified as gufo:Relator with gufo:mediates edges
    (hyperedge-as-vertex, ADR-016)."""
    g = Graph()
    for e in fragment["entities"]:
        iri = EX[e["id"]]
        g.add((iri, RDF.type, GUFO[e["gufo"]]))
        g.add((iri, RDF.type, BFO[e["bfo"]]))
        g.add((iri, RDFS.label, Literal(e["label"])))
    for r in fragment["relations"]:
        iri = EX[r["id"]]
        g.add((iri, RDF.type, GUFO["Relator"]))
        g.add((iri, RDF.type, BFO[r["bfo"]]))
        g.add((iri, RDFS.label, Literal(r["label"])))
        for role in r["roles"]:
            g.add((iri, GUFO["mediates"], EX[role["filler"]]))
    return g


def l3_reason(data: Graph, disc: Discipline) -> LevelResult:
    """L3 — merge fragment with the upper ontology, materialize subclass/type
    closure, then check no individual lands in two disjoint classes. This is where
    the gUFO and BFO classifications are forced to AGREE: a candidate whose gUFO
    type implies Occurrent while its BFO type implies Continuant is inconsistent,
    not merely implausible."""
    g = Graph()
    for t in disc.upper:
        g.add(t)
    for t in data:
        g.add(t)
    owlrl.DeductiveClosure(owlrl.RDFS_Semantics).expand(g)
    problems = []
    for a, _, b in disc.upper.triples((None, OWL.disjointWith, None)):
        both = set(g.subjects(RDF.type, a)) & set(g.subjects(RDF.type, b))
        for x in both:
            if str(x).startswith(str(EX)):
                problems.append(f"{_local(x)} is inferred to be both {_local(a)} and {_local(b)} (disjoint)")
    if problems:
        return LevelResult("L3-reasoner", False, "; ".join(sorted(set(problems))))
    return LevelResult("L3-reasoner", True, "consistent under gUFO+BFO (no disjoint-class clash)")


def l4_shacl(data: Graph, disc: Discipline) -> LevelResult:
    conforms, _results, text = pyshacl.validate(
        data, shacl_graph=disc.shapes, inference="none", advanced=True, debug=False
    )
    if not conforms:
        # Keep the human-readable message lines, drop pyshacl's banner noise.
        msg = "; ".join(
            ln.strip() for ln in text.splitlines() if "Message:" in ln
        ) or text.strip().splitlines()[0]
        return LevelResult("L4-shacl", False, msg)
    return LevelResult("L4-shacl", True, "conforms to gUFO SHACL shapes")


def lineage(fragment: dict, proposer_name: str, prompt_hash: str) -> Graph:
    """PROV-O lineage: every snapped triple traces to its source span, the proposing
    activity (proposer + prompt hash), so the canonical commit is auditable. ADR-032 D5."""
    pg = Graph()
    frag = SIFT[fragment["fragment_id"]]
    src = SIFT["source-" + fragment["source"]["doc"].replace(".", "-")]
    act = SIFT["propose-" + fragment["fragment_id"]]
    pg.add((src, RDF.type, PROV.Entity))
    pg.add((act, RDF.type, PROV.Activity))
    pg.add((act, SIFT.proposer, Literal(proposer_name)))
    pg.add((act, SIFT.promptHash, Literal(prompt_hash)))
    pg.add((frag, PROV.wasGeneratedBy, act))
    pg.add((frag, PROV.wasDerivedFrom, src))
    for item in fragment["entities"] + fragment["relations"]:
        iri = EX[item["id"]]
        pg.add((iri, PROV.wasDerivedFrom, src))
        for span in item["spans"]:
            pg.add((iri, SIFT.span, Literal(f"{fragment['source']['doc']}#{span[0]}-{span[1]}")))
    return pg


class Engine:
    """The loop: propose -> sift (L1-L4) -> snap (project to canonical RDF + lineage)
    OR repair (<= K) OR quarantine. Holographic state is written to out/."""

    def __init__(self, proposer, out_dir: Path, repair_budget: int = 2, disc: Discipline | None = None):
        self.proposer = proposer
        self.out = out_dir
        self.K = repair_budget
        self.disc = disc or Discipline()
        self.candidates: list[Candidate] = []
        (self.out / "canonical").mkdir(parents=True, exist_ok=True)
        (self.out / "lineage").mkdir(parents=True, exist_ok=True)

    def _sift(self, fragment: dict) -> tuple[bool, list[LevelResult], list[str]]:
        levels: list[LevelResult] = []
        # L1 short-circuits — an ill-formed fragment can't be projected.
        l1 = self.disc.l1_schema(fragment)
        levels.append(l1)
        if not l1.ok:
            return False, levels, [l1.detail]
        l2 = self.disc.l2_antipatterns(fragment)
        levels.append(l2)
        data = project(fragment)
        l3 = l3_reason(data, self.disc)
        levels.append(l3)
        l4 = l4_shacl(data, self.disc)
        levels.append(l4)
        violations = [lv.detail for lv in levels if not lv.ok]
        return all(lv.ok for lv in levels), levels, violations

    def _snap(self, fragment: dict, cand: Candidate) -> None:
        data = project(fragment)
        # Authoritative gate: in this slice the in-process pyshacl IS the gate; the
        # production loop re-runs the Fuseki sieve (sieve.sh) here before promoting.
        canon = self.out / "canonical" / f"{fragment['fragment_id']}.ttl"
        data.bind("ex", EX); data.bind("gufo", GUFO); data.bind("bfo", BFO)
        data.serialize(destination=canon, format="turtle")
        lin = lineage(fragment, self.proposer.name, self.proposer.prompt_hash(fragment))
        lin.bind("prov", PROV); lin.bind("sift", SIFT); lin.bind("ex", EX)
        lin_path = self.out / "lineage" / f"{fragment['fragment_id']}.prov.ttl"
        lin.serialize(destination=lin_path, format="turtle")
        cand.state = SNAPPED
        cand.snapped_to = str(canon.relative_to(self.out))

    def run(self, fragments: list[dict]) -> list[Candidate]:
        for fragment in fragments:
            cand = Candidate(fragment_id=fragment.get("fragment_id", "<no-id>"), state=PROPOSED)
            self.candidates.append(cand)
            current = fragment
            while True:
                cand.state = SIFTING
                passed, levels, violations = self._sift(current)
                cand.levels = [asdict(lv) for lv in levels]
                cand.violations = violations
                if passed:
                    self._snap(current, cand)
                    break
                if cand.repair_round >= self.K:
                    cand.state = QUARANTINED  # ADR-032 D6: never auto-promote the unproven
                    break
                repaired = self.proposer.repair(current, violations)
                if repaired is None:
                    cand.state = QUARANTINED
                    break
                current, cand.repair_round = repaired, cand.repair_round + 1
        self._write_holographic()
        return self.candidates

    def _write_holographic(self) -> None:
        graph = {"states": {PROPOSED: 0, SIFTING: 0, SNAPPED: 0, QUARANTINED: 0},
                 "candidates": [c.as_dict() for c in self.candidates]}
        for c in self.candidates:
            graph["states"][c.state] = graph["states"].get(c.state, 0) + 1
        (self.out / "holographic.json").write_text(json.dumps(graph, indent=2), encoding="utf-8")
        manifest = {c.fragment_id: {"state": c.state, **self._hashes(c)} for c in self.candidates}
        (self.out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def _hashes(self, c: Candidate) -> dict:
        out = {}
        canon = self.out / "canonical" / f"{c.fragment_id}.ttl"
        if canon.exists():
            out["canonical_sha256"] = hashlib.sha256(canon.read_bytes()).hexdigest()
        lin = self.out / "lineage" / f"{c.fragment_id}.prov.ttl"
        if lin.exists():
            out["lineage_sha256"] = hashlib.sha256(lin.read_bytes()).hexdigest()
        return out
