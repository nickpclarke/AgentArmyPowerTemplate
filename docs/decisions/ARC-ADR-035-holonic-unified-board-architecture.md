# ARC-ADR-035: Holonic Unified Board Architecture — Graph-First, Human+Agent Collaboration

**Status:** DECIDED  
**Date:** 2026-05-29  
**Deciders:** Track A (Research-Analyst), Track B (Ontologist-UFO), Track C (Architect-Reviewer), User (nick@livecreative.com)  
**Affected:** AgentArmy platform board, UNTOOL orchestration, all spoke PM workflows

---

## Context

AgentArmy requires a unified work management board for humans and agents to collaborate across hub + spokes. Current GitHub Projects v2 serves the hub but lacks holonic decomposition, graph-native semantics, and domain-driven skill routing. Three parallel research tracks evaluated the design space:

- **Track A (Research-Analyst):** Competitive analysis, graph-native PM candidates, RBAC authority patterns
- **Track B (Ontologist-UFO):** UFO ontology model with SAFE+CMMI holon lattice, security model, event schema
- **Track C (Architect-Reviewer):** UNTOOL orchestration architecture, MCP tools, skill registry, deployment topology

This decision synthesizes all three tracks, resolves two architectural escalations, and specifies the technology stack for the build phase.

---

## Escalation 1: Epic Placement in Holon Lattice

**Question:** Should Epics only `componentOf` Program (spanning multiple PIs), or also `componentOf` Feature directly?

**Analysis:**

Track B proposed two lattice interpretations:

1. **Linear:** Program → PI → Feature → Story (Epics only at Program level, span multiple PIs)
2. **Branching:** Epics can also `componentOf` Feature directly (Epic = large Feature with sub-Features)

**Decision:** Adopt **branching lattice** with two Epic roles:

- **Program-level Epic** (`componentOf Program`): Spans multiple PIs, tracks capability delivery roadmap (e.g., "Devsecops Platform")
- **Feature-level Epic** (`componentOf Feature`): Groups large Features under a common narrative within a single PI (e.g., "AuthZ Hardening" as Epic → 3 child Features)

**Rationale:**
- SAFE specifies Features roll up to Epics (hierarchically flexible, not strictly linear)
- Holon part-whole allows this: each level is simultaneously whole (as a unit for its parent) and part (composed of children)
- Enables CMMI capability-modeling across both Program and Feature scopes (e.g., "AuthZ capability operates at both levels")
- Track A research confirmed no competitor handles this flexibility; custom build is justified

**Specification:**
```yaml
Epic:
  stereotypes: [«root», «Situation»]  # Root Epics have Program parent; Situation-stereotyped Epics within Feature scope
  parent: [Program | Feature]
  children: [PI (Program-Epic only) | Feature (Feature-Epic) | Story (rare, for grouping anomalies)]
  properties:
    title: string
    description: string
    acceptance_criteria: string[]
    cmmi_level_target: 0..5
    status: [backlog | scheduled | in_progress | review | done]
    owner: User
    created_at: datetime
    updated_at: datetime
    linked_decisions: Decision[]
    linked_blockers: Blocker[]
```

---

## Escalation 2: CMMI Level Representation

**Question:** Should CMMI level be a scalar enum property on Feature/Epic, or a reified «quality» moment in CMMI ontological space?

**Analysis:**

Track B escalated two approaches:

1. **Scalar property:** `cmmi_level: 0..5` directly on Feature (simpler, loses temporal/evidence grounding)
2. **Reified quality:** `CMMI_Assessment` as a «quality» moment with links to evidence, assessor, date (complex, audit-grade)

**Decision:** Adopt **hybrid approach**:

- **Current state:** Scalar property `cmmi_level_current: 0..5` on Feature (for queries, board filtering)
- **Provenance layer:** Reified `CMMI_Assessment` relator linking Feature → CMMI_ProcessArea, with:
  - `assessed_at: datetime`
  - `assessed_by: User | Agent`
  - `evidence: [Decision | Document | Event][]`
  - `confidence: 0.0..1.0`
  - `predecessor_assessment: CMMI_Assessment?` (for temporal chain)

