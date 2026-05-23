# CLAUDE.md

AI assistant guidance for the AgentArmy template repository.

## What This Repo Is

AgentArmy is a starter template for AI-powered software development. It coordinates two autonomous AI armies and a shared planning surface:

- **Claude Code army** — local, deep, strategic: architecture, complex features, SAFE planning, security audits
- **GitHub Copilot army** — GitHub-native, fast, lightweight: PR review, simple task coding, board queries via `@board-manager`
- **GitHub Projects v2** — shared coordination plane both armies read and write
- **GitHub Actions** — routes issues to the right army, syncs board state, automates ceremonies
- **SAFE** — the planning model at team and program level

All significant work is tracked as GitHub issues on the project board. Agents operate as specialists — delegate to the right agent, in the right army, rather than doing everything generalist.

## Hub vs Spoke Mode (N-Layer)

AgentArmy is intended to be used as a **Hub template** that generates many **Spoke repos** (one per layer: UI, API, worker, mobile, infra, etc.).

- **If you are in the Hub repo** (the AgentArmy template itself): treat deliverables as template artifacts (workflows in `.github/workflows/`, agent definitions in `.claude/agents/`, docs in `docs/`, and root config). Do not assume an application exists.
- **If you are in a Spoke repo** (a layer repo created from this template): treat the repository as the *actual layer implementation*. Prefer contract-first changes (OpenAPI/GraphQL/AsyncAPI/shared types), use mocks/stubs for parallel work, and integrate “late” via environment variables instead of tight repo-to-repo coupling.

When in doubt, infer intent from the issue/task context (e.g., “update the template” vs “implement the API/UI/worker”), and ask for clarification if the repo’s role is ambiguous.

## Repository Layout

```
.claude/agents/categories/  → specialist agent definitions (11 categories)
.claude/commands/           → local slash commands (/wardley, /ea-adr, /capability-map)
.github/workflows/          → GitHub Actions: auto-status, routing, agent-onboarding-validation
docs/                       → user-facing docs: agents.md, setup.md, github-projects.md, capabilities
extensions/board-manager/   → Azure-deployable Copilot Chat extension (@board-manager)
planning/
  ├── release-trains/       → RT1–RT4 strategic roadmap & issue planning
  ├── backlog/              → GitHub Issues index, board population checklist
  ├── synthesis/            → ArcKit integration, research artifacts
  ├── roadmap/              → Platform 6-month vision
  ├── governance/           → FILE_ORGANIZATION.md (folder strategy)
  └── meta/                 → Governance layer: principles, agent validation, learning loops
```

## Working in This Repo

### GitHub Projects is the task backbone

Before starting significant work, check whether an issue exists on the board. If not, create one and add it to the project. Use `gh` CLI:

```bash
# Create an issue and add to project
gh issue create --title "..." --body "..." --label "Feature"
gh project item-add 1 --owner OWNER --url "https://github.com/OWNER/AgentArmy/issues/N"
```

Set the `Type` and `PI` fields on items so they're properly categorised.

### Route work to the right army first, then the right agent

**Copilot army** — apply label and let automation handle it:

| Trigger | Label | Copilot does |
|---|---|---|
| Bug or Story, Size XS/S | `copilot-task` | Creates branch, implements, opens PR |
| Any PR | (automatic) | Inline first-pass review |
| Board question | `@board-manager` in Copilot Chat | Queries board, returns status |

**Claude Code army** — delegate to the right specialist:

