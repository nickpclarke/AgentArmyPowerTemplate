---
title: Untool — Ontology-Orchestrated Swarm Intelligence
status: synthesis
created: 2026-05-30
session: awesome-yonath-f38cd6
related-adrs: [ARC-ADR-016, ARC-ADR-023, ARC-ADR-037, ARC-ADR-038, ARC-ADR-042, ARC-ADR-044]
related-notes: [[Ontology-Pipeline]], [[Reification-and-Hyperedges]], [[Factory-Loop-Test-Infrastructure]], [[OOP Patterns for Agentic Platforms]], [[Scenario Objects]], [[Policy Objects]], [[API Strategy — Internal, External, Open & Monetized]]
tags: [untool, ontology, swarm, mcp, skills, holons, emissions, jit-provisioning, cognitive-harness]
---

# Untool — Ontology-Orchestrated Swarm Intelligence

> **One-liner.** Untool is a dynamic way of discovering and attaching domain-empowered skills and tools easily from across ecosystems so you don't have to think about it — it creates conversational swarm intelligence with right-sized teams of skilled-up tooled-up agents, orchestrated by our ontological hypergraph in-memory system that abstracts across all the agent API schemas and dynamically provisions tools, skills, etc. For individuals, groups, humans, and agents — sync or async. Tools are part of the object model and have trusted traceable emissions and fingerprints. They are [[holons]].

This note is the canonical synthesis from session **awesome-yonath-f38cd6** (2026-05-30). It collapses five conversational reframes into one coherent architecture and links to the existing labs notes and ADRs that supply the pieces.

---

## The architecture stack

```
┌────────────────────────────────────────────────────────────────────────────┐
│  CONVERSATIONAL SURFACE  (human↔human, human↔agent, agent↔agent)           │
│  sync (chat, voice, screen-share) │ async (issues, threads, emissions log) │
└────────────────────────────┬───────────────────────────────────────────────┘
                             │ utterances, intents, asks
                             ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  SWARM COMPOSITION                                                          │
│  right-sized team of agents instantiated from holon templates,             │
│  each agent receiving the JIT skill/tool bundle that fits its role         │
└────────────────────────────┬───────────────────────────────────────────────┘
                             │ team graph + role bindings
                             ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  ONTOLOGICAL HYPERGRAPH (the orchestrator — in-memory + persistent)        │
│  UFO/OntoUML stereotypes · holons · reified n-ary relations ·              │
│  temporal pulse · RDF↔LPG pace-layered projection                          │
│                                                                             │
│  ⟨ everything below is a TYPED ENTITY in this graph ⟩                      │
└──────┬───────────┬───────────┬───────────────┬─────────────────────────────┘
       │           │           │               │
       ▼           ▼           ▼               ▼
   ┌──────┐   ┌────────┐   ┌─────┐       ┌──────────────────────┐
   │Agents│   │ Skills │   │Tools│       │ Emissions (signed,   │
   │ as   │   │ as     │   │ as  │       │ fingerprinted, typed │
   │holons│   │ holons │   │holons│       │ events in the graph)│
   └───┬──┘   └────┬───┘   └──┬──┘       └──────────┬───────────┘
       │           │           │                     │
       └───────────┼───────────┘                     │
                   ▼                                  ▼
        ┌─────────────────────────┐      ┌──────────────────────────┐
        │  SCHEMA ABSTRACTION     │      │  PROVENANCE / TRUST      │
        │  unifies Claude /       │      │  every emission has a    │
        │  Copilot / Gemini /     │      │  cryptographic           │
        │  ChatGPT / custom API   │      │  fingerprint + chain of  │
        │  shapes into one        │      │  custody                 │
        │  conceptual model       │      │                          │
        └─────────────────────────┘      └──────────────────────────┘
                   │
                   ▼
        ┌─────────────────────────────────────────────────────────────┐
        │  JIT PROVISIONING                                            │
        │  the ontology decides WHO needs WHAT capability NOW,        │
        │  binds via credentials-broker (per-user) or fleet identity,  │
        │  attaches into the model session, decays on completion       │
        └─────────────────────────────────────────────────────────────┘
                   │
                   ▼
        ┌─────────────────────────────────────────────────────────────┐
        │  CAPABILITY UNIVERSE  (the substrate)                        │
        │  MCP servers · plugin markets · Anthropic skills ·          │
        │  fleet images · public APIs · user's own tools              │
        └─────────────────────────────────────────────────────────────┘
```

