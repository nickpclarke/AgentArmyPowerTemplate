# Agent Roster

AgentArmy runs two agent armies. This document covers the **Claude Code army** — 100+ specialist sub-agents invoked from the local CLI. For the **GitHub Copilot army** (PR review, coding agent, `@board-manager` extension), see [copilot.md](copilot.md).

## When to use Claude Code vs Copilot

| Signal | Use |
|--------|-----|
| Issue Size XS/S + Type Bug/Story, clear acceptance criteria | Copilot coding agent (`copilot-task` label) |
| Issue Size M+ or Type Feature/Enabler/Epic | Claude Code |
| PR < 200 lines | Copilot auto-review is sufficient |
| PR > 200 lines (`needs-deep-review` label) | Run `/review-pr` in Claude Code |
| Architecture decision needed | Claude Code `architect-reviewer` |
| Security-sensitive change | Claude Code `/security-review` |

## How to Use Claude Code Agents

Claude Code automatically routes to the right agent based on task description. You can also invoke explicitly:

```
Use the architect-reviewer agent to evaluate this design.
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
| `architect-reviewer` | Architecture decisions, tech stack evaluation, ADRs |
| `agent-distinctiveness-advocate` | MECE audit governance: validate new agents for routing clarity, resolve overlap disputes, maintain roster distinctiveness |
| `scrum-master` | Sprint ceremonies, retrospectives, impediment removal, velocity |
| `ui-designer` | Component design, design systems, visual hierarchy, accessibility |
| `ux-researcher` | Usability analysis, persona development, user journey mapping |
| `api-designer` | REST/GraphQL API design, OpenAPI specs, versioning strategy |
| `data-scientist` | Analytics requirements, ML feasibility, data modelling |
| `market-researcher` | Competitive analysis, market sizing, customer discovery |

---

## Build-Time Agents

Use these during sprint execution.

### Frontend

| Agent | Speciality |
|---|---|
| `frontend-developer` | Multi-framework (React, Vue, Angular) full-stack integration |
| `react-specialist` | React 18+, hooks, state management, performance |
| `nextjs-developer` | Next.js 14+ App Router, server components, SEO |
| `typescript-pro` | Advanced type system, generics, type-level programming |
| `vue-expert` | Vue 3, Composition API, Nuxt 3 |
| `angular-architect` | Angular 15+, RxJS, micro-frontends |
| `ui-designer` | Visual polish, design system implementation |

### Backend

| Agent | Speciality |
|---|---|
| `backend-developer` | APIs, microservices, scalability, production architecture |
| `python-pro` | FastAPI, async Python, type-safe production code |
| `node-specialist` | Node.js APIs, CLIs, microservices |
| `golang-pro` | Concurrent Go systems, microservices, cloud-native |
| `java-architect` | Spring Boot, enterprise Java, microservices |
| `rust-engineer` | Systems programming, performance-critical code |
| `fastapi-developer` | Python async APIs, Pydantic v2 |
| `django-developer` | Django 4+, REST APIs, async views |

### Data & AI

| Agent | Speciality |
|---|---|
| `dlt-engineer` | dlt pipelines, source connectors, incremental loading, DuckDB/BigQuery/Snowflake |
| `data-engineer` | Pipelines, ETL/ELT, data platforms |
| `ml-engineer` | Model serving, training pipelines, MLOps |
| `ai-engineer` | End-to-end AI systems, RAG, fine-tuning |
| `llm-architect` | LLM system design, inference, multi-model deployments |
| `nlp-engineer` | NLP pipelines, text processing, domain-specific models |
| `database-administrator` | High-availability, backup, disaster recovery |
| `sql-pro` | Query optimisation, schema design, multi-database |

### Mobile & Desktop

| Agent | Speciality |
|---|---|
| `mobile-web-specialist` | Responsive web, touch UX, mobile media queries, canvas/WebGL sizing, iOS Safari quirks |
| `react-native` / `expo-react-native-expert` | Cross-platform mobile, native modules |
| `flutter-expert` | Flutter 3+, custom UI, iOS/Android/Web |
| `swift-expert` | Native iOS/macOS, SwiftUI, async/await |
| `electron-pro` | Desktop apps, native OS integration, distribution |

---

## Quality Agents

Run these before merging or releasing.

| Agent | When to use |
|---|---|
| `code-reviewer` | Code quality, security vulnerabilities, best practices |
| `security-auditor` | Compliance assessments, systematic vulnerability analysis |
| `security-engineer` | Threat modelling, zero-trust design, security automation |
| `penetration-tester` | Authorised offensive testing, vulnerability validation |
| `qa-expert` | Test strategy, quality metrics, test planning |
| `test-automator` | Automated test frameworks, CI/CD test integration |
| `performance-engineer` | Bottleneck identification, profiling, optimisation |
| `accessibility-tester` | WCAG compliance, assistive technology support |

**Skill shortcuts** (run in current session without spawning an agent):
- `/review-pr` — runs `code-reviewer` + `security-auditor` on the current PR
- `/security-review` — security audit of current branch changes

---

## Operations Agents

Use these for infrastructure, deployment, and reliability work.

| Agent | When to use |
|---|---|
| `devops-engineer` | CI/CD pipelines, containerisation, deployment workflows |
| `deployment-engineer` | Pipeline design, deployment automation strategies |
| `sre-engineer` | SLOs, error budgets, reliability, incident response |
| `cloud-architect` | Multi-cloud strategy, migration, cost optimisation |
| `kubernetes-specialist` | K8s cluster design, workload management |
| `terraform-engineer` | Infrastructure as code, multi-cloud IaC |
| `docker-expert` | Container images, orchestration, security hardening |
| `network-engineer` | Cloud network design, hybrid connectivity |
| `database-optimizer` | Query optimisation, indexing, execution plans |

---

## Management & Planning Agents

| Agent | When to use |
|---|---|
| `project-manager` | Project plans, risk management, stakeholder coordination |
| `scrum-master` | Agile ceremonies, velocity, impediment removal |
| `risk-manager` | Risk identification, quantification, control frameworks |
| `compliance-auditor` | GDPR, HIPAA, PCI DSS, SOC 2 compliance |
| `technical-writer` | API docs, user guides, SDK documentation |
| `documentation-engineer` | Documentation systems, architecture docs |

---

## Enterprise Architecture Agents

TOGAF ADM-aligned EA specialists for US commercial and federal contexts. All agents are designed around NIST frameworks, FedRAMP, FISMA, and US regulatory requirements — no UK-specific framework dependencies.

### EA Routing

| Engagement | Start with | Then involve |
|---|---|---|
| New technology investment | `enterprise-architect` | All EA specialists in ADM phase sequence |
| Strategic direction question | `wardley-strategist` (`/wardley`) | `capability-planner`, `enterprise-architect` |
| Capability model / investment | `business-architect` (`/capability-map`) | `capability-planner` |
| Platform / IDP architecture | `platform-architect` | `security-architect`, `integration-architect` |
| FedRAMP / FISMA / CMMC | `us-regulatory-architect` | `security-architect` |
| HIPAA data system | `us-regulatory-architect` | `information-architect`, `security-architect` |
| Architecture Decision | `/ea-adr` | (standalone skill) |

### EA Agents

| Agent | TOGAF Phase | Purpose |
|---|---|---|
| `enterprise-architect` | All phases | TOGAF ADM orchestrator, Architecture Vision, Repository governance |
| `togaf-adm-advisor` | All phases | Phase deliverable templates, ADM tailoring, artifact guidance |
| `wardley-strategist` | A, B, E | Wardley Maps: value chain, evolution, doctrine, climate, gameplay |
| `business-architect` | B | Business capabilities, value streams, operating models (BIZBOK) |
| `solution-architect` | E, F | ABB→SBB, solution docs, vendor evaluation, transition architecture |
| `information-architect` | C (Data) | Conceptual/logical data models, MDM, data governance (DAMA DMBOK) |
| `capability-planner` | B, E, F | WSJF prioritization, investment heat maps, portfolio backlog |
| `integration-architect` | C (App), D | API governance, EDA, canonical data model, ESB modernization |
| `security-architect` | Cross-cutting | Zero Trust (NIST SP 800-207), NIST CSF 2.0, FedRAMP, CMMC |
| `platform-architect` | D | IDP, Team Topologies, Backstage, golden paths, DORA metrics |
| `us-regulatory-architect` | Cross-cutting | FISMA/RMF, HIPAA, CMMC 2.0, PCI DSS v4, SOX ITGC, CCPA/CPRA |

### EA Skills

| Skill | What it does |
|---|---|
| `/wardley [domain]` | Full 5-stage Wardley pipeline → OWM syntax for create.wardleymaps.ai |
| `/ea-adr [decision]` | MADR v4.0 Architecture Decision Record |
| `/capability-map [domain]` | Business capability model + investment heat map |

### Full EA Program (TOGAF ADM)

```
1. enterprise-architect    → Architecture Vision (Phase A), Architecture Principles
2. wardley-strategist      → strategic landscape map (/wardley)
3. business-architect      → capabilities + value streams (Phase B)
4. capability-planner      → WSJF investment priorities
5. information-architect   → data architecture (Phase C)
6. integration-architect   → application integration (Phase C)
7. security-architect      → security by design (cross-cutting)
8. us-regulatory-architect → compliance constraints (cross-cutting)
9. platform-architect      → technology standards (Phase D)
10. solution-architect     → solution building blocks + transitions (Phase E/F)
11. enterprise-architect   → Architecture Contract (Phase G)
```

---

## Agent Chaining Patterns

### Feature implementation (SAFE Story)

```
1. business-analyst     → write acceptance criteria
2. architect-reviewer   → confirm technical approach
3. frontend-developer   → implement UI
4. backend-developer    → implement API
5. code-reviewer        → review PR
6. security-auditor     → security check
7. qa-expert            → test plan
```

### PI Planning support

```
1. product-manager      → prioritise Feature backlog
2. business-analyst     → decompose Features into Stories
3. scrum-master         → estimate capacity, assign to Iterations
4. architect-reviewer   → identify Enabler stories
5. risk-manager         → flag programme-level risks
```

### Production incident

```
1. devops-incident-responder  → triage and stabilise
2. sre-engineer               → root cause analysis
3. backend-developer          → implement fix
4. code-reviewer              → fast-track review
5. deployment-engineer        → deploy hotfix
```
