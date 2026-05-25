# AGENTS.md

Shared, fleet-wide guidance for AI agents — the AgentArmy specialist roster, routing,
skills, and chaining patterns. **This file is synced from the AgentArmy hub to every
spoke repo; do not edit it in a spoke — edit it in the hub.**

Repo-specific guidance (what *this* repository is, how to build/run/deploy it) lives in
this repo's `CLAUDE.md`, not here. The hub is a template (no app code); each spoke is a
real layer implementation with code to build and ship. Everything below applies to all
of them.

**Full documentation:** https://nickpclarke.github.io/AgentArmy/ — setup, agents,
GitHub Projects, HITL, deployment, and n-layer architecture are published there. Spoke
repos do not carry the hub's `docs/`, so use this link to read them.

## Task Backbone — depends on where you are

**In the hub:** all work items live on the attached GitHub Projects v2 board.
- Check the board: `gh project item-list PROJECT_NUM --owner OWNER`
- Create issues for non-trivial work: `gh issue create --title "..." --body "Closes #N"`

**In a spoke (microVM agent):** you cannot reach the hub board. Your task queue is **your
own repo's Issues + Milestones**. Epics are handed off to you as `[EPIC]` Issues opened in
this repo by the hub's PM/scrum-master; decompose them into Stories/PRs locally. There is
no GitHub Project for you. See [agent-onboarding](agent-onboarding.md) and
[spoke-work-intake](spoke-work-intake.md).

Either way: apply routing labels `copilot-task` (bounded) or `agent-army-task`
(complex/multi-file), and every PR body must include `Closes #ISSUE_NUMBER`.

## Agent Routing

| Task type | Route to |
|---|---|
| XS/S bugs, well-scoped stories | Copilot (`copilot-task` label) |
| M/L/XL stories, architecture, multi-file | Claude Code (`agent-army-task` label) |
| PRs ≤ 200 lines | Copilot first-pass review (automatic) |
| PRs > 200 lines | `/review-pr` in Claude Code |
| Security-sensitive PRs | `security-auditor` + `/security-review` |

## Issue Type Conventions

| Label | GitHub object | Fields to set |
|---|---|---|
| Epic | Issue + `epic` label | Type=Epic, PI, Priority |
| Feature | Issue + `feature` label | Type=Feature, Parent Epic |
| Story | Issue | Type=Story, Size, Estimate, Iteration |
| Bug | Issue + `bug` label | Type=Bug, Priority, Size |
| Spike | Issue + `spike` label | Type=Spike, PI |

## Available Skills

| Skill | Command | What it does |
|---|---|---|
| Commit | `/commit` | Stage, write message, commit |
| Commit + PR | `/commit-push-pr` | Commit, push, open PR |
| PR review | `/review-pr` | Multi-agent deep review |
| Security review | `/security-review` | Security-focused review |
| CLAUDE.md audit | `/revise-claude-md` | Improve AI guidance quality |
| Skill builder | `/skill-creator` | Build and benchmark new skills |

---

## Codex Usage

Codex should use this `AGENTS.md` file as its repository-specific source of truth. `CLAUDE.md`, `.claude/commands/`, and `.claude/agents/categories/` remain useful as shared AgentArmy operating context, but Claude Code slash commands are not Codex commands.

When adapting Claude Code helpers for Codex:

1. **Agent Synchronization**: The large library of specialist agents in `.claude/agents/categories/` is automatically synchronized into Codex-compatible TOML subagent definitions under `.codex/agents/` when a Codex session starts (via the `SessionStart` hook). You can also run this manually: `python scripts/sync_agents_to_codex.py`. For Antigravity CLI, you can sync these agents as native plugins by running `python scripts/sync_agents_to_antigravity.py`.
2. **Remote GCP MCP Servers**: Configure remote HTTP Google Cloud MCP servers (BigQuery, Storage, Observability, and Vertex AI Agent Registry) by defining the necessary environment variables (e.g., `GCP_BEARER_TOKEN`, `GCP_PROJECT_ID`, and the service URLs). Codex maps these automatically via `.codex/config.toml`, and Antigravity CLI maps them via `python scripts/sync_mcp_to_antigravity.py`.
3. Keep changes in template artifacts, not application code.
4. Treat `.claude/agents/categories/` as the specialist taxonomy for routing and review lenses.
5. Use `.codex/hooks.json` for Codex lifecycle hooks.
6. Keep personal provider keys out of committed `.codex/config.toml`; use local user config, environment variables, or untracked `.codex/config.local.toml`.