**Rationale:**
- Scalar property enables fast board queries ("show Features at CMMI-2 or lower")
- Reified Assessment enables audit trail and evidence linking (compliance-auditor needs to justify why a Feature is CMMI-2)
- Event sourcing captures assessment mutations; materialized current_level serves the UI without constant graph traversal
- Track A research showed regulatory audits require evidence chains; PROV-O spine supports this

**Specification:**
```yaml
Feature:
  properties:
    # Current materialized state (for fast queries)
    cmmi_level_current: 0..5
    cmmi_assessed_date: datetime?
    cmmi_assessor: User | null
    # Linked provenance (via Event)
    cmmi_assessment_history: CMMI_Assessment[] # ordered by assessed_at descending

CMMI_Assessment:
  stereotypes: [«quality»]
  properties:
    feature: Feature
    cmmi_process_area: string  # e.g., "CM" (Configuration Management), "REQM" (Requirements Management)
    level: 0..5
    assessed_at: datetime
    assessed_by: User | Agent
    confidence: 0.0..1.0
    evidence_links: (Decision | Document | Event)[]
    notes: string
    predecessor: CMMI_Assessment?  # enables temporal chain queries
```

---

## Technology Stack — Recommended

Based on Track A research, Track B ontology, and Track C architecture:

### Data Layer: ArcadeDB (Multi-Model Graph)

**Why:**
- Multi-model (OpenCypher, SPARQL, documents, time-series) — supports both holon graphs and event sourcing
- Already in AgentArmy local stack (Docker in `templates/local-stack/`)
- Apache 2.0 license; no vendor lock-in
- SPARQL endpoint enables semantic queries (PROV-O provenance, SHACL validation)
- Time-series indexes support temporal CMMI assessment chains
- Horizontally scalable (sharding by tenant/holon-type)

**Not:** PostgreSQL (relational, holon part-whole requires recursive tree walks; limited SPARQL)  
**Not:** Stardog (excellent RDF/OWL, but enterprise-licensed; ArcadeDB sufficient for initial build)

### Ontology: UFO + SAFE + CMMI (Turtle/OWL)

**Artifacts:**
- UFO stereotypes: Kind, Subkind, Role, Phase, Relator, Quality, Mode, Event, Situation (OpenUFO v1.1)
- SAFE decomposition: Program, PI (Planning Interval), Feature, Story, Enabler
- CMMI process areas: CM, REQM, PP (Project Planning), PMC (Project Monitoring & Control), etc.
- Agent collaboration: CapabilityGrant (reified RBAC token), Decision (blocks/unblocks), Blocker (cross-holon dependency)
- Provenance: PROV-O (Agent, Entity, Activity, WasGeneratedBy, WasAssociatedWith)
- Validation: SHACL 1.2 shapes for holon invariants (e.g., "Story must have non-null acceptance_criteria")

**Storage location:** `/planning/ontology/` (checked into repo)  
**Formats:** Turtle (readable diff) + RDF/XML (ArcadeDB import) + JSON-LD (REST API serialization)

### Board REST API: Standard CRUD + Semantic Queries

**Spec language:** OpenAPI 3.1  
**Endpoints:**
- `GET /holons` — list all holons (filter by type, status, owner, team, cmmi_level)
- `POST /holons` — create new holon (Epics, Features, Stories, Decisions, Blockers)
- `GET /holons/{id}` — fetch holon + linked decisions/blockers/children/parent
- `PATCH /holons/{id}` — update holon properties (status, owner, cmmi_level_current)
- `GET /holons/{id}/subgraph` — fetch holon + entire subtree (for agent scoping)
- `GET /events` — event log (immutable; supports audit trail queries)
- `POST /decisions/{id}/resolve` — mark Decision as resolved (unblock linked holons)
- `POST /holons/{id}/capabilities/grant` — create CapabilityGrant (delegate scoped authority)
- `GET /sparql` — SPARQL query endpoint (for agents querying PROV-O chains, CMMI history, etc.)

**Authentication:** JWT (issued by UNTOOL after MCP handshake); edge validation via CF Access  
**Rate-limiting:** Per-principal, per-endpoint (agents get higher limits than humans; query-heavy SPARQL gets separate bucket)

### Agent Orchestration: UNTOOL as MCP Server

