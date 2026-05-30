---
title: Conversational Swarm Intelligence — Mapping to Untool
status: synthesis
created: 2026-05-30
session: awesome-yonath-f38cd6
related-adrs: [ARC-ADR-044]
related-notes: [[Untool-Ontology-Orchestrated-Swarm-Intelligence]], [[Untool-Team-Composer-Spike]], [[Reification-and-Hyperedges]], [[Agentic Loop Primitives]], [[Evidence-Backed Aggregates]]
external-credit: Louis Rosenberg (Stanford; Unanimous AI; platforms UNU, ENSO, Hyperchat)
tags: [untool, ontology, swarm, csi, rosenberg, conviction, deliberation, holons]
---

# Conversational Swarm Intelligence — Mapping to Untool

> **Purpose.** Map **Louis Rosenberg's Conversational Swarm Intelligence (CSI)** vocabulary onto the typed entities of untool's ontology so the relationship between the two is precise, citable, and buildable. This is the dedicated cross-reference for [[Untool-Ontology-Orchestrated-Swarm-Intelligence]] and ARC-ADR-044 Core Commitment 9.

---

## Rosenberg & CSI in one paragraph

**Louis Rosenberg, PhD** (Stanford) founded **Immersion Corporation** in the early 1990s (the haptics company), then in 2014 founded **Unanimous AI** to research and productize **Swarm Intelligence** — real-time amplification of collective wisdom inspired by the closed-loop biology of bee swarms, fish schools, and bird flocks. His platforms **UNU**, **ENSO**, and most recently **Hyperchat** let groups of humans (and increasingly humans-plus-AI-agents) deliberate in synchronous swarms, where contributions are weighted by **conviction** (how strongly the participant holds the position) rather than raw vote. **Conversational Swarm Intelligence (CSI)** is Rosenberg's framing for the LLM-augmented version: small subgroups of ~5–7 participants converse in parallel, AI-mediated **Synthesis** agents compress each subgroup's deliberation into upward-passing summaries, and a hierarchical tree of swarms produces decisions that outperform both individuals and simple polls. The published results (election prediction, market forecasts, medical diagnosis, sports outcomes) show measurable wisdom-amplification — small swarms regularly beat experts.

This note maps CSI onto untool's existing ontology so the design from ARC-ADR-044 honors that lineage and integrates with it cleanly.

---

## Concept mapping table

| CSI concept (Rosenberg) | Untool encoding |
|---|---|
| **Swarm** — a group deliberating toward a goal in real time | `Swarm` Kind (already in ontology) |
| **Subswarm** — a smaller group inside a larger tree of swarms | `Swarm` holon with `partOf` relation to parent `Swarm` |
| **Tree of subswarms** (hierarchical AND networked) | Recursion in the right-sized team composer; reified by `Engagement` relator for each parent-child pairing |
| **Cross-talk** — peer subswarms sharing findings without merging | New Relator `CrossTalk{subswarmA, subswarmB, sharedHolons, scopeBridge}` — a typed bridge so two scopes can read specific shared holons without scope-bleed |
| **Conviction-weighted contribution** | New Mode `Conviction` on each `Emission` — distinct from `Trust` (trust in the source) — captures how strongly the emitter held the position |
| **Synthesis** — compressing N deliberations into 1 upward summary | New Event Kind `Synthesis` — a typed action whose emitter is in a `synthesis-role`; payload is the compressed parent emission citing all child emissions in its `trigger` chain |
| **Synthesis-role** — the agent whose explicit job is to synthesize | New Role `synthesis-role` (OntoUML stereotype: Role) on an Agent within a parent Swarm context |
| **Deliberation round** — time-boxed window for parallel deliberation | New Event Kind `DeliberationRound` with `duration` Quality; relies on temporal pulse (ARC-ADR-042) for "at this point in deliberation" queries |
| **Wisdom amplification** — the swarm outperforms its members | Operational effect of the above, *not* a typed entity; the composer can produce **swarm-of-swarms** (3 parallel teams converging via Synthesis) for high-stakes goals |
| **Escalation to higher level** — subswarm gives up, parent decides | New Subkind `SwarmEscalation` of `Decision Artifact` (per existing ARC-ADR-001 / `hitl-coordinator` pattern) — surfaces to parent Swarm rather than human directly |
| **Convergence** — the swarm settling on a position | Operational effect; trackable as decreasing `Conviction` variance across `Synthesis` emissions over successive `DeliberationRound` events |
| **Polarization** — the swarm splitting | Operational effect; trackable as increasing `Conviction` variance with stable positions; the *weighting curve* (linear / sigmoid / quadratic) on `Conviction` shapes whether this happens |
| **Humans as peer participants** | Already true in untool — `User` is a Kind; their emissions carry `Conviction` and `Trust` like any other emitter |

---

## What this changes about untool (compared to ARC-ADR-044 pre-CSI)

**Architecture: unchanged.** The substrate (ontological hypergraph, holon model, emission DAG, right-sized teams, HITL Decision Artifacts) all stays as in ARC-ADR-044 Core Commitments 1–8.

**Additions:** ARC-ADR-044 Core Commitment 9 names the typed extensions — `Conviction` Mode, `Synthesis` + `DeliberationRound` Event Kinds, `CrossTalk` Relator, `SwarmEscalation` Subkind, and `synthesis-role` Role. These extend the existing OntoUML inventory; nothing replaces.

**Decision raised:** ARC-ADR-044 Open Decision **D** — the **conviction weighting curve** (linear / sigmoid / quadratic). This is genuinely novel from CSI: the shape of the conviction-aggregation function determines whether swarm dynamics converge to consensus or amplify polarization. Linear is balanced; sigmoid biases toward strong-conviction minority positions; quadratic favors broad-conviction majority positions. The choice is product-defining.

