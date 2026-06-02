# Agent Roster

AgentArmyPowerTemplate runs two agent armies. This document covers the **Claude Code army** — specialist sub-agents invoked from the local CLI. For the **GitHub Copilot army** (PR review, coding agent, `@board-manager` extension), see [copilot.md](copilot.md).

## When to use Claude Code vs Copilot

| Signal | Use |
|--------|-----|
| Issue Size XS/S + Type Bug/Story, clear acceptance criteria | Copilot coding agent (`copilot-task` label) |
| Issue Size M+ or Type Feature/Enabler/Epic | Claude Code |
| PR < 200 lines | Copilot auto-review is sufficient |
| PR > 200 lines (`needs-deep-review` label) | Run `/review-pr` in Claude Code |
| Architecture decision needed | Claude Code `enterprise-architect` |
| Security-sensitive change | Claude Code `/security-review` |

## How to Use Claude Code Agents

Claude Code automatically routes to the right agent based on task description. You can also invoke explicitly:

```
Use the enterprise-architect agent to evaluate this design.
```

Or for parallel work:

```
Run the code-reviewer and security-auditor agents in parallel on this PR.
```

---

## Design-Time Agents

Use these during PI planning, sprint planning, and feature refinement.

| Agent | When to use |
|---|---|
| `product-manager` | Feature prioritisation, roadmap decisions, OKR alignment |
| `business-analyst` | Writing user stories, acceptance criteria, process mapping |
| `scrum-master` | Sprint ceremonies, retrospectives, impediment removal, velocity |
| `ui-designer` | Component design, design systems, visual hierarchy, accessibility |
| `ux-researcher` | Usability analysis, persona development, user journey mapping |
| `api-designer` | REST/GraphQL API design, OpenAPI specs, versioning strategy |
| `spike-researcher` | Time-boxed technical spikes: library eval, runnable PoC code, build-vs-buy recommendation |

---

## Build-Time Agents

Use these during sprint execution.

### Software Engineering

| Agent | Speciality |
|---|---|
| `frontend-developer` | Multi-framework (React, Vue, Angular) full-stack integration |
| `backend-developer` | Server-side APIs, microservices, database interfaces |
| `fullstack-developer` | End-to-end features spanning database, API, and frontend layers |
| `javascript-pro` | Core JS idioms, ESM, async/await, browser APIs |
| `typescript-pro` | Strict typing, advanced generics, type-level programming |
| `python-pro` | Packaging, typing, async Python patterns |

---

## Quality Agents

Run these before merging or releasing.

| Agent | When to use |
|---|---|
| `code-reviewer` | Code quality, security vulnerabilities, best practices |
| `security-auditor` | Compliance assessments, systematic vulnerability analysis |
| `qa-expert` | Test strategy, quality metrics, test planning |
| `test-automator` | Automated test frameworks, CI/CD test integration |
| `accessibility-tester` | WCAG compliance, assistive technology support |

**Skill shortcuts** (run in current session without spawning an agent):
- `/review-pr` — runs `code-reviewer` on the current PR
- `/security-review` — security audit of current branch changes

---

## Operations & Infrastructure Agents

Use these for infrastructure, deployment, and reliability work.

| Agent | When to use |
|---|---|
| `devops-engineer` | CI/CD pipelines, containerisation, deployment workflows |
| `deployment-engineer` | Pipeline design, deployment automation strategies |
| `sre-engineer` | SLOs, error budgets, reliability, incident response |
| `cloud-architect` | Multi-cloud strategy, migration, cost optimisation |
| `docker-expert` | Container images, orchestration, security hardening |
| `security-engineer` | Threat modelling, zero-trust design, security automation |

---

## Developer Experience Agents

Use these to improve developer workflows, documentation, and dependencies.

| Agent | When to use |
|---|---|
| `dependency-manager` | Dependency audits, upgrades, vulnerability remediation |
| `documentation-engineer` | Documentation systems, architecture docs |
| `git-workflow-manager` | Git branching strategies, hooks, repository optimization |
| `readme-generator` | README generation, badge setup, project documentation |

---

## Enterprise Architecture Agents

TOGAF ADM-aligned EA specialists. All agents are designed around standard enterprise frameworks.

### EA Routing

| Engagement | Start with | Then involve |
|---|---|---|
| New technology investment | `enterprise-architect` | All EA specialists in ADM phase sequence |
| Strategic direction question | `wardley-strategist` | `capability-planner`, `enterprise-architect` |
| Capability model / investment | `business-architect` | `capability-planner` |

### EA Agents

| Agent | TOGAF Phase | Purpose |
|---|---|---|
| `enterprise-architect` | All phases | TOGAF ADM orchestrator, Architecture Vision, Repository governance |
| `wardley-strategist` | A, B, E | Wardley Maps: value chain, evolution, doctrine, climate, gameplay |
| `business-architect` | B | Business capabilities, value streams, operating models (BIZBOK) |
| `capability-planner` | B, E, F | WSJF prioritization, investment heat maps, portfolio backlog |

---

## Orchestration & Meta Agents

Use these to coordinate multiple agents and handle complex system workflows.

| Agent | Purpose |
|---|---|
| `agent-organizer` | Organize, categorize, and route tasks to the right agent |
| `hitl-coordinator` | Surfacing decision artifacts to GitHub Projects board, managing human-in-the-loop approvals |
| `multi-agent-coordinator` | Coordinate multiple concurrent agents in parallel or sequence |
| `workflow-orchestrator` | Model business process workflows and state machines |
| `research-analyst` | Primary/secondary research across multiple sources with synthesis |
| `github-projects-manager` | Managing and querying GitHub Projects v2 boards |

---

## Agent Chaining Patterns

### Feature implementation (SAFE Story)

```
1. business-analyst     → write user stories & acceptance criteria
2. fullstack-developer   → implement full-stack code (API + UI)
3. code-reviewer        → review PR for quality & correctness
4. qa-expert            → verify test coverage
```

### PI Planning support

```
1. product-manager      → prioritise Feature backlog
2. business-analyst     → decompose Features into Stories
3. scrum-master         → estimate capacity, assign to Iterations
```

### Production incident

```
1. sre-engineer         → triage, stabilize, and run root cause analysis
2. backend-developer    → implement immediate hotfix
3. code-reviewer        → fast-track review
4. deployment-engineer  → deploy hotfix to environment
```