**Deployment:** Stateless application container (Azure Container Apps, GCP Cloud Run)  
**Backing store:** Git-backed skill registry (skills as Helm charts + manifests in `skills/` folder)  
**Rate-limiting:** Per-principal quota (humans: 100 req/min; agents: 1000 req/min; SPARQL: separate 50 req/min)

**MCP Tools (10 core):**
1. `utl_list_available_tasks` — discover holon-level tasks ready for agent assignment
2. `utl_claim_task` — agent marks task as In Progress, gets scoped skill packages
3. `utl_get_holon_subgraph` — agent fetches holon + descendants (respects authority filter)
4. `utl_resolve_skills_for_task` — route skill packages based on holon level + agent role
5. `utl_fetch_skill_package` — download skill manifest + embedded rules/models
6. `utl_deploy_skill` — deploy skill to ephemeral execution context (sandboxed)
7. `utl_publish_skill` — commit skill version to registry (for distribution to other agents)
8. `utl_report_decision` — publish Decision holon (blocks/unblocks linked tasks)
9. `utl_request_decision_input` — escalate to HITL; awaits human or AI-app choice
10. `utl_report_progress` — update holon status + append event log (Agent → board)

**Holon-aware skill routing:** Agents + domains boosted by relevance (e.g., `compliance-auditor` + `CMMI` domain → high score for Feature CMMI assessment tasks)

### UI: React + D3/Cytoscape (Holon Graph Renderer)

**Layout algorithm:** HGA four-layer metaphor (SceneGraph = current state, DomainGraph = constraints, ContextGraph = provenance, HolonicGraph = recursive composition)

**Interaction:**
- Click holon → expand children/parent/linked decisions/blockers
- Filter by: status, owner, team, cmmi_level, agent-accessibility
- Drag-and-drop reassign owner or change parent (mutation → event log → SPARQL view update)
- Timeline view: CMMI assessment history per Feature (via temporal CMMI_Assessment chain)

---

## Build Phase Specification

### Sprint 0: Foundation (Weeks 1–2)

1. **ArcadeDB Setup**
   - Deploy ArcadeDB to `templates/local-stack/` Docker Compose
   - Seed with UFO base ontology (Turtle import)
   - Test SPARQL endpoint connectivity

2. **Ontology Authoring**
   - Finalize UFO model (Turtle) in `/planning/ontology/model.ttl`
   - Define SHACL shapes for invariants in `/planning/ontology/shapes.ttl`
   - Generate JSON-LD context for REST API serialization

3. **REST API Scaffold**
   - OpenAPI spec for 10 endpoints (CRUD + semantic)
   - Stub implementations (mock data from seed ontology)
   - JWT middleware + CF Access integration

### Sprint 1: Core Board (Weeks 3–4)

4. **Holon CRUD**
   - Implement Program/PI/Feature/Story POST (create holon, insert into graph)
   - Status mutations → event log append
   - Owner delegation (CapabilityGrant issuance)

5. **Decisions + Blockers**
   - Decision holon type + resolution workflow
   - Blocker (multi-holon dependency) creation and closure
   - Link holon ↔ decision (bidirectional references)

6. **CMMI Assessment**
   - CMMI_Assessment creation + chaining (predecessor links)
   - Materialize `cmmi_level_current` on Feature (via event reduction)
   - Board filter by CMMI level

### Sprint 2: Orchestration (Weeks 5–6)

7. **UNTOOL MCP Server**
   - Implement 10 core tools (JSON-RPC 2.0)
   - Holon-aware skill routing (domain/level boosters)
   - Rate-limiting per principal
   - Git-backed skill registry (fetch from GitHub releases)

8. **Holon-aware Agent Scoping**
   - Agent claims task → UNTOOL returns subgraph + skill packages
   - Authority filter (agent can only see holons they own or are assigned to)
   - CapabilityGrant scoping (agent scope narrows to assigned PI/Feature)

### Sprint 3: UI (Weeks 7–8)

9. **Holon Graph Renderer**
   - React + D3 holon visualization (four-layer HGA metaphor)
   - Click to expand/collapse, drag to reassign
   - Timeline view for CMMI assessment history

10. **Agent Integration**
    - UNTOOL MCP client library (JavaScript)
    - Agent claim → subgraph fetch → skill deploy (end-to-end flow test)
    - Board real-time sync (WebSocket or polling from REST API)

### Sprint 4: Integration (Weeks 9–10)