---

## Agent Library

Subagents live in `.claude/agents/categories/`. Each is a `.md` file with YAML frontmatter (`name`, `description`, `tools`, `model`). Invoke with `Agent(subagent_type: "<name>")`.

### Subagent Catalog Tool

`.claude/tools/subagent-catalog/` is a slash-command skill for discovering agents from the upstream VoltAgent catalog.

**Install** (run once):
```bash
cp -r .claude/tools/subagent-catalog ~/.claude/commands/
```

| Command | What it does |
|---|---|
| `/subagent-catalog:search <query>` | Find agents by name, description, or category |
| `/subagent-catalog:fetch <name>` | Get full agent definition |
| `/subagent-catalog:list` | Browse all categories |
| `/subagent-catalog:invalidate` | Clear 12-hour cache |

---

### 01 · Core Development

| Agent | Model | Purpose |
|---|---|---|
| `api-designer` | sonnet | REST/GraphQL endpoint design, OpenAPI specs, auth patterns |
| `async-messaging-engineer` | sonnet | Event-driven messaging: brokers (Kafka/RabbitMQ/SQS-SNS/NATS), AsyncAPI schemas, DLQ, consumer groups |
| `backend-developer` | sonnet | Server-side architecture, APIs, databases, performance |
| `design-bridge` | sonnet | Translates design specs into implementable technical requirements |
| `electron-pro` | sonnet | Cross-platform desktop apps with Electron |
| `frontend-developer` | sonnet | UI implementation, component architecture, state management |
| `fullstack-developer` | sonnet | End-to-end feature development across full stack |
| `graphql-architect` | sonnet | GraphQL schema design, resolvers, federation |
| `microservices-architect` | opus | Service decomposition, inter-service communication, resilience |
| `mobile-developer` | sonnet | Native and cross-platform mobile development |
| `mobile-web-specialist` | sonnet | Responsive web for phones/tablets, touch UX, mobile media queries, canvas sizing |
| `ui-designer` | sonnet | Visual design systems, component libraries, accessibility |
| `websocket-engineer` | sonnet | Real-time communication, WebSocket servers and clients |

### 02 · Language Specialists

| Agent | Model | Purpose |
|---|---|---|
| `angular-architect` | sonnet | Angular apps, NgModules, RxJS, state management |
| `cpp-pro` | sonnet | C++ systems, performance optimization, memory management |
| `csharp-developer` | sonnet | C# applications, LINQ, async patterns |
| `django-developer` | sonnet | Django web apps, ORM, middleware, REST APIs |
| `dotnet-core-expert` | sonnet | .NET Core / .NET 5–8 services and APIs |
| `dotnet-framework-4.8-expert` | sonnet | Legacy .NET Framework 4.8 applications |
| `elixir-expert` | sonnet | Elixir, Phoenix, OTP concurrency patterns |
| `expo-react-native-expert` | sonnet | Expo + React Native cross-platform apps |
| `fastapi-developer` | sonnet | FastAPI services, Pydantic models, async Python |
| `flutter-expert` | sonnet | Flutter apps for iOS, Android, web |
| `golang-pro` | sonnet | Go services, goroutines, interfaces, performance |
| `java-architect` | opus | Java enterprise architecture, JVM tuning |
| `javascript-pro` | sonnet | Modern JS, ESM, async/await, browser APIs |
| `kotlin-specialist` | sonnet | Kotlin Android, coroutines, multiplatform |
| `laravel-specialist` | sonnet | Laravel apps, Eloquent, queues, Blade |
| `nextjs-developer` | sonnet | Next.js SSR/SSG, App Router, Edge, API routes |
| `node-specialist` | sonnet | Node.js services, streams, event loop, npm |
| `php-pro` | sonnet | PHP applications, Composer, modern PHP patterns |
| `powershell-5.1-expert` | sonnet | Windows PowerShell 5.1 scripting and modules |
| `powershell-7-expert` | sonnet | PowerShell 7 cross-platform scripting |
| `python-pro` | sonnet | Python applications, packaging, typing, async |
| `rails-expert` | sonnet | Ruby on Rails, ActiveRecord, Hotwire |
| `react-specialist` | sonnet | React components, hooks, context, performance |
| `rust-engineer` | sonnet | Rust systems, ownership, lifetimes, async |
| `spring-boot-engineer` | sonnet | Spring Boot services, DI, JPA, security |
| `sql-pro` | sonnet | SQL query optimization, schema design, migrations |
| `swift-expert` | sonnet | Swift iOS/macOS apps, SwiftUI, Combine |
| `symfony-specialist` | sonnet | Symfony framework, DI container, Doctrine |
| `typescript-pro` | sonnet | TypeScript, strict typing, generics, decorators |
| `vue-expert` | sonnet | Vue 3, Composition API, Pinia, Nuxt |

