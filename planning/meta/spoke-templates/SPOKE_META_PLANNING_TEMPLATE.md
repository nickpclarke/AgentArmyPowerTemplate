# Spoke Meta-Planning Template

What to set up in `/planning/meta/` when you fork AgentArmy into a Spoke (e.g., AgentArmy-API-Layer, AgentArmy-UI-Layer).

**Use this checklist** when initializing a new Spoke repository.

---

## Quick Start (Copy from Hub)

After forking AgentArmy into your Spoke:

```bash
cd /path/to/your-spoke
mkdir -p planning/meta/{principles,ceremonies,decisions,learning}

# Copy Hub governance as baseline (adapt below)
cp /path/to/hub/AgentArmy/planning/meta/principles/ARMY_PRINCIPLES.md planning/meta/principles/
cp /path/to/hub/AgentArmy/planning/meta/decisions/AGENT_ONBOARDING_RUBRIC.md planning/meta/decisions/

# Create Spoke-specific documents (see sections below)
touch planning/meta/README.md  # Spoke version
touch planning/meta/principles/SPOKE_PRINCIPLES.md  # Spoke customizations
```

---

## What Stays the Same (Inherit from Hub)

These documents are **inherited from the Hub** without modification:

1. **`principles/ARMY_PRINCIPLES.md`** — The 7 foundational principles (Error Escalation, Knowledge Feedback, etc.) apply to Spokes
2. **`decisions/AGENT_ONBOARDING_RUBRIC.md`** — Validation rubric for new Spoke agents
3. **`.github/workflows/` automation** — Spoke inherits Hub workflows (auto-status, copilot-review, etc.)

**Spoke responsibility:** Keep these updated when Hub updates (periodic sync).

---

## What Changes (Spoke-Specific Customization)

### 1. Update `/planning/meta/README.md`

Copy from Hub version, then customize the introduction:

```markdown
# Meta-Planning: Governing the [LAYER] Spoke

Strategic governance for how the AgentArmy [LAYER] Layer implementation evolves.

This Spoke inherits core principles from the Hub template but applies them to [LAYER]-specific work.

**Hub principles inherited:** Error escalation, knowledge feedback, delegation direction, MECE
**Spoke customizations:** [LIST ANY LAYER-SPECIFIC GOVERNANCE BELOW]
```

**Layers (examples):**
- API Layer: REST API versioning, schema evolution, contract testing
- UI Layer: component library governance, accessibility standards, design system versioning
- Worker Layer: async job processing, retry policies, deadletter queue governance
- Mobile Layer: platform-specific guidelines (iOS/Android), app store submission process
- Infrastructure Layer: IaC governance, cloud resource tagging, disaster recovery testing

---

### 2. Create `principles/SPOKE_PRINCIPLES.md`

Spoke-specific principle customizations (beyond ARMY_PRINCIPLES). Template:

```markdown
# [LAYER] Spoke Principles

Customizations to ARMY_PRINCIPLES.md for the [LAYER] Layer.

## Core Principles (Inherited from Hub)

See `ARMY_PRINCIPLES.md` for: Error Escalation, Knowledge Feedback, Skill Scaffolding, Hook Integration, Delegation, MECE, Observable Decision-Making.

## Spoke-Specific Principles

### Principle A: [CONTRACT GOVERNANCE or LAYER-SPECIFIC CONCERN]

**Statement:** [Customize for your layer]

**Example for API Layer:**
> "Every API change is validated against Pact contracts before merge. Consumer-driven contract testing is non-negotiable."

**Example for UI Layer:**
> "Every component addition is validated for accessibility (WCAG 2.1 AA) before merge. Accessibility is a first-class citizen."

**Example for Worker Layer:**
> "Every job handler includes a retry policy and deadletter fallback. Unhandled failures are an operational incident, not a code issue."

### Principle B: [PERFORMANCE or QUALITY METRIC]

**Statement:** [Customize for your layer's critical path]

**Example for API Layer:**
> "API latency P99 < 200ms. Query optimization is a definition of done."

**Example for UI Layer:**
> "Lighthouse score >= 90. Performance is the user experience."

### Principle C: [DEPENDENCY GOVERNANCE or EXTERNAL INTEGRATION]

**Statement:** [Customize for your layer's coupling points]

**Example for API Layer:**
> "All downstream dependencies (databases, external APIs) have a circuit breaker and fallback. Cascade failures are prevented by design."

**Example for UI Layer:**
> "All external dependencies are lazy-loaded. Core UI renders in < 2 seconds without external CDNs."
```