The thing that distinguishes this from every existing multi-agent framework (CrewAI, AutoGen, LangGraph, OpenAI Custom GPTs) is the **middle row**: the ontology *is* the orchestrator, and every agent/skill/tool is a typed holon inside it. Those other frameworks treat the agent graph as a control-flow data structure. Untool treats it as a **first-class ontological model** — the same kind of thing as our domain model, our platform self-model, and our user's organizational model.

> [!insight] Architectural through-line
> Our [[Ontology-Pipeline]] and our **untool runtime orchestrator** are the *same kind of model*. The platform has a twin in the ontology; agents have twins in the ontology; tools have twins in the ontology. One graph, many sub-models. Reasoning over "what agent for this task" is the same operation as "what container for this workload" — both are role-fit queries against holons.

---

## The five-reframe progression (how we got here)

The session built this up in stages. Each was true; each was a layer of the same system.

| # | Reframe | What it added |
|---|---|---|
| 1 | **Concrete starter:** the wpcom domain-availability MCP tool | Showed that capabilities decompose into public-availability + user-credentialed-action surfaces |
| 2 | **MCP chaining + curation:** can we re-expose tools as fleet-named?  | Identified pass-through proxy / façade / composed-pipeline as the three chaining shapes; introduced four credential models |
| 3 | **Cognitive harness with three tiers:** Tier-A unauth, Tier-B fleet-credentialed, Tier-C per-user-broker | Aligned identity-vs-billing; mapped to existing `abstraction-mcp` + `credentials-broker` + `llm-gateway` |
| 4 | **JIT discovery + attach across ecosystems:** "don't have to think about it" | Made untool a recommender for capabilities with intent → match → attach → decay loop |
| 5 | **Ontology-orchestrated swarm intelligence:** the actual product | The hypergraph IS the orchestrator; agents/tools/skills/emissions are typed holons; right-sized team composition is a graph query; cross-API abstraction is just multiple bindings per holon |

---

## Core primitives (in OntoUML terms)

Everything in untool is an OntoUML-stereotyped entity in the hypergraph.

| Stereotype | Examples in untool |
|---|---|
| **Kind** | Agent, Tool, Skill, Capability, Emission, User, Swarm |
| **Subkind** | ConversationalAgent, MutatingTool, ReadOnlyTool, EphemeralSkill, SwarmEscalation *(CSI — subkind of Decision Artifact)* |
| **Phase** | active-in-conversation, suspended, decayed, retired |
| **Role** | researcher-in-swarm, broker-for-credential, reviewer-on-PR, synthesis-role *(CSI)* |
| **Relator** | Engagement, Authorization, ToolBinding, EmissionChain, CrossTalk *(CSI — `{subswarmA, subswarmB, sharedHolons, scopeBridge}`)* |
| **Mode** | Trust, Permission, Confidence, Conviction *(CSI — strength of position vs. trust in source)* |
| **Quality** | latency, cost, fitScore, deliberationDuration |
| **Event** | ToolCall, MessageEmission, TeamFormation, DecayTick, Synthesis *(CSI)*, DeliberationRound *(CSI)* |

See [[Reification-and-Hyperedges]] for the rationale behind reifying multi-party relations like `ToolBinding {agent, tool, credential, scope}` instead of fanning them out as binary edges.

---

## Holon model

A holon is a first-class typed entity in the hypergraph with these properties:

```
Holon {
  identity:        UUID                       // stable, addressable
  kind:            Agent | Tool | Skill | …   // OntoUML stereotype
  fingerprint:     SignedHash                 // content + provenance
  capabilities:    [→ CapabilityHolon]        // what it can do
  partOf:          [→ Holon]                  // which wholes it belongs to
  composedOf:      [→ Holon]                  // its parts
  bindings:        [→ ApiBinding]             // how to invoke it (per-ecosystem)
  emissionPolicy:  EmissionPolicy             // what it produces, how it's signed
  trustGrade:      Trust                      // platform / official / community / unverified
  decayPolicy:     DecayPolicy                // when does this de-attach
  temporal:        TemporalPulse              // valid-from / valid-until (see ARC-ADR-042)
}
```

