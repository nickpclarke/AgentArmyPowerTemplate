---
title: ARC-ADR-044 — Untool: Ontology-Orchestrated Swarm Intelligence
status: Proposed
deciders: [nicky]
date: 2026-05-30
tags: [untool, ontology, swarm, mcp, skills, holons, emissions, jit-provisioning, architecture]
related: [ARC-ADR-016, ARC-ADR-023, ARC-ADR-037, ARC-ADR-038, ARC-ADR-042]
supersedes: []
superseded-by: []
---

# ARC-ADR-044 — Untool: Ontology-Orchestrated Swarm Intelligence

## Context and Problem Statement

The fleet has been converging on a product called **untool** through several conceptual layers. Each prior framing was a true partial picture:

1. A curated MCP tool re-exposure (e.g. wpcom domain availability under a fleet name)
2. A three-tier cognitive harness (unauth / fleet-credentialed / per-user-credentialed)
3. A just-in-time discovery + attachment runtime that abstracts across ecosystems
4. **The full picture (this ADR):** conversational swarm intelligence with right-sized teams of skilled-up tooled-up agents, orchestrated by an ontological hypergraph in-memory system that abstracts across all agent API schemas and dynamically provisions tools/skills, for individuals/groups/humans/agents in sync/async, where tools/agents/skills are first-class holons in the ontology with signed traceable emissions and fingerprints.

We need a single architectural commitment that names the orchestrator, the object model, and the verifiability story, so v1 build work can begin without re-deriving the design.

## Decision Drivers

- **Architectural coherence with existing fleet** — must compose with the ontology pipeline (ARC-ADR-016, ARC-ADR-038), temporal pulse (ARC-ADR-042), credentials-broker (ARC-ADR-037), container tiering (ARC-ADR-023), and the platform self-model.
- **Cross-ecosystem reach** — must work across Claude, Copilot, Gemini, ChatGPT, and custom APIs without bespoke per-ecosystem orchestration code.
- **Verifiable execution** — every action must be addressable, signed, replayable, scoped.
- **"Don't have to think about it" UX** — capabilities surface invisibly when needed; no tool-picker, no auth nag mid-flow, no schema-bloat overflow.
- **Sync + async unified** — one runtime for live chat, durable async swarms, and mixed-mode collaboration.
- **Right-sizing** — minimize cost × time × risk subject to the goal; not maximalist multi-agent.
- **Alignment with Conversational Swarm Intelligence (Rosenberg, Unanimous AI)** — nested deliberation, conviction-weighted aggregation, synthesis-as-action, cross-talk between peer subswarms, and escalation of stuck decisions must be expressible without architectural change. See `obsidian/labs/AgentArmyLabs/Conversational-Swarm-Intelligence-Mapping.md` for the concept map.

## Considered Options

### A. Static curated bundle (the "marketplace plugin" framing)

Pre-curate which tools/skills exist; ship as one or more plugins; users install what they want.

- **Pros:** simple to ship; clear value ladder; auth tiers easy to reason about.
- **Cons:** doesn't deliver "don't have to think about it"; doesn't extend across ecosystems automatically; doesn't enable swarm composition; treats agents and tools as different kinds of things.

### B. JIT capability matcher (intent → match → attach)

A runtime that watches intent, federates over ecosystems' indexes, and attaches capabilities just in time. Single-agent-centric.

- **Pros:** delivers the UX promise; cross-ecosystem; progressive disclosure native.
- **Cons:** no team composition; no shared world model; no verifiable execution beyond per-tool logging; tools and agents stay separately modelled.

### C. **Ontology-orchestrated swarm with holon object model (CHOSEN)**

The orchestrator is the existing ontological hypergraph. Agents, tools, skills, and emissions are typed holons in that graph. Right-sized team composition is a set-cover query over holons. Cross-ecosystem support is via ApiBinding holons. JIT provisioning is the runtime side of the orchestration query. Every action emits a signed, fingerprinted, scope-tagged Emission holon, forming a replayable DAG.

