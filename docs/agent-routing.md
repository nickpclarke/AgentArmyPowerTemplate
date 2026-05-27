# Agent routing reference

Extracted from CLAUDE.md to keep the per-session context budget small. This is the **full** routing table — CLAUDE.md keeps the rules; this file keeps the lookups.

For the agent roster itself, see [docs/agents.md](agents.md). For language-tier routing, see [.claude/agents/categories/02-language-specialists/TAXONOMY.md](../.claude/agents/categories/02-language-specialists/TAXONOMY.md). For Copilot-side setup, see [docs/copilot.md](copilot.md).

## Copilot army — label-driven

Apply the label and let automation handle it:

| Trigger | Label | Copilot does |
|---|---|---|
| Bug or Story, Size XS/S | `copilot-task` | Creates branch, implements, opens PR |
| Any PR | (automatic) | Inline first-pass review |
| Board question | `@board-manager` in Copilot Chat | Queries board, returns status |

## Claude Code army — delegate by concern

| Concern | Agent |
|---|---|
| Requirements / user stories | `business-analyst` |
| Architecture decisions | `architect-reviewer` |
| Sprint / PI planning | `scrum-master` |
| Frontend implementation | `frontend-developer` (greenfield / multi-framework), `react-specialist` (existing React optimization) |
| Frontend: Language-level | `javascript-pro`, `typescript-pro` |
| Frontend: Mobile/responsive | `mobile-web-specialist`, `mobile-developer` (cross-platform) |
| Backend implementation | See **Language Specialists** (below) |
| Backend: Language-level | `python-pro`, `golang-pro`, `rust-engineer`, `java-architect`, etc. (see category 02) |
| Deep code review (large PRs, `needs-deep-review` label) | `/review-pr` skill |
| Security audit | `security-auditor` or `/security-review` skill |
| Agent hits decision point requiring human judgment | `hitl-coordinator` |
| Creative/architectural divergence needs human input | `hitl-coordinator` |
| Surfacing decision artifacts to GitHub Projects board | `hitl-coordinator` |
| Agent governance / MECE validation | `agent-distinctiveness-advocate` (pre-merge agent onboarding, routing ambiguity diagnosis) |
| GCP infrastructure (Cloud Run, Cloud SQL, GKE, Vertex AI, IAM, Cloud Build) | `gcp-infra-engineer` |
| AWS infrastructure (Fargate, RDS, Bedrock, EKS, CDK/CloudFormation, IAM/SCP) | `aws-infra-engineer` |
| Azure infrastructure (Container Apps, Bicep, Entra ID, Azure OpenAI) | `azure-infra-engineer` |
| Vercel platform (Functions, Postgres/KV/Blob, edge middleware, monorepo, AI SDK) | `vercel-engineer` |
| Multi-cloud strategy, provider selection, landing zone design | `cloud-architect` |
| Cloud provider / stack choice guide | See [docs/cloud-serving.md](cloud-serving.md) |
| CI/CD system & infra automation | `devops-engineer` (builds/operates pipelines, containerization, infra automation) |
| Release & rollout strategy (single service) | `deployment-engineer` (canary/blue-green/rollback, artifact promotion, GitOps) |
| Cross-spoke release trains | `release-manager` (dependency-order cut & tagging, cross-repo changelog aggregation) |
| Reliability & SLOs | `sre-engineer` (error budgets, toil reduction, reliability culture) |
| Telemetry & instrumentation | `observability-engineer` (OpenTelemetry, metrics/logs/traces pipelines, Grafana/Prometheus) |
| Inspect/manage operator's local docker fleet | **untool fleet suite** — `mcp__local-fleet__fleet_*` tools. Read-only (`fleet_ps` / `fleet_inspect` / `fleet_logs`) auto-approvable; write tools (`fleet_up` / `fleet_down` / `fleet_restart` / `fleet_build` / `fleet_deploy`) require per-call approval. See [tools/mcp-local-fleet/README.md](../tools/mcp-local-fleet/README.md). |
| Cloud cost / FinOps | `finops-engineer` (cost visibility, unit economics, rightsizing, commitments) |
| API gateway & edge policy | `api-gateway-engineer` (rate limiting, edge authN/Z, routing across spoke APIs) |
| Performance | `performance-engineer` (diagnose bottlenecks across any layer) |
| Feature flags & progressive delivery | `feature-flag-engineer` (targeting, lifecycle, kill switches, flag-debt) |
| Event-driven messaging | `async-messaging-engineer` (Kafka/RabbitMQ/SQS-SNS/NATS, AsyncAPI schemas, DLQ) |
| Contract testing across spokes | `contract-test-engineer` (Pact, provider verification, schema-drift) |
| DB schema migrations | `schema-migration-engineer` (Flyway/Liquibase/Alembic, zero-downtime evolution) |
| Data pipeline work (dlt, ELT, connectors) | `dlt-engineer` (source → destination, incremental loading, schema evolution) |
| Data analysis & modeling | `data-analyst`, `data-scientist`, `data-engineer` |
| Data Vault 2.1 strategy (raw vs business, hash algo, identity, materialization) | `data-vault-architect` (loads [docs/data-vault/strategy.md](data-vault/strategy.md)) |
| Data Vault 2.1 logical model (hubs / links / sats / refs / multi-active / effectivity) | `data-vault-modeler` (outputs YAML against `tools/data-vault/model.schema.json`) |
| Data Vault 2.1 build & load (Datavault4dbt, hash keys/diffs, PIT/bridge, info marts) | `data-vault-engineer` (uses `tools/data-vault/` toolkit) |
| Production ML lifecycle | `machine-learning-engineer` (training pipelines, serving, retraining); `mlops-engineer` (ML platform/CI-CD) |
| UFO/OntoUML conceptual modeling (primary authoring) | `ontologist-ufo` (stereotypes, relators, anti-patterns, gUFO OWL — loads `ufo-ontology` skill) |
| BFO 2020 / OBO / CCO realist ontology + interop projection | `ontologist-bfo` (continuant/occurrent, Aristotelian defs, BFO/CCO sidecar — loads `bfo-ontology` skill) |
| Applied OWL/RDFS/SHACL, ontology reuse & alignment, competency questions | `ontologist-generalist` (foundation-agnostic mid-tier + cluster router) |
| Knowledge graph construction, rules, reasoners, SPARQL, KB lifecycle | `knowledge-engineer` (operationalizes ontologies into running systems) |
| Taxonomies, thesauri, SKOS, controlled vocabularies, facets | `taxonomist` (non-axiomatized knowledge organization) |
| Technical spike / build-vs-buy PoC | `spike-researcher` (time-boxed, runnable PoC + recommendation) |
| Developer adoption / DevRel | `developer-advocate` (sample apps, external tutorials, community) |