**The deep move:** Tool, Agent, and Skill holons are the same *kind of thing* in the model. They differ in subtypes and capability relations, not in their place in the type hierarchy. That's what makes "agents call agents" and "agents call tools" the same operation under the hood. And it's what makes "tool is currently part of agent A's bundle" and "agent A is currently part of swarm S" the same `partOf` relation.

### Why "holon"?

Koestlerian: a holon is **both a whole and a part**. An agent is whole (it has its own goals, skills, history) AND part (it serves a swarm). Tools are whole (signed, addressable, callable) AND part (they belong to agents/skills/plans). The reified-and-hyperedges substrate ([[Reification-and-Hyperedges]]) is the data-model expression of this duality — the same node participates in multiple n-ary relations without losing identity.

---

## Three orchestration queries (the loop)

The runtime issues three queries against the hypergraph, constantly:

1. **Role fit** — "Given Goal G and current Swarm S, which Agent holons score highest as candidates for open Role R?"
2. **Capability provisioning** — "Given Agent A in Role R, what Tool/Skill holons are required, available, and credential-resolvable for User U?"
3. **Emission causality** — "Given Emission E, what other emissions depend on it, and what subsequent actions does the graph project?"

Those three queries are **the entire orchestrator loop**, expressed as graph operations over a typed ontology. SHACL/Datalog rules drive them; the temporal pulse (ARC-ADR-042) makes the answers time-aware ("at this moment in the conversation, given what's already been emitted…").

---

## Emissions, fingerprints, trust

Every action in untool produces an **Emission** holon:

```
Emission {
  identity:    UUID
  emitter:     → Holon                     // which agent/tool emitted this
  trigger:     → Emission                  // what caused this (chains form DAGs)
  payload:     CIDv1                       // content-addressed payload (IPLD-style)
  signature:   SignedBy(emitter.fingerprint)
  temporal:    { at: timestamp, validUntil?: timestamp }
  trustChain:  [→ Authorization]           // reified n-ary: who allowed this
  scope:       Scope                       // public, swarm-private, user-private
}
```

This gives us, near-free:

1. **Full replay** — any swarm session reconstructable turn-by-turn from its DAG
2. **Attribution** — "which agent introduced this claim?" walks the trigger chain
3. **Trust propagation** — claims by unverified community tools inherit low trust; downstream agents that use them mark their own emission accordingly
4. **Hallucination quarantine** — an emission with no upstream tool-call trigger is a *pure model claim* — flaggable, citable, optionally filterable
5. **Differential privacy / scope enforcement** — graph-traversal check at query time
6. **Async resumption** — paused swarm can resume at turn 48 because all state is in the DAG

> [!insight] Three product surfaces, one data model
> Emissions-as-holons collapses what frameworks usually split into three: **observability** (logs/metrics), **state** (memory/scratchpad), and **provenance** (audit). They're all the same emission DAG, queried differently. One model, three views.

---

## Right-sized team composition

The composer runs as a graph query — set cover with cost and trust constraints:

```
Given:  goal G, user U, conversation context C, budget B
Find:   minimal set of agent holons {A₁, ..., Aₙ} such that
        - ∀ subgoal g of G: ∃ Aᵢ with capability(Aᵢ) ⊇ capabilities_required(g)
        - ∑ cost(Aᵢ) ≤ B
        - team coordination cost (edges in collaboration graph) is bounded
        - trust(Aᵢ) ≥ minimum_trust_for(g) for all g
        - U's preferences (preferred ecosystems, banned agents, working style) honored
```

NP-hard in general but trivial at small sizes (which is what "right-sized" means: typically 1–5 agents). The JIT matcher from reframe 4 is the special case where team size is 1.

### Typical team shapes the algorithm produces

| Goal shape | Typical team | Coordination |
|---|---|---|
| Single-shot information lookup | 1 agent + 1–3 tools | None |
| Multi-step plan execution | 1 orchestrator + N specialists, async | Plan → fan-out → join |
| Cross-functional review (e.g. PR) | 3–5 reviewers from different lenses | Independent then synthesis |
| Long-running async project | Persistent swarm with rotating membership | Board + handoff emissions |
| Live conversation with humans | 1 conversational front + background helpers | Front filters; helpers stream context |