---

### 3. Update `decisions/AGENT_ONBOARDING_RUBRIC.md`

The Hub rubric applies as-is to Spoke agents. But you MAY add Spoke-specific scoring rules:

```markdown
# [LAYER] Spoke Agent Onboarding Rubric

Inherits AGENT_ONBOARDING_RUBRIC.md from Hub.

## Additional Scoring Criteria (Spoke-Specific)

### Layer-Specific Scope Check

- [ ] Agent is scoped to [LAYER] concerns (not cross-layer)
- [ ] If agent touches multiple layers, document the contract it assumes
- [ ] Agent does not duplicate Hub agent (e.g., don't add `myapp-api-python-pro` — inherit Hub `python-pro`)

### Layer-Specific Tools Check (Optional)

- [ ] If layer has custom tooling (e.g., GraphQL-specific tools for API, Storybook for UI), agent knows about it
- [ ] Agent can invoke Hub agents for common work (AWS provisioning, database optimization, etc.)

## When to Reject a Spoke Agent

Reject if:
- ❌ Agent scope overlaps with Hub agent AND the Hub agent could do the work
- ❌ Agent is "generalist for this layer" (e.g., `myapp-full-stack-implementer`) — same MECE rules apply
- ❌ Agent cannot function due to missing Hub agent or cross-layer contract

Approve if:
- ✅ Agent is genuinely layer-specific (e.g., `ui-component-auditor` for UI layer)
- ✅ Agent enhances Hub agent (e.g., `api-performance-validator` that uses `performance-engineer` + layer-specific knowledge)
```

---

### 4. Create `ceremonies/SPOKE_PLANNING_CEREMONIES.md`

Define sprint planning, principle review, and feedback cadence for this Spoke:

```markdown
# [LAYER] Spoke Planning Ceremonies

## Sprint Planning (Every 2 weeks)

**Attendees:** Team leads, [layer] engineers, product owner  
**Duration:** 1.5 hours  
**Outputs:**
- Sprint goals aligned to Hub RT (if applicable)
- Spoke-specific features committed
- Contract assumptions confirmed (what does this layer assume about OTHER layers?)

**Cadence:** Every other Monday 10 AM

## Daily Standup (Every weekday)

**Attendees:** All [layer] engineers  
**Duration:** 15 min  
**Format:** What I did, what I'm doing, blockers (especially cross-layer dependencies)

**Cadence:** 9:30 AM daily

## Principle Review (Every quarter)

**Attendees:** Architecture lead, one engineer per contract boundary  
**Duration:** 1 hour  
**Agenda:**
1. Review incidents from knowledge-synthesizer: any new anti-patterns?
2. Review [LAYER]-specific principles: still valid? Any additions needed?
3. Review SPOKE_PRINCIPLES.md: any principle drift?
4. Update principles if needed

**Cadence:** End of Q2, Q3, Q4, Q1

## Contract Review (When cross-layer contract changes)

**Attendees:** This layer's team + impacted layer teams (if cross-spoke)  
**Duration:** 30 min  
**Agenda:**
1. Propose contract change (OpenAPI, GraphQL schema, async message schema, etc.)
2. Validate existing consumers
3. Plan contract evolution (versioning, deprecation, migration)

**Trigger:** Before any breaking API change, event schema change, or data format change

## Learning Retrospective (End of each RT)

**Attendees:** Entire [layer] team  
**Duration:** 1 hour  
**Agenda:**
1. Review incidents & KB entries from this RT
2. Identify anti-patterns: Did we see the same problem 3+ times?
3. Propose principle updates for next RT
4. Celebrate learning

**Cadence:** End of RT1, RT2, RT3, RT4 (if Spoke was active during those RTs)
```