### 03 · Infrastructure

| Agent | Model | Purpose |
|---|---|---|
| `api-gateway-engineer` | sonnet | API gateway config & policy: rate limiting, edge authN/Z, routing across spokes, developer portal |
| `azure-infra-engineer` | sonnet | Azure resources, ARM/Bicep, AKS, Azure networking |
| `cloud-architect` | opus | Multi-cloud design, cost optimization, HA patterns |
| `database-administrator` | sonnet | DB admin, backup/recovery, replication, tuning |
| `deployment-engineer` | sonnet | CI/CD pipelines, release automation, rollback |
| `devops-engineer` | sonnet | DevOps practices, automation, toolchain integration |
| `devops-incident-responder` | sonnet | Production incidents, runbooks, RCA for DevOps |
| `docker-expert` | sonnet | Dockerfiles, Compose, multi-stage builds, registries |
| `finops-engineer` | sonnet | Cloud cost engineering: cost visibility, unit economics, rightsizing, commitments, showback/chargeback |
| `incident-responder` | sonnet | On-call response, triage, escalation, postmortems |
| `kubernetes-specialist` | sonnet | K8s deployments, Helm, operators, networking |
| `network-engineer` | sonnet | Networking, DNS, load balancing, VPN, firewalls |
| `observability-engineer` | sonnet | Telemetry production: OpenTelemetry instrumentation, metrics/logs/traces pipelines, Grafana/Prometheus dashboards |
| `platform-engineer` | sonnet | Internal developer platforms, golden paths, IDP |
| `security-engineer` | sonnet | Security controls, IAM, secrets management, hardening |
| `sre-engineer` | opus | SLIs/SLOs, error budgets, toil reduction, reliability |
| `terraform-engineer` | sonnet | Terraform modules, state, providers, drift detection |
| `terragrunt-expert` | sonnet | Terragrunt DRY configs, multi-account patterns |
| `windows-infra-admin` | sonnet | Windows Server, AD, GPO, PowerShell DSC |

### 04 · Quality & Security

| Agent | Model | Purpose |
|---|---|---|
| `accessibility-tester` | sonnet | WCAG compliance, screen reader testing, a11y audits |
| `ad-security-reviewer` | sonnet | Active Directory security posture reviews |
| `ai-writing-auditor` | sonnet | Detect AI-generated content, writing quality audits |
| `architect-reviewer` | opus | Architecture review, trade-off analysis, ADRs |
| `chaos-engineer` | sonnet | Failure injection, resilience testing, GameDays |
| `code-reviewer` | sonnet | Code review, style, correctness, security, maintainability |
| `compliance-auditor` | sonnet | Regulatory compliance, SOC2, ISO 27001, GDPR |
| `contract-test-engineer` | sonnet | Consumer-driven contract testing (Pact), provider verification, cross-spoke schema-drift detection |
| `debugger` | sonnet | Root cause analysis, debugging strategies, fix validation |
| `error-detective` | sonnet | Error pattern analysis, log triage, exception investigation |
| `penetration-tester` | opus | Authorized pen testing, vulnerability assessment |
| `performance-engineer` | sonnet | Profiling, benchmarking, bottleneck elimination |
| `powershell-security-hardening` | sonnet | PowerShell security, constrained language mode, AMSI |
| `qa-expert` | sonnet | Test strategy, test plans, defect management |
| `security-auditor` | opus | Security audits, threat modeling, risk assessment |
| `test-automator` | sonnet | Test automation frameworks, CI integration, coverage |
| `ui-ux-tester` | sonnet | UX testing, usability heuristics, user flow validation |