## Cross-cutting routing clusters

Pick by lifecycle stage, not by keyword overlap:

- **Contract cluster:** `api-designer` (design the contract) → `contract-test-engineer` (enforce it at runtime/CI across spokes) → `schema-migration-engineer` (evolve the DB behind it safely).
- **Delivery/ops cluster:** `devops-engineer` (build & operate CI/CD + infra) → `deployment-engineer` (release/rollout strategy for one service) → `release-manager` (coordinate release trains across spoke repos) → `observability-engineer` (produce telemetry) → `sre-engineer` (consume it for SLOs/error budgets) → `finops-engineer` (govern cost) → `api-gateway-engineer` (edge policy).
- **Knowledge/ontology cluster** (formality gradient): `taxonomist` (SKOS/taxonomies, no axioms) → `ontologist-generalist` (applied OWL/SHACL + cluster router) → `ontologist-ufo` / `ontologist-bfo` (foundational: UFO-design vs BFO-realist, *coordinating* on the dual projection) → `knowledge-engineer` (populate, reason, query). Distinct from `information-architect` (enterprise data architecture/governance) and `knowledge-synthesizer` (agent-interaction learning). See [.claude/agents/categories/12-knowledge-ontology/README.md](../.claude/agents/categories/12-knowledge-ontology/README.md).
- **Data Vault cluster** (lifecycle): `data-vault-architect` (raw vs business placement, identity strategy, materialization choice) → `data-vault-modeler` (hubs / links / sats / refs in YAML against `tools/data-vault/model.schema.json`) → `data-vault-engineer` (Datavault4dbt loaders, hash keys via `tools/data-vault/hash.{mjs,py}`, PIT/bridge, marts). Sits *downstream* of the [canonical data model contract](decisions/ARC-ADR-009-canonical-data-model-arrow.md), *upstream* of marts. Anchor decision: [ARC-ADR-026](decisions/ARC-ADR-026-data-vault-2-1-methodology.md). Full strategy: [docs/data-vault/](data-vault/).

## Enterprise Architecture specialists (TOGAF ADM-aligned)

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
| Architecture Decision Records (new ADR draft) | `/ea-adr` skill → `togaf-adm-advisor` |
| ADR review / second-opinion on existing decisions | `/ea-adr review …` → `architect-reviewer` |

## Language Specialists (Category 02)

Three tiers, structured for MECE distinctiveness:

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

**Full routing guide & tie-breakers:** [.claude/agents/categories/02-language-specialists/TAXONOMY.md](../.claude/agents/categories/02-language-specialists/TAXONOMY.md) — 15+ concrete examples, edge case handling, escalation patterns.