Same algorithm, all five shapes — they're minimum-cost subgraphs of the same ontology.

---

## Conversational surface: sync + async unified

**The emission DAG IS the conversation.** That's how one product serves individuals/groups/humans/agents in sync/async.

- **Sync** (live chat) = appending to the DAG with low latency
- **Async** (issue thread, durable swarm) = appending over hours/days, participants subscribe to scopes
- **Mixed** (some humans live, some agents async) = same DAG, different presence states
- **Group** = same DAG, multiple humans + multiple agents, access by scope
- **Individual** = scope = `{user_only}`, same machinery

> [!insight] Conversation as DAG, not list
> Lists assume a single timeline and serial speakers. DAGs let two agents work in parallel on subgoals, let a human jump in mid-stream, let an async resumption splice cleanly back into a live session. Threading is *natural*, not bolted on. This is also why the temporal pulse (ARC-ADR-042) is more than a timestamp scheme — it makes "at this point in the conversation" queryable, including belief revision.

---

## Nested swarms and conviction-weighted deliberation

The right-sized team composer above produces a single team for a single goal. But many real swarm tasks aren't single-team — they need **multiple parallel subgroups deliberating independently, synthesizing upward, and cross-talking on shared findings**. That structure is the field of **Conversational Swarm Intelligence (CSI)**, developed by **Louis Rosenberg** (Stanford; founder of Unanimous AI; built UNU → ENSO → Hyperchat as platforms for human + AI swarm deliberation). CSI extends biological swarm intelligence (bees, fish, birds) with language-based deliberation, where small subgroups converse, compress, and pass insight up a tree of swarms.

Untool's substrate already supports CSI — the emission DAG, holon model, and HITL Decision Artifacts give us the bones. What's missing are the **typed mechanics of nested deliberation**. The Core primitives section above adds them:

| CSI concept (Rosenberg) | Untool encoding |
|---|---|
| **Tree of subswarms** (hierarchical AND networked) | Swarm holons that are `partOf` parent Swarm holons; team composer recurses |
| **Conviction-weighted contributions** | New Mode `Conviction` — strength of *position*, distinct from `Trust` in source |
| **Synthesis as first-class action** | New Event Kind `Synthesis` — one agent's explicit job is to compress N child Emissions into 1 parent Emission |
| **Cross-talk between peer subswarms** | New Relator `CrossTalk` reifying `{subswarmA, subswarmB, sharedHolons, scopeBridge}` |
| **Escalation of stuck decisions** | New Subkind `SwarmEscalation` of Decision Artifact — when a subswarm can't resolve, the parent swarm receives it as deliberation input |
| **Time-boxed deliberation rounds** | New Event Kind `DeliberationRound` with `duration` Quality; the existing temporal pulse (ARC-ADR-042) makes "at this point in deliberation" queryable |
| **Wisdom amplification** (swarm outperforms individuals) | Team composer optionally produces a *swarm-of-swarms*: 3 parallel teams converge via Synthesis for high-stakes goals |

> [!insight] Conviction ≠ trust
> The deepest refinement is that **conviction is not trust**. Trust says "how much do I believe the source." Conviction says "how strongly does the source itself feel." A high-trust agent saying "maybe X" deserves different weight than the same agent saying "definitely X." Splitting them is one new Mode in the ontology and unlocks the entire CSI aggregation pattern — without it, a swarm averages noise; with it, a swarm finds the position that has both grounded support *and* held conviction.

**Worked micro-example: a "review PR #370" goal as a 3-subswarm CSI deliberation.**

The composer produces three peer subswarms — `Security`, `Architecture`, `Ops` — each with 2–3 specialist agents and a Synthesis-role agent. Each subswarm deliberates for one DeliberationRound (e.g., 90 seconds). Each Synthesis agent emits a single Synthesis emission summarizing the subswarm's findings + conviction-weighted concerns. A parent Synthesis agent reads all three child Synthesis emissions plus any CrossTalk relators (e.g., a Security finding that also bears on Architecture is a `CrossTalk{security-subswarm, arch-subswarm, finding-holon}`). If conviction is high and convergent, the parent emits an approval recommendation. If two subswarms disagree with high conviction, the parent emits a SwarmEscalation Decision Artifact for human resolution. Identical mechanics to a CSI Hyperchat session — but typed in our ontology and replayable from the emission DAG.