### 05 · Data & AI

| Agent | Model | Purpose |
|---|---|---|
| `ai-engineer` | sonnet | AI system integration, LLM APIs, prompt pipelines |
| `data-analyst` | sonnet | Data analysis, visualization, statistical insights |
| `data-engineer` | sonnet | ETL/ELT pipelines, data lakes, orchestration |
| `dlt-engineer` | sonnet | dlt pipelines, source connectors, incremental loading, DuckDB/BigQuery/Snowflake |
| `data-scientist` | sonnet | ML experiments, feature engineering, model evaluation |
| `database-optimizer` | sonnet | Query tuning, index strategy, execution plan analysis |
| `llm-architect` | opus | LLM system design, RAG, fine-tuning, evaluation |
| `machine-learning-engineer` | sonnet | Production ML lifecycle: training pipelines, serving, automated retraining, feature stores, monitoring |
| `mlops-engineer` | sonnet | ML pipelines, model registry, drift detection, CD4ML |
| `nlp-engineer` | sonnet | NLP models, text classification, NER, embeddings |
| `postgres-pro` | sonnet | PostgreSQL internals, extensions, JSONB, partitioning |
| `prompt-engineer` | sonnet | Prompt design, chain-of-thought, few-shot, evaluation |
| `reinforcement-learning-engineer` | sonnet | RL algorithms, reward shaping, policy optimization |
| `schema-migration-engineer` | sonnet | DB schema versioning & migration orchestration (Flyway/Liquibase/Alembic), zero-downtime evolution |

### 06 · Developer Experience

| Agent | Model | Purpose |
|---|---|---|
| `build-engineer` | sonnet | Build systems, Webpack/Vite/Turbo, monorepos |
| `cli-developer` | sonnet | CLI tool design, argument parsing, interactive prompts |
| `dependency-manager` | sonnet | Dependency audits, upgrades, vulnerability remediation |
| `documentation-engineer` | sonnet | Docs sites, API docs, architecture documentation |
| `dx-optimizer` | sonnet | Developer experience improvements, tooling, onboarding |
| `feature-flag-engineer` | sonnet | Feature flags & progressive delivery: targeting, lifecycle, kill switches, flag-debt cleanup |
| `git-workflow-manager` | sonnet | Git branching strategies, hooks, large repo optimization |
| `legacy-modernizer` | opus | Incremental modernization of legacy codebases |
| `mcp-developer` | sonnet | MCP server/client implementation, JSON-RPC, SDK usage |
| `powershell-module-architect` | sonnet | PowerShell module design, manifest, publishing |
| `powershell-ui-architect` | sonnet | PowerShell GUI with WPF/WinForms/XAML |
| `readme-generator` | haiku | README generation, badge setup, project documentation |
| `refactoring-specialist` | sonnet | Safe refactoring, code smell removal, design patterns |
| `slack-expert` | sonnet | Slack bot development, Bolt framework, block kit |
| `tooling-engineer` | sonnet | Developer tooling, scripts, automation, linters |

### 07 · Specialized Domains