**Team composer change:** the composer recurses for multi-subgoal goals, producing a tree-of-subswarms instead of a flat team. The JIT-attach matcher (team size 1) and the flat team composer (team size 2–5) become special cases of the same recursive set-cover algorithm.

---

## Worked example: PR review as a 3-subswarm CSI deliberation

Goal G: *"Review pull request #370 end-to-end before auto-merge fires — security, architecture, ops."*

The team composer's recursion produces:

```
Swarm: "PR-370-review" (parent)
├── synthesis-role agent (1)
├── Subswarm: Security
│   ├── code-reviewer-agent (lens: vulnerability classes)
│   ├── security-auditor-agent (lens: SAST/DAST signals)
│   └── synthesis-role agent (subswarm-local)
├── Subswarm: Architecture
│   ├── architect-reviewer-agent (lens: cross-cut + tier fit)
│   ├── ontologist-ufo-agent (lens: OntoUML correctness — this PR adds Kinds)
│   └── synthesis-role agent (subswarm-local)
└── Subswarm: Ops
    ├── deployment-engineer-agent (lens: rollback safety)
    ├── observability-engineer-agent (lens: traces post-deploy)
    └── synthesis-role agent (subswarm-local)
```

### Flow

1. **DeliberationRound 1** (e.g., 90 seconds parallel): each subswarm's specialist agents emit findings. Each finding is an Emission with: `emitter`, `payload`, `trust` (high — these are platform agents), `conviction` (varies — "this is a real bug" vs "this could potentially be a problem").

2. **CrossTalk emerges.** The Security subswarm finds a vulnerability that also bears on Architecture (e.g., the new `CrossTalk` Relator itself needs scope-policy review). A `CrossTalk{security-subswarm, arch-subswarm, finding-holon, scope=both}` relator is emitted — both subswarms now see the finding without merging into one team.

3. **Subswarm Synthesis emissions.** Each subswarm's synthesis-role agent emits one `Synthesis` Emission summarizing all findings + their conviction-weighted aggregation. Trust + conviction propagate per the policy (`untool/ontology/emissionPolicy.ts`).

4. **Parent Synthesis.** The parent synthesis-role agent reads the three child `Synthesis` emissions plus the `CrossTalk` relators. Three possible parent-emission shapes:
   - **High convergent conviction:** parent emits an "approve" recommendation — auto-merge can proceed.
   - **Disagreement with low conviction:** parent emits a "soften" recommendation — typically a comment on the PR rather than a block.
   - **Disagreement with high conviction:** parent emits a `SwarmEscalation` Decision Artifact → `hitl-coordinator` surfaces it to the owner, blocking auto-merge.

5. **Conviction-curve effect.** With a linear weighting curve, the parent emission is the conviction-weighted mean of children. With a sigmoid curve, a single high-conviction "block this" subswarm dominates. With a quadratic curve, broad mild conviction wins over narrow strong conviction. **The same swarm produces different decisions under different curves** — which is why Decision D matters.

### Why this is structurally different from "have three agents review the PR"

Without CSI typing, three reviewer agents just produce three review emissions and *some other code* synthesizes them — usually a hardcoded merge rule. With CSI typing in the ontology:

- The Synthesis is **emitted by a typed agent in a typed role**, so it's auditable, replayable, signed
- The CrossTalk is **a first-class relator with provenance**, not an ad-hoc shared variable
- The conviction-weighted aggregation is **a Mode propagation along the emission DAG**, queryable retrospectively
- The escalation path is **a typed Subkind of Decision Artifact**, integrating with the existing `hitl-coordinator` pattern instead of being a one-off escape hatch

That's the difference between "we have a multi-agent reviewer" and "we have a *swarm* that deliberates."

---

## See also

- [[Untool-Ontology-Orchestrated-Swarm-Intelligence]] — the synthesis note this maps into
- [[Untool-Team-Composer-Spike]] — H4 (stretch) validates the recursive composer that produces these subswarm trees
- [[Reification-and-Hyperedges]] — the data-model substrate for `CrossTalk` and `Engagement` relators
- [[Agentic Loop Primitives]] — scenario-as-policy is the gate where swarm deliberation outputs land
- [[Evidence-Backed Aggregates]] — state-as-evidence-proven mirrors the emission DAG's audit semantics
- ARC-ADR-044 — Untool: Ontology-Orchestrated Swarm Intelligence (Core Commitment 9 names the typed extensions; Open Decision D names the weighting-curve choice)
- ARC-ADR-016 — reification + hyperedges (substrate for CrossTalk)
- ARC-ADR-042 — temporal persistence (the DeliberationRound `duration` Quality lives here)

---

## External references (Rosenberg / CSI)

- **Unanimous AI** — the company Rosenberg founded; the source of UNU, ENSO, and Hyperchat
- **UNU** — the original Swarm AI platform; demonstrated real-time human-swarm prediction across domains
- **ENSO** — Swarm AI for enterprise decisioning
- **Hyperchat** — the CSI platform; LLM-augmented conversational swarm deliberation at scale
- Peer-reviewed publications on **wisdom amplification** in human swarms across prediction, diagnosis, and forecasting domains (AAAI, IEEE, ACM venues)

> **Attribution note.** This mapping is untool's encoding of CSI vocabulary into our ontology, authored by the AgentArmy fleet. The CSI framing, Swarm AI mechanics, and the conviction-weighted aggregation pattern are Rosenberg's original work. Untool implements its own version of those ideas in a typed ontological substrate; any deviation from the published CSI semantics (e.g., the exact Conviction weighting curve, the SwarmEscalation routing through `hitl-coordinator`) is untool's choice, not Rosenberg's.