- **Pros:** all of B's wins, plus:
  - Reuses the ontology investment as the orchestration plane.
  - Agents and tools are the same kind of thing — composability is free.
  - Verifiable execution (emissions + fingerprints) comes near-free from the holon model.
  - Sync/async unify because the DAG is the conversation.
  - Right-sized teams are graph queries, explainable and tuneable.
  - Shared world model is the ontology — the deepest cognitive strategy.
- **Cons:** five net-new build buckets (~5 sprints to v1). Requires extending the ontology with Agent/Tool/Skill/Emission kinds. Has three live unresolved design decisions (see "Open Decisions" below).

## Decision

**Adopt Option C — Ontology-Orchestrated Swarm Intelligence with Holon Object Model — as the architecture for untool.**

The full architectural detail and rationale is captured in the labs synthesis note:
`obsidian/labs/AgentArmyLabs/Untool-Ontology-Orchestrated-Swarm-Intelligence.md`

### Core commitments

1. **The orchestrator is the ontological hypergraph** — not a custom control-flow framework. Three queries (role fit, capability provisioning, emission causality) drive the entire runtime loop.
2. **Agent, Tool, Skill, Emission are typed Kinds in the ontology** — same Holon meta-model, with subkinds, phases, roles, relators, modes, qualities, and events.
3. **Capabilities are JIT-provisioned per-agent-per-turn** by the orchestrator, with credential resolution via the existing broker (ARC-ADR-037) and identity-tier alignment per the three-tier auth model.
4. **Every action produces an Emission holon** that is content-addressed, signed by emitter fingerprint, scope-tagged, and chained by trigger relations into a replayable DAG.
5. **Cross-ecosystem agents are typed once** as a Kind; each ecosystem (Claude, Copilot, Gemini, ChatGPT, fleet) is an ApiBinding holon attached to the Kind. The composer picks bindings as a sub-query.
6. **The emission DAG IS the conversation** — sync, async, individual, group, mixed-mode collapse to scope policies over one substrate.
7. **Right-sized team composition is set cover with cost + trust constraints** over the typed holon graph; the JIT-attach matcher is the special case of team size 1.
8. **Trust is a Mode that propagates along the emission DAG** — claims from unverified sources inherit low trust; downstream agents see it and mark their own emissions accordingly. Hallucination quarantine falls out: an emission with no upstream tool-call trigger is a pure model claim.
9. **Nested swarm dynamics per CSI lineage (Rosenberg)** — subswarms `partOf` parent swarms; `Conviction` is a Mode distinct from `Trust` (strength of position vs. trust in source); `Synthesis` and `DeliberationRound` are Event Kinds; `CrossTalk` reifies peer-subswarm interaction as `{subswarmA, subswarmB, sharedHolons, scopeBridge}`; `SwarmEscalation` is a Decision Artifact Subkind. The team composer recurses to produce tree-of-subswarm structures for multi-subgoal goals; the flat composer (size 2–5) and JIT-attach matcher (size 1) become special cases. Full concept map in `Conversational-Swarm-Intelligence-Mapping.md`.

## Open Decisions (escalated as separate Decision Artifacts on the board)

### Decision A — Where the ontological hypergraph lives at runtime

- **A1.** Process-local in-memory per swarm session, persisted to ArcadeDB on close
- **A2.** ArcadeDB as the live graph, every emission written through
- **A3.** Hybrid: hot subgraph in-memory, cold archive in ArcadeDB, projection lattice between

*Stakes: physical architecture; locks downstream choices. Escalate to hitl-coordinator as Decision Artifact.*

### Decision B — Holon identity model

- **B1.** Cryptographic content hash (pure functional identity, hard to update, strong provenance)
- **B2.** UUID + version chain (familiar, flexible, explicit lifecycle)
- **B3.** W3C DID (heavyweight, interop with the broader verifiable-AI-agent ecosystem)

*Stakes: determines interop with future verifiable-agent-identity standards. Escalate as Decision Artifact.*

### Decision C — First swarm shape to ship

- **C1.** Solo-with-team (one user, JIT swarm forms around their conversation)
- **C2.** Async-durable (swarm runs against an issue/goal for hours/days)
- **C3.** Group-sync (multiple humans + multiple agents in one shared conversation)

