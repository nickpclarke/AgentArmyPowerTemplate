# Agent Tracks — Design vs Ops (the run-vs-design segregation)

Formal classification of the AgentArmy roster (178 agents across 12 categories) into the two tracks defined in [ARC-ADR-024](decisions/ARC-ADR-024-platform-maturity-audit.md):

- **Design / Architecture** — produces *target state*: ADRs, strategies, golden paths, threat models, capability maps. Doesn't touch running infra.
- **Platform Ops** — assesses + acts on *current state*: gap reports, IaC fixes, runbooks, telemetry pipelines, dispatched issues against the live fleet.
- **Both** — agents that legitimately operate in either mode depending on the brief. *Always brief explicitly: "Track: Design"* or *"Track: Ops"*.
- **Neither** — the agent isn't infrastructure-focused; it's a builder, reviewer, or domain expert that consumes design + ops but produces neither.

When commissioning an agent for a maturity audit or infrastructure work, **state the track in the prompt**. Design agents that try to read live infra waste cycles; ops agents that propose new ADRs duplicate work the architects already did. Briefing the track keeps each agent in its lane and the synthesis tractable.

## Roster (by category)

### 03 — Infrastructure (22 agents)

| Agent | Track | Notes |
|---|---|---|
| `cloud-architect` | Design | Multi-cloud strategy, landing zones; never deploys |
| `azure-infra-engineer` | Ops | Bicep, ACA, KV, OIDC — touches running infra |
| `gcp-infra-engineer` | Ops | Cloud Run, GKE, Vertex; touches running GCP |
| `aws-infra-engineer` | Ops | Fargate, RDS, CDK; touches running AWS |
| `vercel-engineer` | Ops | Vercel platform deploys/config |
| `kubernetes-specialist` | Ops | Cluster operation |
| `terraform-engineer` | Both | IaC strategy (Design) + actual `terraform apply` runs (Ops) |
| `terragrunt-expert` | Both | Module architecture + execution |
| `devops-engineer` | Ops | CI/CD pipelines (builds & operates) |
| `deployment-engineer` | Ops | Canary/blue-green for single service |
| `release-manager` | Design | Cross-spoke train coordination, semver strategy |
| `sre-engineer` | Ops | SLOs, error budgets, on-call |
| `observability-engineer` | Ops | OTel, metrics/logs/traces pipelines, dashboards |
| `finops-engineer` | Ops | Cost mapping + budgets + rightsizing |
| `api-gateway-engineer` | Ops | Gateway runtime config (rate limit, edge policy) |
| `network-engineer` | Ops | VNet, peering, ingress |
| `database-administrator` | Ops | DB HA, DR, replication |
| `incident-responder` | Ops | Active incident handling |
| `chaos-engineer` | Ops | Game days, fault injection |
| `platform-engineer` | Both | IDP design (Design) + golden paths (Ops) |
| `dx-optimizer` | Both | Workflow + build optimization |
| `build-engineer` | Ops | Build system performance |

### 11 — Enterprise Architecture (11 agents)

All **Design**: `enterprise-architect`, `togaf-adm-advisor`, `wardley-strategist`, `business-architect`, `capability-planner`, `solution-architect`, `information-architect`, `integration-architect`, `security-architect`, `platform-architect`, `us-regulatory-architect`.

These produce architecture documents + ADRs + capability maps. They never deploy.

### 04 — Quality & Security (17 agents)

| Agent | Track | Notes |
|---|---|---|
| `security-architect` | Design | (also in 11) — Zero Trust, FedRAMP, ZTA design |
| `security-engineer` | Ops | Implements security controls in CI + infra |
| `security-auditor` | Ops | Audits live systems |
| `compliance-auditor` | Ops | Reads live state vs frameworks |
| `penetration-tester` | Ops | Active testing against running systems |
| `incident-responder` | Ops | (also in 03) |
| `ad-security-reviewer` | Ops | AD security state |
| `code-reviewer` + `coderabbit:code-reviewer` | Neither | Code review on PRs |
| `feature-dev:code-reviewer`, `pr-review-toolkit:code-reviewer` | Neither | PR review |
| `pr-review-toolkit:silent-failure-hunter`, `comment-analyzer`, `type-design-analyzer`, `pr-test-analyzer`, `code-simplifier`, `code-simplifier:code-simplifier` | Neither | Code-quality review |
| `accessibility-tester` | Ops | A11y testing |
| `qa-expert`, `test-automator` | Neither | Test strategy + automation |