11. **Hub ↔ Spokes**
    - Cross-spoke dependencies visible (Blocker links between repos)
    - Spoke task board reads from unified ArcadeDB (not replicated)
    - Spoke agents can claim tasks from hub + spokes (single skill registry)

12. **PROV-O Audit Trail**
    - Event log → PROV-O triples (WasGeneratedBy, WasAssociatedWith)
    - SPARQL query for "who changed what, when, and why" (linked Decision)
    - Compliance-auditor agent can query audit chains

---

## Track A Research Findings — Integration

Track A identified **five RBAC authority inheritance patterns**. Recommended: **five-layer model combining holonic boundary scoping, OWL class hierarchy, SWRL behavioral rules, XACML 3.0 delegation, and PROV-O audit.**

**Layer 1 — Holonic Boundary Scoping:** Roles defined locally to holon level (Owner at Program; Assignee at Story; Decision authority at PI).  
**Layer 2 — OWL Class Hierarchy:** Role types as OWL classes with inheritance (Assignee rdfs:subClassOf TeamMember).  
**Layer 3 — SWRL Behavioral Rules:** Rules like "if holon.owner = Agent AND holon.level = Feature THEN agent.can_edit_children" (materialized as SHACL shapes).  
**Layer 4 — XACML 3.0 Delegation:** Bounded delegation (admin can delegate 1 level down; delegation expires at holon completion).  
**Layer 5 — PROV-O Audit:** Every authority grant/revoke linked to Decision + timestamp + revoker.

**Implementation path:** Encode Layers 1–2 in Turtle; generate Layer 3 (SWRL) from CMMI process models; Layer 4 embedded in CapabilityGrant.expires_at; Layer 5 via event log.

---

## Track B Ontology — Integration

Track B produced **formal UFO model** with:

- **Holon lattice:** Program (Kind) → PI (Subkind) → Feature (Subkind) → Story (Phase) + Epic (branching, as per Escalation 1)
- **Security model:** RBAC matrix by holon level; CapabilityGrant as first-class relator
- **Event schema:** 8 event types (Created, StatusChanged, OwnerChanged, ParentChanged, DecisionLinked, BlockerLinked, CapabilityGranted, BlockerResolved)
- **SPARQL patterns:** Current-state view, decision-authority chain, open blockers, multi-tenant filtering

All outputs migrate to:
- `/planning/ontology/model.yaml` — UFO model spec (source of truth for code generation)
- `/planning/ontology/model.ttl` — RDF serialization (import into ArcadeDB)
- `/planning/ontology/shapes.ttl` — SHACL invariants (validate mutations)
- `templates/ontology-project/` — generator templates (for spoke projects)

---

## Track C Architecture — Integration

Track C specified **UNTOOL as stateless MCP orchestrator** with:

- **Three planes:** Control (UNTOOL decomposer/router), Record (board REST API), Semantics (ArcadeDB holon graph)
- **Skill registry:** Versioned packages (semver) with holon.operates_at metadata
- **MCP tools:** 10 core tools covering task claiming, scoping, skill resolution, decision publishing
- **Deployment topology:** Application container (Azure Container Apps / GCP Cloud Run); Git-backed skill registry; 127.0.0.1 bound with CF Tunnel + CF Access

**Implementation path:**
- UNTOOL server scaffolding in `/tools/untool-orchestrator/` (Node.js + TypeScript)
- Skill manifest schema in `skills/manifest.json` (per-skill metadata)
- Holon-aware routing algorithm (domain/level boosters) in core router
- MCP tool specs in OpenAPI format (for agent SDK codegen)

---

## Unified Timeline & Success Criteria

**Timeline:** 10 sprints (5 weeks per sprint = ~50 days from code start)

**Sprint 0 (Foundation):** ArcadeDB + ontology + API scaffold ready  
**Sprint 1 (Core Board):** CRUD operations, decisions, CMMI assessment  
**Sprint 2 (Orchestration):** UNTOOL live, agents can claim tasks  
**Sprint 3 (UI):** Holon graph renderer + real-time sync  
**Sprint 4 (Integration):** Hub ↔ spokes working; audit trail live  

**Go/No-Go at Sprint 2:** If agents cannot claim tasks and receive scoped subgraphs, architecture is broken; halt and replan.

