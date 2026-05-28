# ARC-ADR-032 — Ontology Sift-Sort Authoring Loop: Cerebras Proposes, the Formal Layer Disposes, over a Holographic Staging Graph

| Field | Value |
|---|---|
| ID | ARC-ADR-032 |
| Status | Accepted |
| Date | 2026-05-28 |
| Deciders | Hub owner (Nicky Clarke) — chose all four facets + the v0.2 refinements; accepted 2026-05-28 |
| Supersedes | — (refines [ARC-ADR-030](ARC-ADR-030-data-to-ontology-ingestion-pipeline.md) i3; resolves its OQ1/OQ3/OQ5 and **diverges** on OQ2) |
| Superseded by | — |
| Tags | ontology, ingestion, llm, cerebras, tavily, shacl, reasoner, gufo, bfo, cco, holographic-graph, provenance, sift-sort, lineage, backend-core |

---

## Context and Problem Statement

[ARC-ADR-030](ARC-ADR-030-data-to-ontology-ingestion-pipeline.md) decided the data→ontology pipeline lives in **backend-core**, gate-first: messy sources → extraction → staging → SHACL gate → canonical Fuseki graph → forge ([ADR-029](ARC-ADR-029-agentarmy-forge-codegen-container.md)). It deliberately left the **unstructured / LLM extraction phase (i3)** as the high-risk piece, with open questions on extractor placement (OQ1), staging-graph modeling (OQ2), provenance vocabulary (OQ3), and the HITL threshold (OQ5).

This ADR specifies **how i3 works**, because the naïve approach fails the hub owner's hard requirement. An LLM asked to "build an ontology from these documents" produces **plausible** output — fluent, well-formed, and *unprovable*. The requirement is the opposite: **accurate, provable ontologies that are snapped to a real mid/upper-level ontology, with lineage back to source.**

The core problem: an LLM that is the *arbiter of truth* will always drift toward plausibility. The structure of the system, not the prompt, must guarantee correctness.

**Decision: how is the LLM phase structured so that LLM non-determinism never produces a "plausible but unprovable" ontology — and so the loop is fast enough to iterate heavily, configurable, and lineage-complete?**

---

## Decision Drivers

| # | Driver |
|---|---|
| D1 | **The LLM proposes; the formal layer disposes.** Acceptance must be a *proof* — reasoner-consistent + SHACL-conformant + competency-questions-satisfied — never LLM self-confidence. The model only searches inside the box the upper ontology defines. |
| D2 | **Snap to a real upper ontology.** Every candidate is classified under a foundational discipline and admitted only if it conforms to that discipline's axioms. "Derived/plausible" is rejected by construction. |
| D3 | **Fast iteration (Cerebras).** The sift-sort is a loop that runs many times. Propose + repair (Cerebras) and the inner validation tiers must be cheap; expensive authoritative checks run only at the boundary. |
| D4 | **Rich working substrate.** Sifting and sorting candidates needs per-candidate metadata — confidence, per-level validation status, violation reports, candidate classifications, repair history, alignment scores. That is property-graph-shaped, not bare-triple-shaped. |
| D5 | **Lineage is first-class (PROV-O).** Every canonical triple traces to its source span, the proposing activity (model + prompt hash), and the validation reports that admitted it — auditable and tamper-evident. |
| D6 | **No plausible leakage.** A candidate that cannot be *proven* never enters the canonical graph. Non-snapping candidates are retained, visible, and re-drivable — not silently promoted or silently dropped. |
| D7 | **Configurable & pluggable.** Upper-ontology set, mid-ontologies, which validation levels are enforced, repair budget `K`, acceptance thresholds, and the non-snap policy are configuration, not code forks. |

---

## Decisions (four facets)

### Facet A — Validation substrate: **hybrid (fast local + authoritative Fuseki gate)** ✅

The hot loop validates **in-process** (`pyshacl` + `rdflib`/`owlrl` reasoner) each repair round — no network round-trip — and a candidate is only declared *snapped* when it clears the **authoritative Fuseki sieve** (`templates/fuseki-ontology-image`, `sieve.sh`) at the boundary. Fast inner loop, independently-proven final commit.