---

### 5. Create `learning/SPOKE_INCIDENT_WORKFLOW.md`

Document how incidents flow from production → KB → principle updates in this Spoke:

```markdown
# [LAYER] Spoke Incident-to-Principle Workflow

How we capture, learn from, and prevent incidents in the [LAYER] layer.

## Incident Capture (Stop Hook)

When a task fails:
1. Agent's Stop hook captures: what failed, why, context
2. Incident logged to `[LAYER]-incidents` in knowledge base
3. `error-coordinator` tags incident with severity (low/medium/high)

## Analysis & Pattern Detection (Weekly)

Once per week:
1. `knowledge-synthesizer` aggregates incidents from past week
2. Identify patterns: "transaction timeout happened 3x in payment processing"
3. Categorize by layer (API, UI, worker, infra)
4. Flag HIGH-severity patterns (block deployment until mitigated)

## Principle Update (Quarterly)

At quarterly principle review:
1. Review all incidents from past quarter
2. Find root causes: "transactions failed because timeout is 5s, but payment API is slow"
3. Update SPOKE_PRINCIPLES.md: "add principle: Payment API calls have 15s timeout + fallback"
4. Update AGENT_ONBOARDING_RUBRIC.md if principle changes onboarding validation
5. Training: Update runbooks and documentation for next team

## Knowledge Base Topics (Layer-Specific)

Spokes SHOULD track incidents by topic:

**Example for API Layer:**
- `api-database-timeout` — DB query exceeded time limit
- `api-schema-mismatch` — Request didn't match OpenAPI spec
- `api-missing-pact` — Response violated consumer contract
- `api-cascading-failure` — Downstream service was down

**Example for UI Layer:**
- `ui-component-error` — Component threw exception
- `ui-performance-regression` — Lighthouse score dropped
- `ui-accessibility-violation` — Feature failed WCAG audit
- `ui-network-error` — External API call failed

## Feedback Loop (Pull Request Routing)

When an incident suggests a code change:
1. Incident summary includes: "root cause was missing validation in X"
2. PR is routed to appropriate agent: backend-developer, frontend-developer, etc.
3. PR includes: "Fixes incident [incident-id]"
4. After merge, incident marked "resolved" with link to PR
5. Next similar incident will reference the previous fix

**Closure criteria:**
- Incident captured in KB
- Root cause identified (not just symptom treated)
- Permanent fix merged (or conscious decision to accept risk)
- Principle updated if systemic
```

---

### 6. Create `decisions/SPOKE_LAYER_ROADMAP.md`

Layer-specific milestones & strategy (complements Hub release trains):

```markdown
# [LAYER] Spoke Implementation Roadmap

How this layer aligns to Hub release trains (RT1–RT4) and layer-specific goals.

## Spoke-to-Hub Dependency Mapping

| Hub RT | Hub Deliverable | [LAYER] Dependency | Spoke Start | Spoke Complete |
|---|---|---|---|---|
| RT1 | Routing decision tree | Need routing rules | Jun 1 | Jun 15 |
| RT1 | Context graph injection | Can use graph for layer context | Jun 1 | Jun 28 |
| RT2 | Skill scaffolding | Can expose layer-specific skills | Jul 12 | Jul 26 |
| RT2 | Learning loop | Can feed incidents to KB | Jul 12 | Aug 9 |
| RT3 | Spoke onboarding playbook | **Blocks Spoke readiness** | Aug 23 | Sep 15 |

## Layer-Specific Milestones

| Milestone | Target | Owner |
|---|---|---|
| **Milestone 1: Foundation** | [DATE] | [Owner] |
| **Milestone 2: Contract Stability** | [DATE] | [Owner] |
| **Milestone 3: Performance Baseline** | [DATE] | [Owner] |
| **Milestone 4: Production Ready** | [DATE] | [Owner] |

## Success Criteria (Layer-Specific)

- [ ] [METRIC 1]: [Definition]
- [ ] [METRIC 2]: [Definition]
- [ ] [METRIC 3]: [Definition]

**Example for API Layer:**
- [ ] 95th percentile latency < 200ms under nominal load
- [ ] Zero unhandled exceptions in error logs
- [ ] Pact contracts with all consumers verified pre-deployment
```