| Agent | Model | Purpose |
|---|---|---|
| `api-documenter` | sonnet | API reference docs, OpenAPI rendering, developer portals |
| `blockchain-developer` | sonnet | Smart contracts, DeFi protocols, Web3 integration |
| `embedded-systems` | sonnet | Embedded C/C++, RTOS, hardware interfaces |
| `fintech-engineer` | opus | Financial systems, payments, regulatory compliance |
| `game-developer` | sonnet | Game mechanics, Unity/Unreal, physics, networking |
| `github-projects-manager` | sonnet | GitHub Projects v2 boards, issues, milestones, sprints |
| `healthcare-admin` | sonnet | Healthcare IT, HL7/FHIR, EHR integrations |
| `iot-engineer` | sonnet | IoT protocols (MQTT, CoAP), edge computing, firmware |
| `m365-admin` | sonnet | Microsoft 365 admin, Exchange, SharePoint, Teams |
| `mobile-app-developer` | sonnet | Mobile strategy, app store, push notifications |
| `payment-integration` | sonnet | Payment gateways, Stripe/Braintree, PCI compliance |
| `quant-analyst` | opus | Quantitative analysis, algorithmic trading, risk models |
| `risk-manager` | sonnet | Risk identification, impact assessment, mitigation plans |
| `seo-specialist` | sonnet | SEO audits, structured data, Core Web Vitals |

### 08 · Business & Product

| Agent | Model | Purpose |
|---|---|---|
| `business-analyst` | sonnet | Requirements elicitation, process mapping, gap analysis |
| `content-marketer` | haiku | Content strategy, copywriting, SEO content |
| `customer-success-manager` | haiku | Customer health, onboarding plans, churn prevention |
| `developer-advocate` | sonnet | DevRel: sample apps, external tutorials, community, developer feedback loops |
| `legal-advisor` | opus | Legal risk review, contracts, licensing guidance |
| `license-engineer` | sonnet | OSS license compliance, SBOM, dependency audits |
| `product-manager` | sonnet | Roadmaps, PRDs, prioritization, stakeholder alignment |
| `project-manager` | haiku | Project planning, WBS, risk register, status reporting |
| `sales-engineer` | sonnet | Technical sales support, demos, POCs, RFP responses |
| `scrum-master` | haiku | Sprint ceremonies, impediment removal, Scrum coaching |
| `technical-writer` | sonnet | User guides, runbooks, API docs, style guides |
| `ux-researcher` | sonnet | User research, usability studies, personas, journey maps |
| `wordpress-master` | sonnet | WordPress theme/plugin development, WooCommerce |

### 09 · Meta & Orchestration

| Agent | Model | Purpose |
|---|---|---|
| `agent-distinctiveness-advocate` | sonnet | Validate new agents for MECE compliance; diagnose routing ambiguity; maintain agent semantic distinctiveness |
| `agent-installer` | sonnet | Install and configure subagents into Claude Code |
| `agent-organizer` | sonnet | Organize, categorize, and route tasks to the right agent |
| `codebase-orchestrator` | opus | Coordinate multi-agent work across a codebase |
| `context-manager` | sonnet | Manage context windows, compress history, maintain state |
| `error-coordinator` | sonnet | Cross-agent error aggregation, recovery coordination |
| `it-ops-orchestrator` | opus | IT operations orchestration across systems and teams |
| `knowledge-synthesizer` | opus | Synthesize findings across agents into coherent outputs |
| `multi-agent-coordinator` | opus | Design and run multi-agent pipelines |
| `performance-monitor` | sonnet | Monitor agent performance metrics and throughput |
| `release-manager` | sonnet | Cross-spoke release trains: dependency-order cut & tagging, cross-repo changelog aggregation, semver |
| `task-distributor` | sonnet | Break work into tasks and assign to appropriate agents |
| `workflow-orchestrator` | opus | Business process workflows, state machines, saga patterns |

### 10 · Research & Analysis

| Agent | Model | Purpose |
|---|---|---|
| `competitive-analyst` | sonnet | Competitive landscape, feature comparison, positioning |
| `data-researcher` | sonnet | Data gathering, source evaluation, synthesis |
| `market-researcher` | sonnet | Market sizing, segmentation, trend identification |
| `project-idea-validator` | sonnet | Validate project ideas, feasibility, market fit |
| `research-analyst` | sonnet | Primary and secondary research, structured analysis |
| `scientific-literature-researcher` | opus | Academic literature review, paper synthesis |
| `search-specialist` | haiku | Web search, information retrieval, fact-checking |
| `spike-researcher` | sonnet | Time-boxed technical spikes: library eval, runnable PoC code, build-vs-buy recommendation |
| `trend-analyst` | sonnet | Technology and market trend analysis |