This pattern is what makes *"shared meaning passing between groups with escalation and cross-talk of key decision flows"* structural rather than aspirational. The full concept mapping and a deeper worked example live in [[Conversational-Swarm-Intelligence-Mapping]].

---

## Cross-API abstraction (Claude / Copilot / Gemini / ChatGPT / custom)

Each agent ecosystem is a **binding** on the agent Kind. The Kind describes the agent abstractly: capabilities, costs, latency profile. The binding says: how do you actually invoke this Kind in this ecosystem?

```
Agent: { kind: "code-reviewer-agent",
         capabilities: [code-review, diff-analysis, security-scan],
         bindings: [
           { ecosystem: claude,       via: anthropic-api,  promptStyle: xml-tags },
           { ecosystem: copilot,      via: @-mention,      promptStyle: markdown },
           { ecosystem: gemini,       via: gemini-api,     promptStyle: gemini-flavor },
           { ecosystem: untool-fleet, via: ACA-spoke,      promptStyle: ontology-native }
         ] }
```

When the swarm-composer picks this agent, it picks a binding based on user preference, cost, latency, capability fit, and trust. Same role-fit query, applied to bindings. Skill/tool abstraction works identically.

---

## What we already have vs. net-new (delta against current fleet)

| Layer | Already exists | Net-new |
|---|---|---|
| Ontology core (UFO/OntoUML, BFO interop) | ✓ `ontologist-ufo`, `ontologist-bfo`, gUFO projection, RDF↔LPG (ADR-038) | – |
| Hypergraph storage | ✓ ArcadeDB (LPG), Fuseki (RDF) | Extend ontology to *agents/tools/skills* schemas |
| Temporal pulse | ✓ ARC-ADR-042 (in PR #367) | – |
| Holon model | ✓ §1.6 of recent untool foundations | Extend to Agent/Tool/Skill kinds |
| Reification + hyperedges | ✓ ADR-016, [[Reification-and-Hyperedges]] | – |
| Platform self-model | ✓ recent merge #362 | Mirror pattern for **agent self-model** |
| Generator-first compilation | ✓ generator-first doctrine + `forge` | Generate per-binding API adapters |
| BYO credentials broker | ✓ ARC-ADR-037, `/api/v1/credentials/*` | Wire to JIT provisioning |
| MCP fleet substrate | ✓ `abstraction-mcp`, `llm-gateway`, `local-embedder`, all ACA images | – |
| HITL Decision Artifacts | ✓ ARC-ADR-001, `hitl-coordinator` | Use for swarm decision-point escalation |
| Async work surface | ✓ GitHub Projects board, board-sync | Project emission DAG onto issues |
| **Trace & emissions** | ⚠ logging exists; emissions-as-holons not yet | **NEW: emissions store + sign + DAG semantics** |
| **Right-sized team composer** | ⚠ `agent-organizer` agent exists; algorithm not formalized | **NEW: set-cover query with constraints** |
| **Cross-ecosystem bindings** | ⚠ ad-hoc routing in CLAUDE.md | **NEW: typed Binding holon + binding selector** |
| **Trust grading + propagation** | ⚠ trust tier concept; not computed | **NEW: trust as Mode that propagates along emission DAG** |
| **JIT provisioning runtime** | ⚠ partial in `abstraction-mcp` | **NEW: complete loop integrated with broker** |

**Five net-new buckets**, each ~1–2 sprints. Five sprints to a credible v1 if partly parallel.

---

## Cognitive strategies enabled

| Strategy | What it does | Why this architecture enables it |
|---|---|---|
| **Shared world model** | Every agent in the swarm reads/writes the same ontology — they don't have to re-explain context | Ontology IS shared memory; emissions are how agents update it |
| **Specialization without isolation** | Agents have narrow skills but see the whole graph | Holons `partOf` other holons → narrow scope, wide context |
| **Disagreement as data** | Two agents emit conflicting claims; ontology preserves both with provenance; downstream agent decides | Emission DAG records both; trust propagation chooses |
| **Tacit handoff** | Async agent picks up where sync left off, no explicit serialization | Emission DAG is the state; pick up by scope subscription |
| **Adversarial verification at low cost** | Spin a 3-agent jury for any high-stakes emission | Right-sized composer with a "verify-this-claim" goal template |
| **User as a peer agent** | The human is a holon in the swarm, emissions normalized | Conversational surface treats user emissions identically |
| **Memory that compounds** | Episodic graph grows with use; future queries find prior patterns | The graph is persistent; everything is queryable |
| **Tree-of-deliberation** *(CSI)* | Subswarms deliberate independently, synthesize upward, cross-talk on shared findings, escalate stuck decisions to parent | Nested Swarm holons + Synthesis Event + CrossTalk Relator + SwarmEscalation Subkind make this structural, not bolted-on |

> [!insight] What "swarm intelligence" actually means here
> Not marketing — operational: **multiple specialized cognitive units sharing a typed world model, coordinated by inference over that model, with the ability to disagree, verify, and converge.** "Shared world model" is the piece other frameworks get wrong. They give agents shared *memory* (a scratchpad), shared *context* (a prompt blob), or shared *plans* (a DAG of steps). Untool gives them a shared *ontology* — typed entities with relations, queryable, projectable. The agents don't have to align on representation; the ontology is the representation.

---

## Four open decisions (escalated to ARC-ADR-044)

1. **Where the ontological hypergraph lives at runtime** — process-local in-memory / ArcadeDB live / hybrid hot+cold
2. **What counts as a holon's identity** — content-hash / UUID+version / DID
3. **First swarm shape to ship** — solo-with-team / async-durable / group-sync
4. **Conviction weighting curve** *(CSI)* — linear / sigmoid / quadratic. Shapes whether swarm dynamics converge to consensus or amplify polarization.

See ARC-ADR-044 for the formal decision artifacts.

---

## v1 → v3 staging plan

- **v1 — Single-ecosystem JIT attach.** Untool federates only fleet's catalog (Tier A+B). Intent → match → attach works end-to-end. Validates the loop. ~4 weeks.
- **v2 — Federate public MCP registries.** Add 2–3 ecosystem crawlers (Anthropic skills, mcp.so, one plugin market). Trust tier defaults: fleet=high, official=medium, community=low (opt-in). **The first "magic" moment.** ~6 weeks.
- **v3 — OpenAPI auto-wrap + episodic memory.** Any spec becomes an ephemeral tool; per-user memory makes untool *yours* in 2 weeks of use. **The moat appears.** ~10 weeks.

In parallel from week 1: trust ladder, trace UI, broker UX for Tier-C.

---

## See also

- [[Ontology-Pipeline]] — the pipeline this orchestrator runs on top of
- [[Reification-and-Hyperedges]] — the data-model substrate for holons (and for `CrossTalk` relator)
- [[Factory-Loop-Test-Infrastructure]] — the test-loop pattern that becomes the swarm verification loop
- [[OOP Patterns for Agentic Platforms]] — the object-model lineage
- [[Agentic Loop Primitives]] — scenario-as-policy: the gate/decision surface where team composition is enforced
- [[Evidence-Backed Aggregates]] — state-as-evidence-proven: audit-logged decisions overlap with the emission DAG
- [[Scenario Objects]] — what scenarios look like as holons
- [[Policy Objects]] — policies (like emission policies) as ontological entities
- [[Conversational-Swarm-Intelligence-Mapping]] — focused CSI ↔ untool concept mapping; credits Louis Rosenberg's lineage
- [[API Strategy — Internal, External, Open & Monetized]] — the API tier model that untool's three-tier auth aligns with
- ARC-ADR-016 — ontology representation (reification + hyperedges)
- ARC-ADR-023 — container tiering strategy
- ARC-ADR-037 — BYO-credentials broker
- ARC-ADR-038 — pace-layered RDF↔LPG projection
- ARC-ADR-042 — temporal persistence (stamp model)
- ARC-ADR-044 — Untool ontology-orchestrated swarm intelligence (this design)