| Concern | Agent |
|---|---|
| Requirements / user stories | `business-analyst` |
| Architecture decisions | `architect-reviewer` |
| Sprint / PI planning | `scrum-master` |
| Frontend implementation | `frontend-developer` (greenfield / multi-framework), `react-specialist` (existing React optimization) |
| Frontend: Language-level | `javascript-pro`, `typescript-pro` |
| Frontend: Mobile/responsive | `mobile-web-specialist`, `mobile-developer` (cross-platform) |
| Backend implementation | See **Language Specialists Routing Rules** (below) |
| Backend: Language-level | `python-pro`, `golang-pro`, `rust-engineer`, `java-architect`, etc. (see category 02) |
| Deep code review (large PRs, `needs-deep-review` label) | `/review-pr` skill |
| Security audit | `security-auditor` or `/security-review` skill |
| Agent hits decision point requiring human judgment | `hitl-coordinator` |
| Creative/architectural divergence needs human input | `hitl-coordinator` |
| Surfacing decision artifacts to GitHub Projects board | `hitl-coordinator` |
| Agent governance / MECE validation | `agent-distinctiveness-advocate` (pre-merge agent onboarding, routing ambiguity diagnosis) |
| CI/CD system & infra automation | `devops-engineer` (builds/operates pipelines, containerization, infra automation) |
| Release & rollout strategy (single service) | `deployment-engineer` (canary/blue-green/rollback, artifact promotion, GitOps) |
| Cross-spoke release trains | `release-manager` (dependency-order cut & tagging, cross-repo changelog aggregation) |
| Reliability & SLOs | `sre-engineer` (error budgets, toil reduction, reliability culture) |
| Telemetry & instrumentation | `observability-engineer` (OpenTelemetry, metrics/logs/traces pipelines, Grafana/Prometheus) |
| Cloud cost / FinOps | `finops-engineer` (cost visibility, unit economics, rightsizing, commitments) |
| API gateway & edge policy | `api-gateway-engineer` (rate limiting, edge authN/Z, routing across spoke APIs) |
| Performance | `performance-engineer` (diagnose bottlenecks across any layer) |
| Feature flags & progressive delivery | `feature-flag-engineer` (targeting, lifecycle, kill switches, flag-debt) |
| Event-driven messaging | `async-messaging-engineer` (Kafka/RabbitMQ/SQS-SNS/NATS, AsyncAPI schemas, DLQ) |
| Contract testing across spokes | `contract-test-engineer` (Pact, provider verification, schema-drift) |
| DB schema migrations | `schema-migration-engineer` (Flyway/Liquibase/Alembic, zero-downtime evolution) |
| Data pipeline work (dlt, ELT, connectors) | `dlt-engineer` (source → destination, incremental loading, schema evolution) |
| Data analysis & modeling | `data-analyst`, `data-scientist`, `data-engineer` |
| Production ML lifecycle | `machine-learning-engineer` (training pipelines, serving, retraining); `mlops-engineer` (ML platform/CI-CD) |
| Technical spike / build-vs-buy PoC | `spike-researcher` (time-boxed, runnable PoC + recommendation) |
| Developer adoption / DevRel | `developer-advocate` (sample apps, external tutorials, community) |

**Cross-cutting routing clusters** (pick by lifecycle stage, not by keyword overlap):

- **Contract cluster:** `api-designer` (design the contract) → `contract-test-engineer` (enforce it at runtime/CI across spokes) → `schema-migration-engineer` (evolve the DB behind it safely).
- **Delivery/ops cluster:** `devops-engineer` (build & operate CI/CD + infra) → `deployment-engineer` (release/rollout strategy for one service) → `release-manager` (coordinate release trains across spoke repos) → `observability-engineer` (produce telemetry) → `sre-engineer` (consume it for SLOs/error budgets) → `finops-engineer` (govern cost) → `api-gateway-engineer` (edge policy).

**Enterprise Architecture specialists** — TOGAF ADM-aligned:

| Concern | Agent |
|---|---|
| Architecture program (all phases) | `enterprise-architect` |
| TOGAF ADM phase guidance / artifacts | `togaf-adm-advisor` |
| Strategic positioning, Wardley maps | `wardley-strategist` or `/wardley` |
| Business capabilities, value streams | `business-architect` or `/capability-map` |
| Capability investment prioritization | `capability-planner` |
| Solution architecture, vendor selection | `solution-architect` |
| Data / information architecture | `information-architect` |
| API strategy, integration patterns | `integration-architect` |
| Enterprise security (Zero Trust, FedRAMP) | `security-architect` |
| IDP, Team Topologies, platform design | `platform-architect` |
| FISMA, HIPAA, CMMC, SOX, CCPA | `us-regulatory-architect` |
| Architecture Decision Records | `/ea-adr` skill |

### Meta-Planning & Governance (ARMY_PRINCIPLES)

The agent army operates under **7 foundational principles** defined in `/planning/meta/principles/ARMY_PRINCIPLES.md`:

1. **Error Escalation** — Every agent escalates failures to `error-coordinator`
2. **Knowledge Feedback** — Agents feed insights to `knowledge-synthesizer`
3. **Skill Scaffolding** — Reusable, composable skills exposed by agents
4. **Hook Integration** — Agents listen to session lifecycle events
5. **Delegation Direction** — Down-hierarchy only, no UP-delegation, no circular references
6. **MECE** (Mutual Exclusive, Collectively Exhaustive) — Boundary rules disambiguate routing
7. **Observable Decisions** — Decision-making is logged and queryable