### 11 · Enterprise Architecture

TOGAF ADM-aligned EA agents for US commercial and federal contexts. See `.claude/agents/categories/11-enterprise-architecture/README.md` for engagement flows.

| Agent | Model | TOGAF Phase | Purpose |
|---|---|---|---|
| `enterprise-architect` | opus | All | TOGAF ADM orchestrator, Architecture Vision, Repository governance |
| `togaf-adm-advisor` | sonnet | All | Phase deliverables, artifact templates, ADM tailoring |
| `wardley-strategist` | opus | A, B, E | Wardley value chains, evolution, doctrine, climate, gameplay |
| `business-architect` | sonnet | B | Capability maps, value streams, BIZBOK operating models |
| `solution-architect` | sonnet | E, F | ABB→SBB translation, solution docs, vendor evaluation, transition architecture |
| `information-architect` | sonnet | C (Data) | CDM/LDM, MDM, data governance, lineage, DAMA DMBOK |
| `capability-planner` | sonnet | B, E, F | WSJF investment prioritization, capability roadmaps |
| `integration-architect` | sonnet | C (App), D | API strategy, EDA, canonical data model, ESB modernization |
| `security-architect` | opus | Cross-cutting | Zero Trust (NIST SP 800-207), NIST CSF 2.0, FedRAMP, CMMC |
| `platform-architect` | sonnet | D | IDP, Team Topologies, Backstage, golden paths, DORA |
| `us-regulatory-architect` | sonnet | Cross-cutting | FISMA/RMF, HIPAA, CMMC 2.0, PCI DSS v4, SOX, CCPA/CPRA |

---

## Agent Selection Guide

| Task | Use |
|---|---|
| New feature end-to-end | `fullstack-developer` or `codebase-orchestrator` |
| API design only | `api-designer` |
| Language-specific work | matching language specialist |
| Security concern | `security-auditor` → `penetration-tester` |
| Slow queries / perf | `database-optimizer` or `performance-engineer` |
| Multi-step complex task | `multi-agent-coordinator` + specialists |
| GitHub board / issues | `github-projects-manager` |
| Unknown — find an agent | `/subagent-catalog:search <keyword>` |
| Enterprise architecture program | `enterprise-architect` (orchestrator) |
| Strategic positioning / investment | `wardley-strategist` + `capability-planner` |
| Business capability model | `business-architect` → `capability-planner` |
| FedRAMP / FISMA / CMMC | `us-regulatory-architect` + `security-architect` |
| Platform / IDP design | `platform-architect` + `integration-architect` |
| TOGAF phase deliverable | `togaf-adm-advisor` |

## Agent Chaining Patterns

**Feature implementation:**
```
product-manager → architect-reviewer → fullstack-developer → code-reviewer → security-auditor
```

**PI Planning:**
```
product-manager (backlog grooming) → scrum-master (iteration setup) → github-projects-manager (board population)
```

**Production incident:**
```
incident-responder (triage) → debugger (root cause) → sre-engineer (postmortem) → deployment-engineer (fix)
```

**Enterprise architecture program (full TOGAF ADM):**
```
enterprise-architect (Preliminary + Phase A: Vision)
  → wardley-strategist (strategic landscape map)
  → business-architect (Phase B: capabilities + value streams)
  → capability-planner (WSJF scoring + investment case)
  → information-architect (Phase C: data architecture)
  → integration-architect (Phase C: application integration)
  → security-architect (security by design, cross-cutting)
  → us-regulatory-architect (compliance constraints)
  → platform-architect (Phase D: technology standards)
  → solution-architect (Phase E/F: SBBs + transition architecture)
  → enterprise-architect (Phase G: Architecture Contract)
```

**Strategic investment decision:**
```
wardley-strategist (/wardley [domain]) → capability-planner (WSJF) → enterprise-architect (roadmap update)
```

**Platform engineering program:**
```
platform-architect (IDP architecture + Team Topologies)
  → security-architect (shift-left security design)
  → integration-architect (API gateway + service mesh)
  → capability-planner (platform capability roadmap)
  → sre-engineer (SLOs for platform services)
```