*Stakes: order of work; C1 backloads collab UX, C2 lights up emission-DAG-as-state, C3 is the wow but operationally hardest. Escalate as Decision Artifact.*

### Decision D — Conviction weighting curve *(CSI)*

- **D1.** Linear — balanced; the parent emission is the conviction-weighted mean of children. Neutral default.
- **D2.** Sigmoid — biases toward strong-conviction minority positions; a single highly-convicted "block this" subswarm can dominate.
- **D3.** Quadratic — favors broad mild conviction over narrow strong conviction; consensus-seeking.

*Stakes: shapes whether swarm dynamics converge to consensus or amplify polarization. The same swarm produces different decisions under different curves. Product-defining; not a tuning knob. Escalate as Decision Artifact.*

## Consequences

### Positive

- Single coherent orchestration plane (the ontology) replaces ad-hoc per-domain routing.
- Verifiable execution (signed emissions) emerges from the data model, not bolted on.
- Cross-ecosystem support is structural, not a feature flag.
- Swarm intelligence becomes operationally meaningful — distributed cognition over a typed shared world model.
- Strong defensible product claim: "every capability your swarm uses is an addressable, signed, replayable, schema-typed object in your private knowledge graph."

### Negative / Costs

- Five net-new build buckets (emissions store, team composer, binding selector, trust propagation, JIT provisioning runtime). Estimated 5 sprints to v1 if partly parallel.
- Ontology investment now serves runtime in addition to design; performance budget for orchestration queries must be enforced (sub-300ms per loop tick).
- Three foundational decisions (A/B/C above) must be resolved before commitment-grade build work begins.
- Surface area for security review grows substantially — emission signing, trust propagation rules, scope enforcement at graph-query time all need formal review.

### Neutral

- Plugin marketplaces become *target ecosystems* untool federates over, not *the* distribution model. The untool plugin itself ships the runtime; the content of what it attaches is open.
- Existing fleet substrates (`abstraction-mcp`, `credentials-broker`, `llm-gateway`, `local-embedder`, `forge`, `runbook-orchestrator`) all map cleanly onto specific untool roles — no major rewrites, mostly extension.

## Validation / Spike

Before commitment-grade build work, run the **right-sized team composer spike** (see `obsidian/labs/AgentArmyLabs/Untool-Team-Composer-Spike.md`):

- Stub 5 agent holons, 10 tool holons, 3 capability types directly in ArcadeDB
- Implement the set-cover composer in <50 lines
- Hand-author 3 goal scenarios; verify the composer produces the team you'd choose
- If the composer feels wrong, the data model is wrong — fix that before continuing

A spike outcome of "feels right with minor weight tuning" green-lights the ADR for build. A spike outcome of "the model can't express the constraint" is a forcing function to revise the Kind/Relator inventory before any code commits to it.

## Links

- Labs synthesis: `obsidian/labs/AgentArmyLabs/Untool-Ontology-Orchestrated-Swarm-Intelligence.md`
- CSI concept mapping: `obsidian/labs/AgentArmyLabs/Conversational-Swarm-Intelligence-Mapping.md`
- Spike plan: `obsidian/labs/AgentArmyLabs/Untool-Team-Composer-Spike.md`
- Emission policy starter: `untool/ontology/emissionPolicy.ts`
- ARC-ADR-016 — ontology representation (reification + hyperedges)
- ARC-ADR-023 — container tiering strategy
- ARC-ADR-037 — BYO-credentials broker
- ARC-ADR-038 — pace-layered RDF↔LPG projection
- ARC-ADR-042 — temporal persistence (stamp model)
- [[Ontology-Pipeline]]
- [[Reification-and-Hyperedges]]
- [[Factory-Loop-Test-Infrastructure]]
- [[Agentic Loop Primitives]]
- [[Evidence-Backed Aggregates]]

## External references

- **Louis Rosenberg, PhD** — Stanford; founder of Unanimous AI (2014); platforms UNU, ENSO, Hyperchat. CSI as a research field is his lineage; this ADR encodes his vocabulary in our ontology, but the conviction-weighted swarm-aggregation pattern is original to him.