---

## Checklist for New Spoke

When initializing a new Spoke, run this checklist:

```markdown
# Spoke Meta-Planning Checklist

- [ ] Fork Hub AgentArmy template
- [ ] Create `/planning/meta/` directory structure
- [ ] Copy and adapt `/planning/meta/README.md` (update layer name)
- [ ] Copy `principles/ARMY_PRINCIPLES.md` from Hub
- [ ] Create `principles/SPOKE_PRINCIPLES.md` (layer-specific customizations)
- [ ] Copy `decisions/AGENT_ONBOARDING_RUBRIC.md` from Hub
- [ ] Create `decisions/SPOKE_LAYER_ROADMAP.md` (align to Hub RTs)
- [ ] Create `ceremonies/SPOKE_PLANNING_CEREMONIES.md` (team cadence)
- [ ] Create `learning/SPOKE_INCIDENT_WORKFLOW.md` (KB topic mapping)
- [ ] Link from `/planning/README.md` to `/planning/meta/README.md`
- [ ] Update `/docs/n-layer-architecture.md` to reference this Spoke
- [ ] Schedule kickoff meeting with team
- [ ] Sync with Hub on RT timeline (when does this Spoke start work?)

**Status:** [ ] Ready to work
```

---

## Example: API Layer Spoke

Here's a concrete example for an API Layer Spoke:

```markdown
# API Layer Spoke Meta-Planning

## Spoke-Specific Principle 1: Contract-First Design

All API changes go through Pact consumer-driven contract testing before implementation.

## Spoke-Specific Principle 2: Cascade Prevention

Every external dependency (DB, downstream API, message broker) has a circuit breaker and fallback.

## Spoke Planning Ceremonies

- **Daily standup:** 9:30 AM (includes dependency status check)
- **Sprint planning:** Every 2 weeks, aligned to Hub RTs
- **Contract review:** When OpenAPI or async schema changes (before implementation)
- **Principle review:** End of each Hub RT
- **Learning retro:** End of quarter

## Roadmap Alignment to Hub RTs

| Hub Deliverable | API Impact | Timeline |
| Routing Policy (RT1) | API must expose routing decision via `/health/routing` endpoint | Jun 1–12 |
| Hook System (RT1) | API integrates PostToolUse hook for query logging | Jun 15–28 |
| Telemetry (RT1) | API emits OTel spans for every request | Jun 29–Jul 12 |
| Choreography (RT2) | API implements saga pattern for distributed transactions | Jul 12–Aug 9 |
| Spoke Onboarding (RT3) | API exports manifest.json for Spoke init | Aug 23–Sep 15 |

## Success Criteria (API Layer)

- [ ] P99 latency < 200ms under load test
- [ ] Zero unhandled 5xx errors in logs
- [ ] 100% Pact consumer contracts passing pre-deployment
- [ ] All external calls have circuit breaker
```

---

## Relationship to Hub

**Hub is the source of truth for:** Core principles, general-purpose agents, governance automation, release train schedule.

**Spoke customizes:** Layer-specific principles, layer-specific agents, local planning ceremonies, layer-specific roadmap.

**Spoke syncs regularly:** Pull Hub updates to principles, MECE audit rubric, automation workflows.

---

**Last Updated:** 2026-05-23  
**This is a template.** Adapt all sections for your specific layer.

https://claude.ai/code/session_01FpTQSAUHfYEkRh9ziy5cDK