**Success criteria:**
1. ✅ Agents can list available tasks (utl_list_available_tasks)
2. ✅ Agent claims task → receives subgraph + skill packages (utl_claim_task + utl_get_holon_subgraph)
3. ✅ Agent publishes Decision → board updates in real-time (utl_report_decision)
4. ✅ CMMI assessment chains queryable (SPARQL temporal query)
5. ✅ Cross-spoke blockers visible + resolvable (Blocker link across repos)
6. ✅ Audit trail complete (PROV-O + SPARQL "who changed what when")
7. ✅ 3+ agents (Claude, Copilot, custom domain expert) coordinate on single holon graph
8. ✅ Human and agent UIs show same data (single source of truth)

---

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| **Graph query performance at scale (1000+ holons)** | ArcadeDB sharding by team/org; SPARQL query indexes on Event.holon_id; materialize current_level to avoid expensive event log scans |
| **CMMI assessment evidence linking breaks compliance audit** | PROV-O layer non-negotiable; every CMMI_Assessment must link to ≥1 Evidence (Decision or Document); CI validates shape |
| **Agent CapabilityGrant scope creep (agent edits outside assigned holon)** | JWT claims include holon.id filter; API enforces filter before update; SHACL shape validates parent constraint |
| **Event log unbounded growth** | Partition by holon (each holon has own event stream); archive older than 1 year; snapshot current state quarterly |
| **Skill routing sends agent wrong packages** | Unit test every domain/level booster combo; manual approval gate for new skill registrations; agents report mismatches to HITL |

---

## Decision Record

**Resolved escalations:**
- ✅ **Escalation 1:** Epic placement → branching lattice (Program-level + Feature-level Epics)
- ✅ **Escalation 2:** CMMI level → hybrid (scalar property + reified Assessment for provenance)

**Technology stack decided:**
- ✅ **Data:** ArcadeDB (multi-model graph, SPARQL, time-series)
- ✅ **Ontology:** UFO + SAFE + CMMI (Turtle/OWL, SHACL shapes)
- ✅ **Board API:** REST (OpenAPI 3.1) + SPARQL endpoint
- ✅ **Orchestration:** UNTOOL (MCP server, Git-backed skills, holon-aware routing)
- ✅ **UI:** React + D3/Cytoscape (HGA four-layer metaphor)
- ✅ **Auth:** JWT + CF Access (edge validation)
- ✅ **RBAC:** Five-layer model (holonic boundary + OWL + SWRL + XACML + PROV-O audit)

**Ready for Sprint 0:** Yes. Track B ontology output migrates directly to `/planning/ontology/`. Track C UNTOOL spec becomes `/tools/untool-orchestrator/` skeleton. Track A RBAC research informs SHACL shape authoring.

---

## Downstream Artifacts

This ADR authors two new GitHub Projects board items:

1. **Enabler: Holonic Unified Board — Build (Sprint 0–4)**
   - Parent: Epic "Platform Next-Gen Work Management"
   - Status: Ready
   - Type: Enabler
   - Size: XL (10 sprints)
   - Estimate: 40 story points
   - Assignment: Platform team (devops-engineer + backend-developer + frontend-developer + untool-orchestrator specialist)

2. **Decision Artifact: Tech Stack Approved**
   - Status: Completed
   - Type: Decision
   - Assignees: Track A, Track B, Track C leads
   - Linked issues: Escalation 1 (Epic placement), Escalation 2 (CMMI modeling)

Both items added to GitHub Projects board v2 with this ADR as the source document.

---

## Next Steps

1. **Review & Approval** (24–48 hrs): Nick Clarke + domain leads (compliance-auditor, ontologist-ufo, architect-reviewer) sign off
2. **Sprint 0 Kickoff:** Platform team begins ArcadeDB setup + ontology authoring
3. **Daily standups:** Design → Ops sync (ontology changes feed to API design; API feedback refines ontology)
4. **Go/No-Go Gate at Sprint 2:** If agents cannot claim tasks, escalate to HITL for replan

---

**Document compiled by:** Synthesis of Track A (ae10214515a6a2c36), Track B (a45c0959060ff1ac1), Track C (a32fc6794ad698c7e)  
**Approval chain:** Nick Clarke (user) → Platform team leads → GitHub Projects board
