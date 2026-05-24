# N-Layer Hub & Spoke Architecture (Contract-Driven)

AgentArmy adopts a universal **N-layer Hub & Spoke** architecture so teams can build multiple layers **in parallel** without a monorepo.

- **Hub**: this repository template (AgentArmy) — it defines the workflows, agent roster, and GitHub Projects coordination model.
- **Spokes**: one repository **per layer** (UI, API, worker, mobile app, infra, etc.) created by stamping out this template.
- **Contracts**: the only shared “integration surface” between spokes — OpenAPI/GraphQL/AsyncAPI schemas and/or shared type libraries.

This model is designed for **Contract-Driven Development (API-first)** and **runtime isolation** (MicroVM-compatible), so each spoke can run an independent AI session without cross-contamination.

For the operational rules that keep these spokes safe in daily work, see [N-Layer Spoke Rules](n-layer-spoke-rules.md). That companion standard defines layer manifests, virtual/dev environment boundaries, agent settings rules, and cross-spoke coordination expectations.

---

## The N-Layer Spoke Model

Instead of putting all layers into one monorepo, create a new repository from AgentArmy for each layer you want to build:

- `myapp-ui` (Web UI)
- `myapp-api` (REST/GraphQL API)
- `myapp-worker` (async worker / event consumer)
- `myapp-mobile` (mobile app)
- `myapp-infra` (IaC, environments, pipelines)

Each spoke:

- owns its own codebase and CI
- runs its own AI session in an isolated sandbox
- integrates with other spokes only through **published contracts**

You can add more spokes at any time (N is unbounded): e.g. `myapp-ml`, `myapp-analytics`, `myapp-admin`, `myapp-edge`, etc.

---

## MicroVM / Runtime Isolation

Because each layer is a separate repo, each spoke runs AI agents in a **completely isolated filesystem + runtime**:

- No shared working directory, caches, or build outputs between spokes
- No “accidental context bleed” where an agent invents dependencies based on a different layer’s code
- Clear boundaries: agents can only see *what’s in their spoke repo* plus whatever is explicitly provided via contracts

This improves parallelism and correctness:

- Parallel sessions can confidently move fast without stepping on each other.
- Integration surprises are pushed into **contract negotiation**, where they belong.

---

## Contract-First Synchronization (API-First)

Spokes stay decoupled by treating contracts as the source of truth:

- **OpenAPI** for REST
- **GraphQL SDL** for GraphQL
- **AsyncAPI** for event/message interfaces
- **Shared type libraries** for compile-time contracts (e.g. TypeScript types, protobufs, JSON Schema)

### Recommended contract layout

Pick one of these patterns (both work):

1. **Dedicated “contracts spoke” repo** (recommended for multi-team parallelism)
   - Example: `myapp-contracts`
   - Contains `openapi/`, `graphql/`, `asyncapi/`, `types/`
   - Publishes versioned artifacts (tags, releases, packages)
2. **Contracts live in the API spoke**
   - Works well early on, but can bottleneck when multiple spokes need to negotiate changes simultaneously

### Synchronization rules (what keeps this MECE)

- **No spoke implements against “tribal knowledge”** of another spoke.
- Every breaking integration change becomes a **contract change** (with review and versioning).
- Each spoke depends on **a specific contract version** (e.g. a tag or package version), not “whatever is on main”.

---

## Stubbed Integration (Parallel Execution)

To keep spokes moving in parallel, each spoke builds against stubs instead of waiting for other spokes to ship.

Typical patterns:

- UI spoke runs against a **mock API server** generated from OpenAPI/GraphQL schema.
- Worker spoke runs against a **stub broker** (or a recorded event stream) derived from AsyncAPI.
- API spoke runs with **fake downstreams** (mock payment provider, fake identity provider) behind environment flags.

### “Integrate late” via environment variables

Spokes should treat concrete endpoints as deploy-time configuration:

- UI: `API_BASE_URL`
- Worker: `BROKER_URL`, `TOPIC_PREFIX`
- API: `DOWNSTREAM_*_BASE_URL`

During parallel development:

- point those variables at local mocks/stubs

At integration time (end-to-end environments):

- point those variables at real deployed spoke endpoints

This keeps physical integration as a **final step**, while contracts are integrated continuously.

---

## Agent Roster for Contract-Driven N-Layer Delivery

This workflow uses existing AgentArmy agents so routing stays clear and MECE-compliant.

### Phase 1: Contract design (single source of truth)

| Agent | Primary output |
|---|---|
| `business-analyst` | Use cases, acceptance criteria, domain language |
| `api-designer` | OpenAPI/GraphQL schema drafts, versioning guidance |
| `integration-architect` | AsyncAPI/events, integration patterns, EDA boundaries |
| `typescript-pro` | Shared type library shape (if using shared types) |
| `architect-reviewer` | Cross-layer architecture review, contract boundaries, ADR-level decisions |
| `agent-distinctiveness-advocate` | Validates any new/modified agent roles to avoid routing overlaps |

### Phase 2: Parallel execution (one spoke per layer)

Run the relevant domain agent(s) *inside each spoke repo*:

| Spoke layer | Agents |
|---|---|
| Web UI | `frontend-developer`, `react-specialist`, `mobile-web-specialist` |
| API | `backend-developer` + language specialist (`python-pro`, `node-specialist`, `golang-pro`, etc.) |
| Async worker | `backend-developer`, `integration-architect` |
| Mobile | `mobile-developer`, `expo-react-native-expert`, `flutter-expert`, `swift-expert` |
| Data | `data-engineer`, `dlt-engineer`, `sql-pro` |
| Infrastructure | `devops-engineer`, `terraform-engineer`, `kubernetes-specialist`, `cloud-architect` |

### Phase 3: Integration and hardening (end-to-end)

| Agent | Primary output |
|---|---|
| `qa-expert` | End-to-end test strategy, integration test plan |
| `test-automator` | CI test automation integration across spokes |
| `sre-engineer` | SLOs, runbooks, reliability requirements |
| `deployment-engineer` | Release orchestration, rollout/rollback strategy |
| `security-auditor` | Cross-spoke threat review against real integration points |

---

## How GitHub Projects Coordinates N Spokes

Use a **single GitHub Projects v2 board** as the shared coordination plane across all spokes:

- Every spoke repo routes issues using the same SAFE conventions (Type/PI/Iteration).
- The board can contain items from multiple repos, so one view shows end-to-end progress.
- Each spoke’s CI and automation can update the same board (requires `PROJECT_TOKEN` configured per repo).

See [docs/github-projects.md](github-projects.md) for field definitions and automation conventions.

