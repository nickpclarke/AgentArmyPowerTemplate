# ontology-sift — the sift-sort authoring loop (ARC-ADR-032 thin slice)

Turns source documents into **proven, snapped-to-upper-ontology** structure — not
plausible-looking guesses. The reference implementation + the offline proof of the
loop from [ARC-ADR-032](../../docs/decisions/ARC-ADR-032-ontology-sift-sort-authoring-loop.md).

## The thesis

An LLM asked to "build an ontology" produces *plausible* output — fluent and
**unprovable**. This inverts that: **the LLM (Cerebras) only proposes; the formal
layer disposes.** A candidate is admitted only when it is *proven* — and every
admitted triple is traceable to its source span and the proof that admitted it.

```
 retrieve ─▶ FRAME (discipline box) ─▶ PROPOSE (Cerebras, structured IR)
                                            │  → holographic graph (state=proposed)
                                            ▼  state=sifting
   L1 JSON-Schema → L2 anti-pattern → L3 reasoner (gUFO ∧ BFO) → L4 SHACL
                                            │
              conforms? ── yes ─▶ SNAP: authoritative Fuseki gate
                  │ no                       → project to canonical RDF + PROV-O
            REPAIR (≤ K, Cerebras)           → state=snapped
                  │ can't snap
            state=quarantined  ◀── retained, queryable, never auto-promoted
```

- **Dual grounding** (ADR-032 facet B): every candidate carries *both* a gUFO and a
  BFO classification; L3 forces them to **agree** (a candidate whose gUFO type implies
  Occurrent while its BFO type implies Continuant is *inconsistent*, not just unlikely).
- **Holographic graph** (facet C): the staging layer is a property graph; the sift
  metadata (validation status, violations, repair history, classifications, spans)
  lives *on* the candidate. **Quarantine is a `state`, not a separate store.**
- **Hybrid validation** (facet A): cheap in-process tiers (pyshacl + owlrl) in the hot
  loop; the authoritative **Fuseki sieve** at the snap boundary.

## Run the proof

```bash
python doctor.py        # needs: rdflib, pyshacl, owlrl, jsonschema
```

Proves, deterministically and offline:

| fragment | outcome | gated at |
|---|---|---|
| `conformant` | **snaps** to canonical + PROV-O lineage | — |
| `violating-shacl` (under-mediated relator) | **quarantined** | L4 SHACL |
| `violating-reason` (gUFO/BFO disagree) | **quarantined** | L3 reasoner |

…and that **only proven fragments reach canonical**. Outputs land in `out/`
(gitignored): `holographic.json` (the working graph + states), `canonical/*.ttl`,
`lineage/*.prov.ttl`, `manifest.json` (content hashes).

## Layout

```
discipline/   the box the proposer must stay inside
  ir-fragment.schema.json     L1 — the structured shape Cerebras must emit
  upper/{gufo,bfo}-lite.ttl    tiny upper ontologies + the cross-grounding + disjointness
  shapes/gufo.shapes.ttl       L4 — SHACL conformance shapes
fixtures/     a tiny corpus + pre-baked proposals (one per outcome)
sift_engine.py  the loop: project → L1-L4 → snap | repair | quarantine → lineage
proposer.py     FixtureProposer (doctor) + GatewayProposer (live Cerebras via llm-gateway)
doctor.py       the offline proof
```

## Slice vs production

This is the **hub reference + proof**. The production loop is a backend-core service
(per ADR-030/032): it swaps `FixtureProposer` → `GatewayProposer` (live Cerebras +
Tavily via the llm-gateway), the in-memory holographic graph → an **ArcadeDB LPG**,
and re-runs the real **Fuseki sieve** as the authoritative gate before promoting to
the canonical Fuseki graph that [forge](../../docs/decisions/ARC-ADR-029-agentarmy-forge-codegen-container.md)
consumes. The validation ladder here is the one that service reuses.
