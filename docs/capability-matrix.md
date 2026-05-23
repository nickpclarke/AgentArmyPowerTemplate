# Agent Capability Matrix

This document maps the 169-agent AgentArmy roster to their primary capability domains. It is the authoritative reference for routing decisions, MECE gap analysis, and onboarding new agents.

**Maintained by:** `agent-distinctiveness-advocate`
**Validated by:** `node tools/audit-agents.mjs` (see [Validation](#validation))
**Schema:** `.claude/agent-schema.json`
**Template:** `templates/agent-spec-template.md`

---

## Table of Contents

1. [MECE Principle](#mece-principle)
2. [Category Overview](#category-overview)
3. [Category 01 — Core Development](#category-01--core-development)
4. [Category 02 — Language Specialists](#category-02--language-specialists)
5. [Category 03 — Infrastructure](#category-03--infrastructure)
6. [Category 04 — Quality & Security](#category-04--quality--security)
7. [Category 05 — Data & AI](#category-05--data--ai)
8. [Category 06 — Developer Experience](#category-06--developer-experience)
9. [Category 07 — Specialized Domains](#category-07--specialized-domains)
10. [Category 08 — Business & Product](#category-08--business--product)
11. [Category 09 — Meta Orchestration](#category-09--meta-orchestration)
12. [Category 10 — Research & Analysis](#category-10--research--analysis)
13. [Category 11 — Enterprise Architecture](#category-11--enterprise-architecture)
14. [Quick Routing Guide](#quick-routing-guide)
15. [Cross-Cutting Routing Clusters](#cross-cutting-routing-clusters)
16. [Known Overlaps & Boundary Rules](#known-overlaps--boundary-rules)
17. [Validation](#validation)

---

## MECE Principle

The AgentArmy roster is governed by the **MECE principle** (Mutually Exclusive, Collectively Exhaustive):

- **Mutually Exclusive:** Each concern type has one primary agent. Two agents should not have meaningfully identical descriptions without an explicit boundary rule disambiguating them.
- **Collectively Exhaustive:** The full roster covers the complete software delivery lifecycle — from requirements to production observability, from language idioms to enterprise architecture.

**Operationalizing MECE:**

1. **Boundary rules** — when two agents share a concern area, each description contains an explicit "use me for X; use AgentY for Y" statement.
2. **Category taxonomy** — the 11 categories partition the routing space by lifecycle phase and concern type, not by technology keyword.
3. **Automated audit** — `tools/audit-agents.mjs` detects agents sharing high-frequency keywords (potential overlap) and categories with fewer than 3 agents (potential gap).
4. **Onboarding rubric** — new agents pass `planning/meta/decisions/AGENT_ONBOARDING_RUBRIC.md` before merge.

---

## Category Overview

| # | Category | Agents | Primary Domain |
|---|---|---|---|
| 01 | Core Development | 13 | Application building: APIs, UI, mobile, real-time, distributed systems |
| 02 | Language Specialists | 30 | Language idioms, web frameworks, mobile frameworks, platform runtimes |
| 03 | Infrastructure | 19 | Cloud, DevOps, SRE, deployment, cost, networking, observability |
| 04 | Quality & Security | 17 | Testing, code review, security audits, compliance, chaos engineering |
| 05 | Data & AI | 15 | Data pipelines, ML, databases, NLP, RL, MLOps |
| 06 | Developer Experience | 15 | Build tooling, DX, documentation, refactoring, feature flags |
| 07 | Specialized Domains | 13 | Vertical industries and specialized technical domains |
| 08 | Business & Product | 13 | Business analysis, product management, marketing, legal, content |
| 09 | Meta Orchestration | 14 | Agent coordination, error handling, HITL, knowledge synthesis |
| 10 | Research & Analysis | 9 | Market research, competitive analysis, spikes, scientific research |
| 11 | Enterprise Architecture | 11 | TOGAF ADM, Wardley, capability planning, regulatory compliance |
| **Total** | | **169** | |

---

## Category 01 — Core Development

**Scope:** Building new applications and features across the full stack, from API contracts to UI implementation to real-time systems.

| Agent | Primary Skills | Routing Trigger |
|---|---|---|
| `api-designer` | REST/GraphQL API design, OpenAPI 3.1, versioning strategy, authentication patterns, developer experience | Designing new APIs, authoring OpenAPI specs, API versioning |
| `async-messaging-engineer` | Message broker design (Kafka/RabbitMQ/SQS-SNS/NATS), AsyncAPI schemas, DLQ strategy, consumer-group coordination | Event-driven messaging, broker design, async event schema governance |
| `backend-developer` | Server-side APIs, microservice implementation, database integration, authentication, scalability | Building API servers, business logic, production backend services |
| `design-bridge` | DESIGN.md extraction, design token translation, visual fidelity instruction generation | Translating design files to agent-ready instructions |
| `electron-pro` | Electron framework, cross-platform desktop apps, auto-updates, system integration, offline capability | Desktop app development, web-to-desktop port |
| `frontend-developer` | Multi-framework UI (React/Vue/Angular), component architecture, state management, responsive design | Greenfield web UIs, multi-framework integration |
| `fullstack-developer` | End-to-end feature development, rapid prototyping, database-to-UI implementation | Complete features, small-to-medium projects, prototypes |
| `graphql-architect` | GraphQL schema design, federation, resolver optimization, subscriptions, migration from REST | GraphQL API design, schema optimization, federation setup |
| `microservices-architect` | Service decomposition, inter-service communication, distributed transactions, service mesh | Microservices design, monolith decomposition, distributed system challenges |
| `mobile-developer` | React Native, Flutter, iOS/Android native, offline capability, push notifications, app store | Cross-platform mobile apps, mobile-specific features |
| `mobile-web-specialist` | Responsive design, PWA, mobile-first CSS, touch UX, viewport optimization | Mobile-optimized web experiences, responsive design |
| `ui-designer` | Design systems, typography, color theory, interaction patterns, visual hierarchy, brand identity | Visual design, design system creation, design-to-dev handoff |
| `websocket-engineer` | WebSocket servers, Socket.io, real-time features, connection scaling, live collaboration | Real-time chat, live notifications, collaborative features |

**Key boundary rules:**
- `api-designer` (design contracts) vs `backend-developer` (implement them)
- `graphql-architect` (complex federation/optimization) vs `api-designer` (initial GraphQL API design)
- `mobile-developer` (native/cross-platform apps) vs `mobile-web-specialist` (responsive web)
- `frontend-developer` (greenfield/multi-framework) vs `react-specialist` (existing React optimization, in category 02)

---

## Category 02 — Language Specialists

**Scope:** Language idioms, type systems, runtime semantics, web frameworks, mobile frameworks, and version-pinned platform runtimes.

**Three-tier taxonomy:**

| Tier | When to Use | Agents |
|---|---|---|
| **Languages** | Need language idioms, type system, performance, runtime semantics | `cpp-pro`, `csharp-developer`, `elixir-expert`, `golang-pro`, `java-architect`, `javascript-pro`, `kotlin-specialist`, `php-pro`, `python-pro`, `rust-engineer`, `sql-pro`, `swift-expert`, `typescript-pro` |
| **Web Frameworks** | Building an app WITH a web framework (conventions, ORM, routing) | `angular-architect`, `django-developer`, `fastapi-developer`, `laravel-specialist`, `nextjs-developer`, `node-specialist`, `rails-expert`, `react-specialist`, `spring-boot-engineer`, `symfony-specialist`, `vue-expert` |
| **Mobile Frameworks** | Building a mobile app (React Native, Flutter) | `expo-react-native-expert`, `flutter-expert` |
| **Platforms** | Version-pinned (.NET) or OS-bound (Windows automation) | `dotnet-core-expert`, `dotnet-framework-4.8-expert`, `powershell-5.1-expert`, `powershell-7-expert` |

**Quick decision rule:**
- "Build a REST API in Python" → `python-pro` (language design) then `fastapi-developer` (framework)
- "Optimize React component rendering" → `react-specialist`
- "Debug async/await issues" → `javascript-pro` or `typescript-pro`
- "Migrate to .NET Core" → `dotnet-framework-4.8-expert` (assess) then `dotnet-core-expert` (implement)

**Full taxonomy:** `.claude/agents/categories/02-language-specialists/TAXONOMY.md`

---

## Category 03 — Infrastructure

**Scope:** Cloud infrastructure, DevOps CI/CD, deployment strategy, SRE, cost governance, networking, security engineering, and observability.

| Agent | Primary Skills | Routing Trigger |
|---|---|---|
| `api-gateway-engineer` | API gateway policy, rate limiting, edge authentication, routing across spoke APIs | API gateway configuration, edge auth/Z, cross-spoke routing |
| `azure-infra-engineer` | Azure resource provisioning, ARM/Bicep templates, Azure DevOps, AKS, cost management | Azure cloud infrastructure, Azure-native services |
| `cloud-architect` | Multi-cloud strategy, cloud-native patterns, IaaS/PaaS selection, migration planning | Cloud strategy, multi-cloud architecture, cloud migration |
| `database-administrator` | Database provisioning, high availability, backup/recovery, user management, capacity planning | Database infrastructure administration, HA setup |
| `deployment-engineer` | Canary/blue-green deployments, rollback strategy, artifact promotion, GitOps | Release/rollout strategy for a single service |
| `devops-engineer` | CI/CD pipeline design, containerization, infrastructure automation, IaC | CI/CD system build, infra automation, containerization |
| `devops-incident-responder` | Incident detection, CI/CD pipeline failure recovery, rollback automation | Active DevOps/pipeline incident response |
| `docker-expert` | Docker image optimization, multi-stage builds, compose orchestration, registry management | Docker containerization, image optimization |
| `finops-engineer` | Cloud cost visibility, unit economics, rightsizing, commitment recommendations | Cloud cost governance, FinOps implementation |
| `incident-responder` | Incident response coordination, runbook execution, post-mortem facilitation | Production incident response, on-call coordination |
| `kubernetes-specialist` | Kubernetes cluster design, workload deployment, YAML optimization, troubleshooting | Kubernetes cluster operations, workload management |
| `network-engineer` | Network architecture, VPC/subnet design, DNS, load balancing, CDN, firewall rules | Network infrastructure, connectivity, traffic routing |
| `observability-engineer` | OpenTelemetry instrumentation, metrics/logs/traces pipelines, Grafana/Prometheus dashboards | Telemetry setup, observability stack implementation |
| `platform-engineer` | Internal developer platform, golden paths, self-service infrastructure, Backstage | IDP design and implementation, developer platform engineering |
| `security-engineer` | Infrastructure security hardening, IAM, network security groups, compliance controls | Infrastructure security implementation, security controls |
| `sre-engineer` | SLO/SLA/error budget definition, toil reduction, reliability culture, capacity planning | Reliability engineering, error budget management |
| `terraform-engineer` | Terraform module design, state management, provider configuration, refactoring | Terraform IaC authoring and optimization |
| `terragrunt-expert` | Terragrunt configuration, DRY Terraform structures, multi-account management | Terragrunt-based IaC, multi-account Terraform |
| `windows-infra-admin` | Windows Server administration, Active Directory, Group Policy, IIS, WSUS | Windows infrastructure management |

**Delivery cluster routing order:** `devops-engineer` → `deployment-engineer` → `release-manager` → `observability-engineer` → `sre-engineer` → `finops-engineer` → `api-gateway-engineer`

---

## Category 04 — Quality & Security

**Scope:** All testing disciplines, code review, security auditing, compliance, and chaos engineering.

| Agent | Primary Skills | Routing Trigger |
|---|---|---|
| `accessibility-tester` | WCAG compliance, screen reader testing, keyboard navigation, assistive technology | Accessibility audit, WCAG verification |
| `ad-security-reviewer` | Active Directory security, privileged access review, AD misconfiguration detection | AD security review, Kerberos/NTLM audit |
| `ai-writing-auditor` | AI content detection, human-voice rewriting, LLM text pattern removal | Audit and rewrite AI-generated content |
| `architect-reviewer` | Architecture decision review, tech stack evaluation, ADR creation, design feedback | Architecture decisions, design review, ADRs |
| `chaos-engineer` | Failure injection, resilience validation, game day exercises, chaos hypothesis design | Chaos experiments, resilience testing, game days |
| `code-reviewer` | Code quality, security vulnerability detection, best practices, pull request review | Code review, quality assessment |
| `compliance-auditor` | GDPR/HIPAA/PCI DSS/SOC 2/ISO compliance, control implementation, audit preparation | Regulatory compliance, control implementation |
| `contract-test-engineer` | Pact consumer-driven contracts, provider verification, schema-drift detection | Contract testing across services/spokes |
| `debugger` | Single-service bug diagnosis, root cause analysis, error log analysis, stack trace interpretation | Bug fixing in a single service, local debugging |
| `error-detective` | Distributed error correlation, multi-service root cause analysis, error cascade analysis | Cross-service error diagnosis, distributed system debugging |
| `penetration-tester` | Offensive security testing, vulnerability exploitation, risk demonstration, pen test reporting | Authorized penetration testing |
| `performance-engineer` | Performance bottleneck diagnosis, load testing strategy, profiling, optimization across layers | Performance analysis, bottleneck identification |
| `powershell-security-hardening` | PowerShell security baseline, remoting hardening, least-privilege script design | PowerShell security hardening, PS remoting configuration |
| `qa-expert` | QA strategy, test planning, quality metrics, test process design | Quality assurance strategy, test planning across cycles |
| `security-auditor` | Comprehensive security audits, vulnerability analysis, compliance gap identification, risk evaluation | Security audits, compliance assessments |
| `test-automator` | Automated test frameworks, CI/CD integration, unit/integration/e2e/load test implementation | Test automation implementation |
| `ui-ux-tester` | UI functionality testing, UX flow validation, browser/desktop interaction, defect reporting | UI/UX testing, user flow validation |

**Key boundary rules:**
- `debugger` (single service) vs `error-detective` (distributed/multi-service correlation)
- `qa-expert` (strategy/planning) vs `test-automator` (implementation/automation)
- `security-auditor` (comprehensive audit) vs `penetration-tester` (active exploitation/pen test)
- `contract-test-engineer` (cross-service contracts) vs `test-automator` (other automated tests)

---

## Category 05 — Data & AI

**Scope:** Data pipelines, machine learning, database optimization, NLP, reinforcement learning, MLOps, and AI engineering.

| Agent | Primary Skills | Routing Trigger |
|---|---|---|
| `ai-engineer` | AI application development, LLM integration, AI pipeline construction, production AI systems | Building AI-powered applications |
| `data-analyst` | Data analysis, statistical modeling, business intelligence, visualization, reporting | Data analysis, BI reports, statistical insights |
| `data-engineer` | Data pipeline architecture, ETL/ELT, data warehouse design, data lake patterns | Data pipeline construction, warehouse architecture |
| `data-scientist` | ML model development, feature engineering, statistical analysis, experiment design | ML feasibility, model development, experiment design |
| `database-optimizer` | Query optimization, index strategy, execution plan analysis, performance tuning | Database query performance, index optimization |
| `dlt-engineer` | dlt (data load tool) pipelines, source-to-destination connectors, incremental loading, schema evolution | dlt pipeline development, data connector implementation |
| `llm-architect` | LLM system architecture, RAG design, prompt engineering at scale, LLM evaluation frameworks | LLM-based system architecture, RAG infrastructure |
| `machine-learning-engineer` | ML training pipelines, model serving, inference optimization, retraining workflows | Production ML lifecycle, training pipeline, model serving |
| `mlops-engineer` | ML platform CI/CD, experiment tracking, model registry, feature store, deployment automation | ML platform operations, MLOps infrastructure |
| `nlp-engineer` | Natural language processing pipelines, text classification, NER, language model fine-tuning | NLP application development, text processing pipelines |
| `postgres-pro` | PostgreSQL advanced features, performance tuning, replication, partitioning, extensions | Deep PostgreSQL optimization, advanced PG features |
| `prompt-engineer` | Prompt design, chain-of-thought patterns, few-shot examples, evaluation frameworks | LLM prompt optimization, prompt strategy |
| `reinforcement-learning-engineer` | RL algorithm design, reward function engineering, environment simulation, policy optimization | Reinforcement learning systems, RL algorithm implementation |
| `schema-migration-engineer` | Database schema migrations (Flyway/Liquibase/Alembic), zero-downtime evolution, rollback design | DB schema migrations, zero-downtime schema changes |
| `data-researcher` | Data sourcing, dataset curation, data quality assessment, research data pipelines | Research data acquisition, dataset evaluation |

**Key boundary rules:**
- `database-administrator` (category 03, infrastructure provisioning) vs `database-optimizer` (category 05, query/index performance)
- `postgres-pro` (advanced PostgreSQL features) vs `database-optimizer` (generic cross-RDBMS optimization)
- `machine-learning-engineer` (training pipelines, model serving) vs `mlops-engineer` (ML platform CI/CD, infrastructure)
- `ai-engineer` (AI application development) vs `llm-architect` (LLM system architecture)

---

## Category 06 — Developer Experience

**Scope:** Build tooling, developer workflow optimization, documentation, refactoring, feature flags, and CLI/IDE tooling.

| Agent | Primary Skills | Routing Trigger |
|---|---|---|
| `build-engineer` | Build system optimization, compilation time reduction, build parallelization, caching | Build performance optimization, build system scaling |
| `cli-developer` | CLI tool design, cross-platform compatibility, command UX, shell completion | CLI tool and terminal application development |
| `dependency-manager` | Dependency auditing, vulnerability scanning, version conflict resolution, update automation | Dependency audit, vulnerability resolution |
| `documentation-engineer` | API docs, tutorials, guides, documentation site architecture, docs-as-code | Comprehensive documentation system creation |
| `dx-optimizer` | Developer workflow analysis, feedback loop optimization, tooling benchmarking, DX metrics | Developer experience optimization, workflow efficiency |
| `feature-flag-engineer` | Feature flag strategy, targeting rules, lifecycle management, kill switches, flag-debt cleanup | Feature flag system design and lifecycle |
| `git-workflow-manager` | Git branching strategies, merge management, commit conventions, workflow design | Git workflow design, branching strategy |
| `legacy-modernizer` | Legacy migration strategy, incremental modernization, technical debt reduction, risk mitigation | Legacy system modernization, migration planning |
| `mcp-developer` | MCP server/client development, tool definition, resource management, MCP protocol integration | Model Context Protocol server/client development |
| `powershell-module-architect` | PowerShell module design, profile systems, cross-version compatibility, packaging | PowerShell module architecture, reusable library design |
| `powershell-ui-architect` | WinForms/WPF desktop GUIs, PowerShell TUIs, UI/logic separation for PS tools | PowerShell GUI/TUI development |
| `readme-generator` | README authoring from codebase reality, zero-hallucination scanning, maintainer-ready docs | Repository README creation |
| `refactoring-specialist` | Code restructuring, complexity reduction, duplication elimination, behavior-preserving transformation | Code refactoring, clean-up, complexity reduction |
| `slack-expert` | Slack app development, Slack API integration, bot implementation, workflow builder | Slack application and bot development |
| `tooling-engineer` | Developer tool creation, code generators, build tool plugins, IDE extensions | Custom developer tooling, code generators |

---

## Category 07 — Specialized Domains

**Scope:** Vertical industry applications and highly specialized technical domains.

| Agent | Primary Skills | Routing Trigger |
|---|---|---|
| `blockchain-developer` | Smart contract development, DeFi protocols, blockchain architecture, Web3 integration | Blockchain and smart contract development |
| `embedded-systems` | Embedded C/C++, RTOS, hardware interfaces, firmware development, low-level optimization | Embedded system firmware and hardware integration |
| `fintech-engineer` | Financial system architecture, payment flows, regulatory compliance (PCI DSS), core banking | Financial technology system development |
| `game-developer` | Game engine architecture, physics simulation, rendering pipelines, game AI | Game development and engine work |
| `github-projects-manager` | GitHub Projects v2, board configuration, automation rules, project board queries | GitHub Projects board management and automation |
| `healthcare-admin` | Healthcare IT systems, EHR integration, HL7/FHIR, HIPAA technical safeguards | Healthcare system integration, EHR/FHIR work |
| `iot-engineer` | IoT device firmware, MQTT/CoAP protocols, edge computing, sensor data pipelines | IoT device and connectivity engineering |
| `m365-admin` | Microsoft 365 administration, Exchange Online, SharePoint, Teams, Entra ID | Microsoft 365 tenant administration |
| `mobile-app-developer` | Native iOS (Swift/UIKit/SwiftUI) and Android (Kotlin/Jetpack) app development | Native iOS/Android app development |
| `payment-integration` | Payment gateway integration (Stripe/Braintree), PCI DSS compliance, checkout flows | Payment system integration |
| `quant-analyst` | Quantitative financial modeling, algorithmic trading strategies, risk modeling, backtesting | Quantitative finance, algorithmic trading |
| `risk-manager` | Risk framework design, risk register management, mitigation planning, risk reporting | Enterprise risk management |
| `seo-specialist` | Technical SEO, structured data, Core Web Vitals, search performance optimization | SEO strategy and technical optimization |

---

## Category 08 — Business & Product

**Scope:** Business analysis, product management, content strategy, legal/licensing, customer success, and developer relations.

| Agent | Primary Skills | Routing Trigger |
|---|---|---|
| `business-analyst` | Requirements gathering, user stories, process mapping, acceptance criteria, stakeholder analysis | Business requirements, user stories, process improvement |
| `content-marketer` | Content strategy, SEO content, multi-channel campaigns, content ROI measurement | Content strategy and marketing content creation |
| `customer-success-manager` | Customer onboarding, retention strategy, health scoring, escalation management | Customer success program design |
| `developer-advocate` | Developer community, sample apps, tutorials, external documentation, conference content | Developer relations, community building |
| `legal-advisor` | Contract drafting, compliance requirements, IP protection, legal risk assessment | Legal review, contract drafting, regulatory guidance |
| `license-engineer` | OSI license selection, dependency compliance, proprietary licensing, license risk monitoring | Software license management, OSS compliance |
| `product-manager` | Feature prioritization, roadmap decisions, OKR alignment, stakeholder management | Product strategy, roadmap, feature decisions |
| `project-manager` | Project planning, resource management, timeline tracking, stakeholder communication | Project management, delivery coordination |
| `sales-engineer` | Technical sales support, demo design, solution mapping, RFP responses | Technical pre-sales, customer solution design |
| `scrum-master` | Sprint ceremonies, retrospectives, velocity tracking, impediment removal, SAFe facilitation | Sprint planning, agile ceremonies, team coaching |
| `technical-writer` | API documentation, user guides, reference docs, release notes, docs-as-code | Technical documentation authoring |
| `ux-researcher` | Usability analysis, persona development, user journey mapping, research synthesis | UX research, usability testing, persona work |
| `wordpress-master` | WordPress theme/plugin development, Gutenberg blocks, WooCommerce, multisite, performance | WordPress site development and optimization |

---

## Category 09 — Meta Orchestration

**Scope:** Agent coordination, error handling, HITL decision management, knowledge synthesis, and army governance.

| Agent | Primary Skills | Routing Trigger |
|---|---|---|
| `agent-distinctiveness-advocate` | MECE audit, overlap detection, boundary rule validation, roster governance | Pre-merge agent validation, routing ambiguity diagnosis |
| `agent-installer` | Agent installation, configuration, plugin management, agent setup | Installing and configuring agents |
| `agent-organizer` | Agent categorization, roster organization, naming convention enforcement | Agent roster organization and structure |
| `codebase-orchestrator` | Local code-diff approval loops, multi-file change coordination, merge conflict resolution | Local codebase orchestration, complex multi-file changes |
| `context-manager` | Cross-session context persistence, project state management, context retrieval | Context window management, session state persistence |
| `error-coordinator` | Error aggregation, failure pattern analysis, escalation routing, incident coordination | Error escalation endpoint for all agents |
| `hitl-coordinator` | HITL decision artifact creation, GitHub Projects board integration, cross-session decision lifecycle | Human-in-the-loop decisions, strategic judgment calls |
| `it-ops-orchestrator` | IT operations coordination, multi-system change management, operational workflow orchestration | IT operations coordination across systems |
| `knowledge-synthesizer` | Insight capture, anti-pattern documentation, learning loop management, knowledge base updates | Post-task learning capture, knowledge base synthesis |
| `multi-agent-coordinator` | Parallel agent execution, agent output merging, coordination protocol management | Coordinating multiple agents running in parallel |
| `performance-monitor` | Agent performance tracking, latency measurement, throughput analysis, optimization recommendations | Monitoring agent army performance |
| `release-manager` | Cross-repo release coordination, dependency-order tagging, cross-spoke changelog aggregation | Multi-repo release train coordination |
| `task-distributor` | Task decomposition, agent assignment, workload balancing, dependency mapping | Breaking work into parallelizable tasks for multiple agents |
| `workflow-orchestrator` | Complex workflow design, conditional branching, retry logic, pipeline state management | Complex multi-step workflow design |

---

## Category 10 — Research & Analysis

**Scope:** Market research, competitive intelligence, technical spikes, and scientific literature.

| Agent | Primary Skills | Routing Trigger |
|---|---|---|
| `competitive-analyst` | Competitive landscape mapping, feature comparison, positioning analysis, market dynamics | Competitive analysis, market positioning |
| `data-researcher` | Data sourcing, dataset evaluation, research data pipelines, data quality assessment | Research data acquisition and curation |
| `market-researcher` | Market sizing, customer discovery, segment analysis, demand forecasting | Market research, customer discovery |
| `project-idea-validator` | Idea feasibility scoring, market fit assessment, technical risk evaluation, MVP scoping | Project/idea validation, feasibility assessment |
| `research-analyst` | Multi-source research synthesis, evidence evaluation, recommendation generation | General research synthesis, evidence-based analysis |
| `scientific-literature-researcher` | Academic paper review, literature synthesis, citation analysis, research gap identification | Scientific literature review, academic research |
| `search-specialist` | Advanced search strategy, boolean queries, source evaluation, research retrieval optimization | Targeted information retrieval, search strategy |
| `spike-researcher` | Time-boxed PoC development, build-vs-buy recommendation, technology evaluation, runnable spike | Technical spikes, technology evaluation, build-vs-buy |
| `trend-analyst` | Technology trend monitoring, emerging pattern identification, trend impact assessment | Technology trend analysis, emerging pattern identification |

---

## Category 11 — Enterprise Architecture

**Scope:** TOGAF ADM phases, Wardley Mapping, enterprise capability planning, regulatory compliance architecture, and integration architecture.

| Agent | Primary Skills | Routing Trigger |
|---|---|---|
| `business-architect` | TOGAF Phase B, business capability modeling, value stream mapping, operating model design | Business architecture, capability mapping, value streams |
| `capability-planner` | Capability investment scoring, WSJF prioritization, capability roadmaps, PI planning linkage | Capability investment planning, portfolio prioritization |
| `enterprise-architect` | Architecture program management, Architecture Vision (Phase A), Architecture Repository governance, multi-phase ADM coordination | Enterprise-wide architecture programs |
| `information-architect` | Conceptual/logical/physical data models, MDM strategy, data governance, TOGAF Phase C (data) | Information/data architecture, data governance |
| `integration-architect` | API governance strategy, event-driven architecture, canonical data models, ESB modernization | Enterprise integration strategy, API governance |
| `platform-architect` | Internal Developer Platform design, Team Topologies, golden paths, Backstage, DORA metrics | IDP strategy, platform-as-a-product design |
| `security-architect` | Zero Trust architecture (NIST SP 800-207), FedRAMP, CMMC, NIST CSF 2.0, enterprise IAM | Enterprise security architecture, Zero Trust design |
| `solution-architect` | Solution architecture documents, ABB-to-SBB translation, vendor evaluation, transition architecture | Solution-level architecture, vendor selection |
| `togaf-adm-advisor` | TOGAF ADM phase guidance, ADM artifact templates, ADM tailoring, phase deliverables | TOGAF ADM phase execution, artifact production |
| `us-regulatory-architect` | FedRAMP, FISMA/RMF, CMMC 2.0, HIPAA technical safeguards, PCI DSS v4, SOX IT controls | US regulatory compliance architecture |
| `wardley-strategist` | Wardley Mapping, value chain decomposition, evolution axis positioning, climatic pattern analysis, strategic gameplay | Wardley maps, strategic positioning analysis |

---

## Quick Routing Guide

| Concern | Agent |
|---|---|
| REST or GraphQL API design | `api-designer` |
| API implementation (Python) | `python-pro` → `fastapi-developer` |
| API implementation (Node.js) | `node-specialist` |
| API gateway, edge auth, rate limiting | `api-gateway-engineer` |
| Event-driven messaging / brokers | `async-messaging-engineer` |
| Contract testing across services | `contract-test-engineer` |
| React app (existing, optimize) | `react-specialist` |
| React app (greenfield, multi-framework) | `frontend-developer` |
| Mobile app (React Native) | `expo-react-native-expert` |
| Mobile app (Flutter) | `flutter-expert` |
| Mobile app (native iOS/Android) | `mobile-app-developer` |
| CI/CD pipeline, infra automation | `devops-engineer` |
| Release/rollout for one service | `deployment-engineer` |
| Release train across repos | `release-manager` |
| SLOs, error budgets, toil | `sre-engineer` |
| OpenTelemetry, metrics, tracing | `observability-engineer` |
| Cloud cost, rightsizing | `finops-engineer` |
| Security audit | `security-auditor` |
| Pen test | `penetration-tester` |
| Kubernetes | `kubernetes-specialist` |
| Terraform | `terraform-engineer` |
| Database query performance | `database-optimizer` |
| PostgreSQL advanced features | `postgres-pro` |
| DB schema migration | `schema-migration-engineer` |
| Data pipeline / ELT | `data-engineer` or `dlt-engineer` |
| ML model training / serving | `machine-learning-engineer` |
| ML platform / CI-CD | `mlops-engineer` |
| LLM system architecture | `llm-architect` |
| User stories / requirements | `business-analyst` |
| Architecture decisions (ADR) | `architect-reviewer` or `/ea-adr` skill |
| Sprint planning / retrospectives | `scrum-master` |
| HITL decision, human judgment | `hitl-coordinator` |
| Agent governance / MECE audit | `agent-distinctiveness-advocate` |
| Error escalation (from any agent) | `error-coordinator` |
| Knowledge capture (from any agent) | `knowledge-synthesizer` |
| Wardley map | `wardley-strategist` or `/wardley` skill |
| Enterprise architecture program | `enterprise-architect` |
| TOGAF ADM phase guidance | `togaf-adm-advisor` |
| Business capability model | `business-architect` or `/capability-map` skill |
| Technical spike, build-vs-buy | `spike-researcher` |
| Feature flags, progressive delivery | `feature-flag-engineer` |
| Performance bottlenecks | `performance-engineer` |
| Chaos / resilience testing | `chaos-engineer` |

---

## Cross-Cutting Routing Clusters

These clusters show how agents hand off to each other across a lifecycle:

### Contract Cluster
```
api-designer            → design the API contract
contract-test-engineer  → enforce it at runtime/CI across spokes
schema-migration-engineer → evolve the DB schema behind it safely
```

### Delivery/Ops Cluster
```
devops-engineer          → build & operate CI/CD + infra
deployment-engineer      → release/rollout strategy for one service
release-manager          → coordinate release trains across spoke repos
observability-engineer   → produce telemetry
sre-engineer             → consume telemetry for SLOs/error budgets
finops-engineer          → govern cloud cost
api-gateway-engineer     → edge policy
```

### ML Cluster
```
data-scientist           → ML feasibility, experiment design
machine-learning-engineer → training pipelines, model serving
mlops-engineer           → ML platform CI/CD, feature store
observability-engineer   → ML model observability, drift detection
```

### Enterprise Architecture Cluster (TOGAF ADM aligned)
```
enterprise-architect     → Phase A: Architecture Vision
business-architect       → Phase B: Business Architecture
information-architect    → Phase C: Data Architecture
integration-architect    → Phase C: Application Architecture (integration view)
solution-architect       → Phase E/F: Migration Planning
deployment-engineer      → Phase G: Implementation Governance
wardley-strategist       → Strategic context (pre-Phase A)
togaf-adm-advisor        → Any phase: artifact guidance
```

---

## Known Overlaps & Boundary Rules

These agent pairs share concern areas. Each has an explicit boundary rule documented in their descriptions:

| Agent A | Agent B | Boundary |
|---|---|---|
| `debugger` | `error-detective` | `debugger` = single service; `error-detective` = distributed/multi-service correlation |
| `qa-expert` | `test-automator` | `qa-expert` = strategy/planning; `test-automator` = automation implementation |
| `security-auditor` | `penetration-tester` | `security-auditor` = comprehensive audit/compliance; `penetration-tester` = active exploitation |
| `api-designer` | `graphql-architect` | `api-designer` = initial design + REST + simple GraphQL; `graphql-architect` = complex federation/optimization |
| `api-designer` | `async-messaging-engineer` | REST/GraphQL contracts vs async event schemas (Kafka/AsyncAPI) |
| `devops-engineer` | `deployment-engineer` | CI/CD infrastructure vs rollout strategy for a single service |
| `deployment-engineer` | `release-manager` | Single-service rollout vs cross-repo release train coordination |
| `machine-learning-engineer` | `mlops-engineer` | Model training/serving vs ML platform/CI-CD |
| `database-administrator` | `database-optimizer` | Infrastructure provisioning vs query/index performance tuning |
| `postgres-pro` | `database-optimizer` | Advanced PostgreSQL features vs generic multi-RDBMS optimization |
| `frontend-developer` | `react-specialist` | Greenfield/multi-framework vs existing React optimization |
| `hitl-coordinator` | `codebase-orchestrator` | Board-level cross-session decisions vs local code-diff approval loops |
| `platform-architect` (cat 11) | `platform-engineer` (cat 03) | IDP strategy/design vs IDP build/operations |
| `security-architect` (cat 11) | `security-engineer` (cat 03) | Enterprise security architecture design vs infrastructure security implementation |

---

## Validation

Run the audit script to check compliance of the full agent roster against the schema:

```bash
# Summary only (fastest)
node tools/audit-agents.mjs --summary-only

# Full per-agent table
node tools/audit-agents.mjs

# Filter to one category
node tools/audit-agents.mjs --category 01-core-development

# Machine-readable JSON
node tools/audit-agents.mjs --json > audit-results.json
```

**Exit codes:**
- `0` — All agents have required fields (`name`, `description`, `tools`, `model`)
- `1` — One or more agents are missing required fields
- `2` — Schema file not found

**What the audit reports:**
- Missing required fields (FAIL — blocks merge per AGENT_ONBOARDING_RUBRIC.md)
- Invalid model tier or unknown category enum value (FAIL)
- Description convention violations, unknown tools, model-tier/tool-count mismatches (WARN)
- Optional field coverage rates (shows migration progress as agents adopt the full schema)
- Potential MECE overlaps (4+ agents sharing a keyword in their description)
- Coverage gaps (categories with fewer than 3 agents)

**Schema location:** `.claude/agent-schema.json`
**Template location:** `templates/agent-spec-template.md`
**Onboarding rubric:** `planning/meta/decisions/AGENT_ONBOARDING_RUBRIC.md`

> Note: Optional fields (`category`, `primary_skills`, `routing_conditions`, `routing_anti_patterns`, `prerequisites`, `escalates_to`, `known_limits`, `example_prompts`) currently show 0% coverage — migration from simple frontmatter to the full schema is a separate task tracked by RT1-FEAT-001 migration issues.