**New agents must pass `AGENT_ONBOARDING_RUBRIC.md` before merge**, which operationalizes these principles. See `/planning/meta/decisions/AGENT_ONBOARDING_RUBRIC.md` for validation checklist.

**Planning structure (3 layers):**

| Layer | Location | Purpose | Cadence |
|---|---|---|---|
| **Tasks** | GitHub Projects board | Issue tracking, sprints, burndown | Per-sprint |
| **Strategy** | `/planning/release-trains/` | Feature delivery roadmap (RT1–RT4) | Quarterly |
| **Governance** | `/planning/meta/` | Principles, agent validation, learning loops | Quarterly + continuous |

**For fork users (Spokes):** See `/planning/meta/spoke-templates/SPOKE_META_PLANNING_TEMPLATE.md` for how to inherit Hub principles while customizing for your layer.

### Language Specialists Routing Rules (Category 02)

**The three tiers** for language work (structured for MECE distinctiveness):

| Tier | When to Use | Example Agents |
|------|---|---|
| **Languages/** | Need language idioms, type system, performance, runtime semantics | `python-pro`, `golang-pro`, `typescript-pro`, `rust-engineer`, `java-architect` |
| **Frameworks/web/** | Building an app WITH a web framework (conventions, libraries, ORM) | `django-developer`, `fastapi-developer`, `react-specialist`, `nextjs-developer`, `rails-expert` |
| **Frameworks/mobile/** | Building a mobile app (React Native, Flutter) | `expo-react-native-expert`, `flutter-expert` |
| **Platforms/** | Version-pinned (.NET versions) or OS-bound work (Windows automation) | `dotnet-core-expert`, `dotnet-framework-4.8-expert`, `powershell-7-expert` |

**Quick decision rule:**
- "Build a REST API in Python" → `python-pro` (design) → `fastapi-developer` (framework implementation)
- "Optimize React component perf" → `react-specialist`
- "Debug async/await issue" → `javascript-pro` or `typescript-pro`
- "Migrate to .NET Core" → `dotnet-framework-4.8-expert` → `dotnet-core-expert`

**Full routing guide & tie-breakers:** See [.claude/agents/categories/02-language-specialists/TAXONOMY.md](.claude/agents/categories/02-language-specialists/TAXONOMY.md) for:
- 15+ concrete examples (framework vs. language decision)
- Edge case handling (JavaScript/TypeScript, .NET versions, PowerShell, mobile)
- Escalation patterns (when to involve multiple agents)

Full roster: [docs/agents.md](docs/agents.md) | Language routing: [TAXONOMY.md](.claude/agents/categories/02-language-specialists/TAXONOMY.md) | Copilot setup: [docs/copilot.md](docs/copilot.md)

### Issue type conventions

Label every issue with its SAFE type:

| Label | Meaning | Typical hierarchy |
|---|---|---|
| `Epic` | Large body of work (>1 PI) | Top level — no parent |
| `Feature` | Deliverable capability within a PI | Child of Epic milestone |
| `Story` | User-facing value, completable in 1 sprint | Sub-issue of Feature |
| `Enabler` | Technical infrastructure or exploration | Same level as Story |
| `Bug` | Defect | Same level as Story |
| `Spike` | Time-boxed research | Same level as Story |
| `Decision` | HITL decision artifact — requires human or AI-app judgment | Created by `hitl-coordinator`; blocks linked issues |

### PR conventions

PR body must contain `Closes #N`, `Fixes #N`, or `Resolves #N` to trigger the `auto-status` workflow. This is what moves issues from *In progress* to *Done* automatically.

## HITL Decision Pattern

When an agent hits a creative fork, architectural divergence, or judgment call exceeding its authority, it escalates to `hitl-coordinator` which creates a **Decision Artifact** issue on the board.

**Decision Artifact lifecycle:**
1. Agent calls `hitl-coordinator` → Decision issue created with `hitl-decision` label, `Decision` Type, Status = "Awaiting Decision"
2. Blocked issues get `awaiting-human` label and a comment linking the decision
3. Assignee (human or AI app) reviews, comments with choice, closes the issue
4. Automation unblocks linked issues, posts decision context, resets Status to "Todo"

**Board commands for decisions:**
- `/decisions` — list all open Decision Artifacts grouped by assignee type (human / copilot / claude-app / gemini-app)
- Filter board by Status = "Awaiting Decision" or Label = `hitl-decision` to find items needing attention

**Assignee labels** (for board filtering):
- `assignee:human` (soft purple) — specific human
- `assignee:copilot` (Copilot blue) — GitHub Copilot
- `assignee:claude-app` (Claude amber) — Claude GitHub App
- `assignee:gemini-app` (Gemini blue) — Gemini GitHub App

**When agents should escalate:** multiple valid design paths with strategic/values implications, architectural divergence, risk acceptance, scope changes, priority conflicts. See `hitl-coordinator` agent and [docs/hitl.md](docs/hitl.md) for the full pattern.

## GitHub Projects Field Reference

| Field | When to set |
|---|---|
| `Status` | Auto-managed by Actions; only override manually if needed. Values: Todo, In progress, **Awaiting Decision**, Done (the board option is literally `In progress` — lowercase "p"; workflow code and docs must match that casing) |
| `Type` | Set on creation |
| `PI` | Set to current Program Increment (e.g. `PI-1`) |
| `Priority` | P0 = must ship this sprint; P1 = should ship this PI; P2 = backlog |
| `Size` | T-shirt estimate: XS ≤ 0.5 day, S ≤ 1 day, M ≤ 3 days, L ≤ 1 week, XL > 1 week |
| `Estimate` | Story points (Fibonacci: 1, 2, 3, 5, 8, 13) |
| `Iteration` | Assign to the sprint when committed |
| `Start date` / `Target date` | Set during sprint planning |
| `Parent issue` | Link Stories to their parent Feature |

## SAFE Workflow Summary

- **PI** = Program Increment (~10 weeks / 5 sprints), tracked as a GitHub Milestone.
- **Sprint** = 2-week iteration via the `Iteration` field.
- **Definition of Ready**: Type, PI, Size, Estimate set + acceptance criteria in the body.
- **Definition of Done**: PR merged with a `Closes #N` link so `auto-status` moves the issue.

## Available Skills (Claude Code)

Run these with `/skill-name` in the Claude Code prompt:

| Skill | What it does |
|---|---|
| `/commit` | Stage and commit with a well-formed message |
| `/commit-push-pr` | Commit, push, and open a PR in one step |
| `/review-pr` | Multi-agent PR review |
| `/security-review` | Security audit of current branch changes |
| `/revise-claude-md` | Update this file with session learnings |
| `/simplify` | Review and clean up changed code |
| `/wardley [domain]` | Full Wardley analysis pipeline — value chain, map (OWM), doctrine, climate, gameplay |
| `/ea-adr [decision topic]` | Architecture Decision Record in MADR v4.0 format |
| `/capability-map [domain]` | Business capability model + investment heat map |

## GitHub Actions in This Repo

| Workflow | Do not manually override |
|---|---|
| `auto-add-to-project` | Runs on every new issue/PR — don't manually add items |
| `auto-status` | Runs on PR open/merge — don't manually change Status unless correcting |
| `copilot-review` | Adds Copilot as reviewer and flags large PRs — don't remove `needs-deep-review` label |
| `copilot-coding-agent` | Routes labelled issues — trust the routing, don't reassign manually |

## Copilot Handoff Conventions

- When closing a `copilot-task` issue via PR, ensure the PR body contains `Closes #N` so `auto-status` fires correctly
- If Copilot's PR needs a deep review, add `needs-deep-review` label and run `/review-pr`
- If Copilot's implementation is wrong or too shallow, remove `copilot-task`, add `agent-army-task`, and handle with Claude Code

## Gotchas

- **This is a template repo.** When forked into a real project, owner/project references in `.github/workflows/*.yml` are hardcoded (e.g. `nickpclarke`, project number `1`) and must be edited by hand — see [docs/setup.md](docs/setup.md).
- **`PROJECT_TOKEN`** must be a **classic** PAT with the `project` scope checked — the default `GITHUB_TOKEN` cannot write to Projects v2 boards. Used by every workflow that updates the board.
- **`GITHUB_TOKEN`** (built-in) is only enough for `stale` and `label-pr-size`.
- `.claude/settings.local.json` contains personal permissions — gitignore in forks.
- `auto-status` only fires when a PR body contains `Closes #N` / `Fixes #N` / `Resolves #N`. Without it, the linked issue stays in *In progress*.
