# Routing Matrix

Complete decision tree for delegating work to the right army and agent.

## Quick Filters

### By Effort Size

| Size | Turnaround | Use | Armies |
|------|-----------|-----|--------|
| **XS** (≤0.5 day) | Minutes | `copilot-task` label | Copilot |
| **S** (≤1 day) | 1-4 hours | `copilot-task` label (if clear) or Claude Code | Copilot / Claude |
| **M** (≤3 days) | 4-24 hours | Claude Code specialist | Claude Code |
| **L** (≤1 week) | 1-3 days | Claude Code specialist + architecture review | Claude Code |
| **XL** (>1 week) | 3+ days | Epic break-down required | Claude Code + Planning |

### By Issue Type

| Type | Owner | Process |
|------|-------|---------|
| **Epic** | Claude Code | Architect breaks into Stories |
| **Feature** | Claude Code | Assign specialist, estimate sub-issues |
| **Story** | Copilot or Claude | 1-sprint deliverable with clear acceptance criteria |
| **Enabler** | Claude Code | Infrastructure, exploration, tooling |
| **Bug** | Copilot or Claude | Size determines routing |
| **Spike** | Claude Code | Time-boxed research, max 3 days (`spike-researcher` for PoC code + build-vs-buy) |

### By Domain

#### Backend & Microservices
```
API Design              → api-designer
REST/GraphQL APIs       → backend-developer
FastAPI                 → fastapi-developer
Django                  → django-developer
Spring Boot             → spring-boot-engineer
.NET Core               → dotnet-core-expert
Node.js                 → node-specialist
Go/Rust                 → golang-pro / rust-engineer
Microservices           → microservices-architect
Event-Driven Messaging  → async-messaging-engineer
Message Brokers (Kafka/RabbitMQ/SQS-SNS/NATS) → async-messaging-engineer
```

#### Frontend
```
React (optimize)        → react-specialist
React (greenfield)      → frontend-developer
Vue 3                   → vue-expert
Next.js                 → nextjs-developer
Mobile Web              → mobile-web-specialist
Responsive Design       → mobile-web-specialist
Angular                 → angular-architect
```

#### Mobile
```
React Native            → expo-react-native-expert
Flutter                 → flutter-expert
iOS/Android Native      → mobile-app-developer
```

#### Data & Analytics
```
ETL/ELT Pipelines       → dlt-engineer
Data Warehousing        → data-engineer
Analytics               → data-analyst / data-scientist
ML Model Development    → machine-learning-engineer
ML Production Serving   → mlops-engineer
Schema Migration (Flyway/Liquibase/Alembic) → schema-migration-engineer
Zero-Downtime Schema Evolution → schema-migration-engineer
```

#### Infrastructure & DevOps
```
Kubernetes              → kubernetes-specialist
Docker                  → docker-expert
CI/CD Pipelines         → deployment-engineer
Terraform/IaC           → terraform-engineer
AWS/Azure/GCP           → cloud-architect
Monitoring/Observability → sre-engineer
Telemetry Instrumentation (OpenTelemetry, dashboards) → observability-engineer
Cloud Cost / FinOps     → finops-engineer
API Gateway (rate limiting, edge auth, routing) → api-gateway-engineer
Feature Flags / Progressive Delivery → feature-flag-engineer
Cross-Spoke Release Trains → release-manager
```

#### Enterprise Architecture
```
Strategy & Capability   → business-architect / wardley-strategist
Technology Architecture → architect-reviewer / solution-architect
Security Architecture   → security-architect
Compliance (FISMA/FedRAMP) → us-regulatory-architect
```

#### Special Tasks
```
Security Audit          → security-auditor
Code Review (deep)      → /review-pr skill
Performance Bottleneck  → performance-engineer
Database Optimization   → database-optimizer / postgres-pro
Git Workflow            → git-workflow-manager
Contract Testing (Pact, schema drift) → contract-test-engineer
Technical Spike / PoC   → spike-researcher
Developer Relations / Adoption → developer-advocate
```

---

## Decision Tree

### Step 1: Is it a bug fix or simple feature?
```
YES → Is it XS or S size with clear acceptance criteria?
      YES → Label with 'copilot-task' → Copilot Coding Agent
      NO  → Continue to Step 2

NO → Continue to Step 2
```

### Step 2: What's the primary domain?
```
→ Backend/API        → See Backend routing (above)
→ Frontend           → See Frontend routing (above)
→ Mobile             → See Mobile routing (above)
→ Data/Analytics     → dlt-engineer or data-engineer
→ DevOps/Infra       → deployment-engineer or devops-engineer
→ Architecture       → architect-reviewer or enterprise-architect
→ Security           → security-auditor or security-engineer
```

### Step 3: Language/Framework Specialist?
```
YES → Language Routing Guide → See language-routing.md
NO  → Use domain specialist above
```

---

## Issue Template Fields

Every issue must have these fields set **before** delegating:

| Field | Options | When to Set |
|-------|---------|------------|
| **Type** | Epic, Feature, Story, Enabler, Bug, Spike, Decision | At creation |
| **PI** | PI-1, PI-2, etc. | At creation |
| **Size** | XS, S, M, L, XL | At creation |
| **Estimate** | Story points (1,2,3,5,8,13) | During planning |
| **Priority** | P0, P1, P2 | At creation or during grooming |
| **Status** | Todo→Ready→In Progress→In Review→Done (+ Awaiting Decision for HITL) | Auto-managed, don't override |

---

## Escalation & Cross-Army Work

### When to involve multiple agents
```
Large refactor                 → Claude Code specialist + performance-engineer
New API + Frontend             → backend-developer + frontend-developer
Data pipeline + ML             → dlt-engineer + data-scientist
Infrastructure + Security     → devops-engineer + security-engineer
```

### When to escalate
```
Ambiguous requirements         → business-analyst (story refinement)
Architectural decision         → architect-reviewer
Performance bottleneck         → performance-engineer (root cause analysis)
Security concern              → security-auditor
```

---

## PR Conventions

Every PR must:
1. **Link to issue**: `Closes #N` / `Fixes #N` / `Resolves #N`
2. **Be reviewable**: Size < 400 LOC (large PRs auto-labeled `needs-deep-review`)
3. **Have tests**: For features/bug fixes
4. **Pass CI**: Green checks required for merge

Copilot auto-reviews all PRs. Flag large PRs with `needs-deep-review` for `/review-pr` skill.

---

## Learn More

- **[Languages Routing](language-routing.md)** — Python, Go, Rust, Java, TypeScript, etc.
- **[Agent Roster](agents.md)** — Full roster of specialist definitions
- **[Specialist Guide](language-routing.md)** — Deep dive into language specialists