- *Rejected* A2 (Fuseki every iteration): a container round-trip per repair round fights D3.
- *Rejected* A3 (in-process only): no independent authoritative gate weakens D1/D6.

### Facet B — Upper-ontology grounding: **dual gUFO + BFO/CCO from day one** ✅

Every candidate carries **both** a gUFO/OntoUML classification *and* a BFO 2020 + CCO classification, and "snap" requires conformance to **both** profiles. This is maximal provability (two independent foundational checks cross-validate) and matches the north-star "emit both alignments" rule. The reasoner profile is pluggable per [ADR-019](ARC-ADR-019-ontology-reasoning-layer.md) (gUFO ‖ BFO).

- *Rejected* B1 (gUFO first, BFO later): the hub owner chose dual grounding up front for cross-checkable proof; the cost (double validation surface) is accepted.

### Facet C — Staging substrate: **holographic graph = ArcadeDB LPG** (quarantine as a state) ✅

The working/staging layer is a **labeled property graph in ArcadeDB**, called the **holographic graph**, *not* a Fuseki named graph. Each candidate node holds the *whole context needed to judge it* — provenance spans, dual candidate classifications (gUFO + BFO), per-level validation status, violation reports, repair-round count, CQ coverage, embedding-alignment scores, and a lifecycle `state` — as **properties**. Candidate relators are vertices with role-binding edges (hyperedge-as-vertex, reusing [ADR-016](ARC-ADR-016-ontology-representation-reification-hyperedges.md), already built in middle-core #61).

The sift-sort is fundamentally *ranking/filtering candidates by rich, mutating metadata* — natural on an LPG (properties queried/sorted directly), awkward in RDF (every annotation needs reification ceremony). **Quarantine is a `state` value on the holographic graph, not a separate store.** The canonical graph stays **Fuseki RDF** (semantics + SHACL + reasoning — the arbiter). **Snap is a deterministic projection** holographic-LPG → canonical-RDF, honouring the north-star rule "do not collapse the runtime graph and the semantic ontology."

- *Rejected* C1 (Fuseki named-graph staging — ADR-030 OQ2's lean): RDF reification ceremony for per-candidate sift metadata is the wrong ergonomics for the working loop. **This ADR diverges from ADR-030 OQ2 on the working layer; the canonical layer is unchanged (Fuseki).**

### Facet D — Non-snap disposition: **quarantine state in the holographic graph** ✅

A candidate that cannot snap within the repair budget `K` is set to `state=quarantined` in the holographic graph, **retaining its full violation report and sift metadata**. It is queryable ("everything stuck + why"), re-drivable when new evidence/repairs arrive, and **never auto-promotes** to canonical. HITL escalation (a Decision Artifact, [ARC-ADR-001](ARC-ADR-001-hitl-decision-point-pattern.md)) becomes an *optional* action on the quarantine queue rather than the default path.

**Human-review face (reconciles ADR-030 OQ2 for the review side).** The holographic LPG is the *working* substrate (rich, mutating sift metadata the loop needs). Quarantined candidates are additionally **projected into a Fuseki `quarantine` named graph** alongside their SHACL/reasoner reports, so a human reviews them with the **Fuseki UI / SPARQL** that already ships with the store — no bespoke review surface. So quarantine has two faces: machine-sift (LPG state) and human-review (Fuseki named graph). `staging`/`quarantine` and `canonical` are sibling named graphs in one Fuseki dataset (ADR-030's lean), cheap to promote between; approval still flows through a HITL Decision Artifact, not a Fuseki write.

- *Rejected* D1 (always escalate to HITL): too heavy as the default; HITL is opt-in on the quarantine queue.
- *Rejected* D3 (auto-discard): loses near-miss work and its provenance, violating D6's "retained + visible."

---

## The loop

```
 source (Tavily search/extract · backend-core file ingest)
        │
        ▼
 0 · FRAME — load the discipline box: upper-ontology vocab (gUFO + BFO/CCO),
        their SHACL shapes, the UFO anti-pattern catalog, a corpus glossary
        (taxonomist), + embeddings of existing terms (snap-to-existing, not mint)
        │
        ▼
 1 · PROPOSE (Cerebras, structured output) ──▶ candidates written to the
        HOLOGRAPHIC GRAPH (ArcadeDB LPG)              state = proposed
        entity+mandatory gUFO&BFO stereotype, relations reified as relators
        with role bindings, each citing its source span (lineage)
        │
        ▼  state = sifting
 2 · SIFT (in-process, cheap→dear)
        L1 JSON-Schema  → L2 OntoUML anti-pattern/rigidity-sortality
        → L3 OWL reasoner consistency (gUFO ∧ BFO)  → L4 pyshacl conformance
        each failure → a STRUCTURED violation report (axiom/shape, node, why)
        │
        ├── conforms ───────────────────────────────┐
        │                                            ▼
 3 · REPAIR (Cerebras, fed the violations)     4 · SNAP — authoritative
        reclassify / reify / split / fix card.       Fuseki sieve (sieve.sh)
        ≤ K rounds, then ▼                            + competency questions
        │                                            │  all pass?
   state = quarantined  ◀── can't snap ──┐           ├── yes ─▶ project
        (full violation report retained,  │          │         LPG → CANONICAL
         queryable, re-drivable, HITL-opt) │          │         RDF (Fuseki)
        └───────────────────────────────────┘          │         + PROV-O lineage
                                                       │         + emit
                                                       ▼         fleet.ontology.changed
                                              CANONICAL graph ─▶ snapshot (BE-7) ─▶ forge
```

**Why this yields "snapped, not plausible":** the LLM never widens what is true. It proposes inside the upper-ontology box (D1/D2); the reasoner + SHACL + CQs + the Fuseki gate decide (D1); failures become repair instructions, not accepted assertions (D3 facet); unprovable candidates are quarantined, never promoted (D6); and every admitted triple carries the proof + source span that admitted it (D5).

### The sort step — an evidence ladder before a human

Step 3 ("repair") is not only "patch the SHACL violation." Violations come in two flavours: **mechanical** (under-mediated relator, missing role binding — fast Cerebras repair) and **rigorous** (Kind vs Role? correct upper parent? is this the *same-as* an existing term?). Rigorous questions climb an **evidence ladder** before a candidate is quarantined or sent to a human — and crucially, **each rung's finding is attached as PROV-O evidence**, so resolving the question strengthens lineage rather than just unblocking:

1. **Mechanical repair** — Cerebras, fed the structured violation (cheap, the common case).
2. **Web search** — Tavily (`/v1/tools/search` + `/extract`, ARC-ADR-021) for an authoritative definition / usage to ground the classification; an embedding match (Cohere) proposes *snap-to-existing-term* over minting a duplicate.
3. **Stronger-model query** — escalate from fast Cerebras to a more capable model (e.g. Claude, also on the gateway) for the genuine judgment call.
4. **HITL** — only what evidence + models could not resolve reaches a human (Decision Artifact + the Fuseki quarantine view).

This keeps Cerebras as the fast bulk proposer/repairer while reserving slow/expensive resolution (search, big model, human) for the few rigorous cases — and turns "the model guessed" into "the model cited," feeding the *Evidence as a Primitive* north-star.

---

## Affected Layers / Repos

| Layer | Repo | Impact |
|---|---|---|
| backend-core | nickpclarke/backend-core | Hosts the loop: holographic-LPG schema + the propose→sift→repair→snap→lineage orchestrator; calls the llm-gateway (`/v1/chat/completions` Cerebras, `/v1/tools/search`+`/extract` Tavily, `/v1/embeddings` Cohere); projects snapped fragments to Fuseki canonical; emits `fleet.ontology.changed`. Implements ADR-030 i3. |
| hub | nickpclarke/AgentArmy | This ADR; the **discipline box** (IR fragment JSON-Schema, gUFO + BFO SHACL shapes, vendored/pinned upper-ontology ttl catalog, anti-pattern catalog); the runnable **doctor** + thin-slice fixture corpus. |
| fuseki-ontology-image | hub `templates/fuseki-ontology-image` | The **authoritative gate** — consumed unchanged (`sieve.sh` accept/reject, `emit.sh` CONSTRUCT). |
| persistence | ArcadeDB | Holographic LPG (staging) + vector index for term alignment; Fuseki holds canonical RDF. |
| (cross-cutting) | docs/contracts.md | New Registry row for the ontology authoring loop surface; ties to BE-7/BE-8. |
| (agents) | hub `.claude/agents/` | `ontologist-ufo`/`ontologist-bfo` author the SHACL shapes + anti-pattern catalog; `knowledge-engineer` owns reasoner runs + CQs; `taxonomist` mines the corpus glossary. |

---

## Open Questions

1. **Term identity resolution (ADR-030 OQ4).** Embedding-based "snap to an existing upper/mid-ontology term" vs minting a new subclass — the similarity threshold for auto-align vs propose-new.
2. **Quarantine re-drive.** Auto-retry a quarantined candidate when new evidence/repairs land, or only on explicit operator/HITL action? Lean: event-driven re-drive on new evidence for the same source span.
3. **BFO beyond OWL-DL.** BFO 2020's CLIF axioms exceed OWL 2 DL; the L3 reasoner covers the OWL projection, with Z3/SMT ([levels 5–6 of the north-star](../../obsidian/labs/AgentArmyLabs/Ontology-Pipeline.md)) deferred for the full CL axioms.
4. **Projection fidelity.** The deterministic holographic-LPG → canonical-RDF projection for *dual* profiles (emit both gUFO-OWL and BFO alignments + a documented divergence list, not a lossless round-trip).
5. **Repair budget `K` + acceptance thresholds.** Default `K`, CQ pass-rate bar, and embedding-alignment cutoff — start conservative, tune on the thin-slice corpus.

---

## Related Decisions

- **[ARC-ADR-030](ARC-ADR-030-data-to-ontology-ingestion-pipeline.md):** Parent — this ADR specifies its i3 phase and resolves OQ1 (Cerebras via llm-gateway), OQ3 (PROV-O), OQ5 (quarantine-state, HITL opt-in), and **diverges** on OQ2 (holographic LPG staging, not a Fuseki named graph).
- **[ARC-ADR-029](ARC-ADR-029-agentarmy-forge-codegen-container.md):** Forge — the downstream consumer of the canonical snapshot this loop produces.
- **[ARC-ADR-019](ARC-ADR-019-ontology-reasoning-layer.md):** Reasoning layer (Fuseki + pluggable gUFO‖BFO) — the authoritative gate + reasoner profiles.
- **[ARC-ADR-016](ARC-ADR-016-ontology-representation-reification-hyperedges.md):** Reification/hyperedges — candidate relators are vertices with role-binding edges in the holographic graph.
- **[ARC-ADR-021](ARC-ADR-021-llm-gateway.md):** LLM gateway — the policy-enforced egress for Cerebras/Tavily/Cohere calls.
- **[ARC-ADR-004](ARC-ADR-004-llm-provider-cerebras.md):** Cerebras provider — the fast proposer/repairer.
- **[ARC-ADR-022](ARC-ADR-022-event-bus-bridges.md):** Event bus — `fleet.ontology.changed` emit that triggers forge.
- **Labs north-stars:** *Ontology-Pipeline* (multi-representation, congruence-first), *Reification-and-Hyperedges*, *Evidence as a Primitive*.

---

## Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-28 | Claude Code (assisted) | Initial Proposed — sift-sort authoring loop (Cerebras proposes / formal layer disposes) over a holographic ArcadeDB LPG staging graph; four facets chosen by the hub owner; refines ADR-030 i3 |
| 0.2 | 2026-05-28 | Claude Code (assisted) | Refinements per hub owner: (a) quarantine projected to a Fuseki named graph for human review via the Fuseki UI/SPARQL — the holographic LPG stays the working substrate; (b) the sort step gains an evidence ladder (Cerebras mechanical repair → Tavily web search → stronger-model query → HITL), with each finding attached as PROV-O evidence |
| 0.3 | 2026-05-28 | Hub owner | **Accepted.** Thin slice proven (10/10 in `tools/ontology-sift/`). F# adopted for the IR→projections compiler core — see [ARC-ADR-033](ARC-ADR-033-fsharp-ontology-compiler-core.md) |
