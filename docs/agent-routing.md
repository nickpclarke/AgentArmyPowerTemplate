# Agent Routing Reference

This is the **full** routing table — matching tasks to their dedicated specialist agent.

## Copilot army — label-driven

Apply the label and let automation handle it:

| Trigger | Label | Copilot does |
|---|---|---|
| Bug or Story, Size XS/S | `copilot-task` | Creates branch, implements, opens PR |
| Any PR | (automatic) | Inline first-pass review |
| Board query | `@board-manager` | Queries board, returns status |

## Claude Code army — delegate by concern

| Concern | Agent |
|---|---|
| Requirements / user stories | `business-analyst` |
| Architecture decisions | `architect-reviewer` |
| Sprint / PI planning | `scrum-master` |
| Frontend implementation | `frontend-developer` (greenfield), `react-specialist` (existing React optimization) |
| Frontend: Language-level | `javascript-pro`, `typescript-pro` |
| Frontend: Mobile/responsive | `mobile-web-specialist`, `mobile-developer` (cross-platform) |
| Backend implementation | `backend-developer` |
| Backend: Language-level | `python-pro`, `golang-pro`, `rust-engineer`, `java-architect` |
| Deep code review | `/review-pr` skill |
| Security audit | `security-auditor` or `/security-review` skill |
| Agent hits decision point | `hitl-coordinator` |
| Agent governance / MECE validation | `agent-distinctiveness-advocate` |
| GCP infrastructure | `gcp-infra-engineer` |
| AWS infrastructure | `aws-infra-engineer` |
| Azure infrastructure | `azure-infra-engineer` |
| Vercel platform | `vercel-engineer` |
| Multi-cloud strategy | `cloud-architect` |
| CI/CD system & infra automation | `devops-engineer` |
| Release & rollout strategy | `deployment-engineer` |
| Cross-spoke release trains | `release-manager` |
| Reliability & SLOs | `sre-engineer` |
| Telemetry & instrumentation | `observability-engineer` |
| Cloud cost / FinOps | `finops-engineer` |
| API gateway & edge policy | `api-gateway-engineer` |
| Performance optimization | `performance-engineer` |
| Feature flags | `feature-flag-engineer` |
| Event-driven messaging | `async-messaging-engineer` |
| Contract testing across spokes | `contract-test-engineer` |
| DB schema migrations | `schema-migration-engineer` |
| Data pipeline work (dlt, ELT) | `dlt-engineer` |
| Data analysis & modeling | `data-analyst`, `data-scientist`, `data-engineer` |
| Data Vault 2.1 strategy | `data-vault-architect` |
| Data Vault 2.1 logical model | `data-vault-modeler` |
| Data Vault 2.1 build & load | `data-vault-engineer` |
| Production ML lifecycle | `machine-learning-engineer`, `mlops-engineer` |
| UFO/OntoUML conceptual modeling | `ontologist-ufo` |
| BFO 2020 foundational ontology | `ontologist-bfo` |
| Applied OWL/RDFS/SHACL modeling | `ontologist-generalist` |
| Knowledge graph reasoning | `knowledge-engineer` |
| Taxonomies & controlled vocabularies | `taxonomist` |
| Technical spike / build-vs-buy | `spike-researcher` |
| Developer adoption / DevRel | `developer-advocate` |

## Cross-cutting routing clusters

Pick by lifecycle stage, not by keyword overlap:

- **Contract cluster:** `api-designer` (design the contract) → `contract-test-engineer` (enforce it in CI) → `schema-migration-engineer` (evolve the DB behind it safely).
- **Delivery/ops cluster:** `devops-engineer` (build & operate CI/CD) → `deployment-engineer` (release/rollout strategy) → `release-manager` (coordinate release trains across spoke repos) → `observability-engineer` (produce telemetry) → `sre-engineer` (consume it for SLOs/error budgets) → `finops-engineer` (govern cost) → `api-gateway-engineer` (edge policy).
- **Knowledge/ontology cluster** (formality gradient): `taxonomist` (SKOS/taxonomies, no axioms) → `ontologist-generalist` (applied OWL/SHACL) → `ontologist-ufo` / `ontologist-bfo` (foundational: UFO-design vs BFO-realist) → `knowledge-engineer` (populate, reason, query).
- **Data Vault cluster** (lifecycle): `data-vault-architect` (raw vs business placement) → `data-vault-modeler` (hubs / links / sats / refs) → `data-vault-engineer` (Datavault4dbt loaders, PIT/bridge, marts). Sits *downstream* of the canonical data model contract, *upstream* of marts.