### 01 — Core Development, 02 — Languages, 05 — Data/AI, 06 — Dev Experience, 07 — Specialized Domains, 08 — Business/Product

These are predominantly **Neither** (code builders, domain experts, product/market roles). Notable exceptions:

| Agent | Track | Notes |
|---|---|---|
| `ai-engineer`, `llm-architect`, `mlops-engineer`, `machine-learning-engineer` | Both | Design for architecture, Ops for serving infra |
| `dlt-engineer` | Ops | Pipeline operation |
| `data-engineer` | Ops | Data infrastructure |
| `schema-migration-engineer` | Ops | Live migrations |
| `feature-flag-engineer` | Ops | Flag lifecycle |
| `async-messaging-engineer` | Ops | Broker operation |
| `contract-test-engineer` | Ops | Pact provider verification at runtime |
| `api-designer` | Design | Contract authoring |
| `git-workflow-manager` | Ops | Branch strategy + execution |
| `dependency-manager` | Ops | Live dependency audit + bumps |
| `docker-expert` | Ops | Image build + runtime |
| `legacy-modernizer`, `refactoring-specialist` | Neither | Code transformation |

### 09 — Meta-Orchestration (14 agents)

Coordination layer — track depends on what they orchestrate.

| Agent | Track | Notes |
|---|---|---|
| `agent-organizer`, `multi-agent-coordinator`, `task-distributor`, `workflow-orchestrator` | Both | Track inherits from the work being orchestrated |
| `context-manager`, `performance-monitor`, `error-coordinator` | Ops | Operate the meta-layer |
| `knowledge-synthesizer` | Neither | Cross-session learning extraction |
| `hitl-coordinator` | Both | Surfaces design decisions OR ops alarms to humans |
| `agent-distinctiveness-advocate`, `agent-installer`, `agent-organizer` | Neither | Roster management |
| `codebase-orchestrator` | Neither | Local refactor governance |

### 10 — Research/Analysis (9 agents)

All **Design** or **Neither** — they produce reports, never touch infra:
`research-analyst`, `market-researcher`, `competitive-analyst`, `trend-analyst`, `search-specialist`, `data-researcher`, `ux-researcher`, `scientific-literature-researcher`, `spike-researcher` (Design — produces runnable PoC + recommendation).

### 12 — Knowledge/Ontology (5 agents)

All **Design**: `ontologist-ufo`, `ontologist-bfo`, `ontologist-generalist`, `knowledge-engineer`, `taxonomist`. They author models; they don't operate a graph database. The `knowledge-engineer` overlaps Ops when it actually queries a running KG.

## Routing rules for the maturity audit pattern

When running a periodic Platform Maturity Audit (proposed cadence: quarterly), the agent slate is:

**Wave 1 — Design** (4-5 agents, parallel, target-state outputs):
- `cloud-architect`, `platform-architect`, `security-architect`, `release-manager`
- Optional: `enterprise-architect` (if the audit spans business/product), `togaf-adm-advisor` (if formal TOGAF artifacts are required)

**Wave 2 — Ops** (4-6 agents, parallel, gap-report outputs):
- `azure-infra-engineer` (or `gcp-`/`aws-` per cloud), `observability-engineer`, `sre-engineer`, `finops-engineer`
- Optional: `security-engineer` (for control gaps), `incident-responder` (for IR readiness), `deployment-engineer` (for rollout strategy)

The synthesis (an updated ADR-024 or a new sequenced ADR) merges the two waves into a fresh scorecard + dispatched backlog.

## Briefing template

When commissioning an agent for the maturity audit, copy this scaffold:

```
You are reviewing the AgentArmy fleet's <domain> as part of a Platform
Maturity Audit. **Track: <DESIGN | PLATFORM OPS> — <produce target state |
assess current state>. Do NOT <opposite-track work>.**

## Context
<env landscape paragraph + relevant ADRs>

## Your specific brief (<TRACK> only)
1. <numbered scope item>
2. ...

## Output shape
Markdown, under <N> words, structured as:
- ## Summary (3-5 lines)
- ## Findings (numbered items)
- ## Decision Points for Hub Owner (3-5 concrete items)
- ## Backlog (proposed)  (5-10 dispatched issues, each: title + repo + label)
```

Briefing the track up front is the single biggest lift in audit quality. Without it agents drift between strategy and tactics and the synthesis becomes noise.
