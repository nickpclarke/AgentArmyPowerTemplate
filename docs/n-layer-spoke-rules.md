# N-Layer Spoke Rules

These rules operationalize the [N-Layer Hub & Spoke Architecture](n-layer-architecture.md). They are for teams using AgentArmy as the hub template while building separate repositories for the meaningful containers and subsystems in an N-layer stack.

The approach is a good fit when each spoke has clear ownership, independent runtime needs, and contract boundaries. It is not a reason to create one repository per tiny class, component, or helper.

## Why This Is A Best-Practice Fit

The model aligns with established architecture and operations guidance:

- Microservices are independently deployable services built around business capabilities, communicating through lightweight mechanisms, with minimal centralized management ([Martin Fowler](https://martinfowler.com/articles/microservices.html)).
- Service data should be private to the service and accessed through APIs; private tables, private schemas, or a database server per service are all valid isolation levels depending on scale and operational cost ([microservices.io](https://microservices.io/patterns/data/database-per-service)).
- Runtime config and secrets should be separated from code and supplied through environment/config channels, not committed constants ([Twelve-Factor Config](https://www.12factor.net/config)).
- Python virtual environments are the standard built-in mechanism for per-project Python isolation ([Python venv](https://docs.python.org/3/library/venv.html)).
- Dev containers provide repeatable per-repository development environments for local, cloud, and CI workflows ([Dev Containers spec](https://github.com/devcontainers/spec), [GitHub Codespaces](https://docs.github.com/en/codespaces/setting-up-your-project-for-codespaces/adding-a-dev-container-configuration/introduction-to-dev-containers)).
- Docker Compose supports project-local `.env` files and ordered `--env-file` overrides for environment-specific runtime configuration ([Docker Compose env docs](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/)).
- Reusable GitHub Actions workflows are the right way for a hub repo to provide CI/CD patterns to spoke repos without copying entire workflow implementations ([GitHub reusable workflows](https://docs.github.com/actions/reference/workflows-and-actions/reusable-workflows)).

## Hub And Spoke Ownership

AgentArmy is the hub. It owns reusable standards and patterns:

- agent taxonomy and generated agent definitions
- repository operating rules
- workflow templates and reusable workflows
- diagnostics standards and the doctor CLI
- setup, onboarding, and scaffolding guidance
- example manifests and spoke templates

Spoke repositories own their layer implementation:

- service source code
- runtime dependencies and lockfiles
- layer-specific CI callers
- service-specific Dockerfiles and compose files
- local `.env.example` files
- contracts they publish or consume
- `.agent/layer.json` identity manifests

Do not copy personal provider settings, plugin installs, local permissions, machine paths, or secret-bearing config from the hub into spokes.

## Layer Identity Manifest

Every spoke must commit:

```text
.agent/layer.json
```

The manifest identifies what the repo is, which layer it belongs to, and what it must not own.

Minimum shape:

```json
{
  "schema_version": "agentarmy.layer.v1",
  "system": "career-platform",
  "layer": "api",
  "service": "career-api",
  "repo_role": "spoke",
  "runtime_kind": "container",
  "contracts": ["career-contracts@0.3.0"],
  "owns": ["REST API", "domain services", "API database schema"],
  "does_not_own": ["web UI", "mobile app", "infra state", "personal agent settings"]
}
```

Allowed `repo_role` values:

| Value | Meaning |
|---|---|
| `hub` | Template/control-plane repository such as AgentArmy. |
| `spoke` | One meaningful layer or subsystem repo. |
| `contracts` | Dedicated contract source-of-truth repo. |

Recommended `layer` values:

| Layer | Typical ownership |
|---|---|
| `web-ui` | Browser UI, static assets, UI tests, frontend build. |
| `api` | REST/GraphQL API, domain services, API-owned persistence. |
| `worker` | Async jobs, event consumers, batch processors. |
| `data` | Data pipelines, analytics transforms, data contracts. |
| `ml-ai` | Model serving, evals, prompt/model assets, vector workflows. |
| `mobile` | Mobile app shells and platform-specific mobile code. |
| `infra` | IaC, environment provisioning, deploy orchestration. |
| `contracts` | OpenAPI, GraphQL SDL, AsyncAPI, JSON Schema, protobuf, shared type packages. |

Recommended `runtime_kind` values:

| Runtime | Meaning |
|---|---|
| `static` | Static docs/site/frontend with no server runtime. |
| `serverless` | Function or edge runtime. |
| `container` | Long-lived or request-driven container service. |
| `worker` | Background or scheduled compute. |
| `mobile` | Mobile app build/runtime. |
| `iac` | Infrastructure-only repository. |
| `library` | Package or shared contract/type library. |

## Runtime Isolation Rules

Each spoke gets its own runtime environment. Do not share mutable runtime folders across spokes.

| Runtime asset | Rule |
|---|---|
| Python | Use a spoke-local `.venv/`; commit `pyproject.toml`, lockfile, or requirements files. |
| Node | Use spoke-local `node_modules/`; commit the package manager lockfile. |
| Containers | Keep service Dockerfiles and compose files in the spoke; use project-local env files. |
| Dev containers | Commit `.devcontainer/devcontainer.json` when a reproducible dev runtime is useful. |
| Local config | Commit `.env.example`; ignore `.env`, `.env.local`, and secret-bearing overrides. |
| Build outputs | Keep build/cache/artifact output out of source control unless intentionally curated. |

Each container spoke should use a unique Compose project name for local CI and developer smoke tests. Do not reuse one mutable compose project across layers.

```text
COMPOSE_PROJECT_NAME=<system>-<service>-local-<run_id>
```

Agents working in parallel should use separate checkouts or worktrees. A spoke agent should not edit another spoke's repo unless the active task explicitly assigns cross-repo integration work.

## Agent Settings Rules

Commit shared agent standards:

- `AGENTS.md`
- `CLAUDE.md` when used as shared routing context
- `.claude/agents/categories/`
- generated `.codex/agents/` files when the spoke intentionally tracks generated agents
- safe `.codex/config.toml` defaults with no secrets
- hook definitions that call repo-local scripts

Keep personal or machine-specific settings local:

- `.codex/config.local.toml`
- `.claude/settings.local.json`
- provider API keys
- plugin installation state
- user-level model/provider choices
- machine-specific absolute paths
- local MCP tokens and bearer tokens

If a spoke needs AgentArmy's agent taxonomy, sync or regenerate it from the hub source instead of copying a personal tool setup.

## Contract Boundary Rules

Spokes integrate through published contracts, not private source imports or direct database reads.

Allowed contract surfaces:

- OpenAPI for REST
- GraphQL SDL for GraphQL
- AsyncAPI for messages and events
- JSON Schema for payloads
- protobuf for binary or strongly typed interfaces
- versioned shared type packages

Rules:

- A UI spoke must not import API implementation files.
- A worker spoke must not read API-owned tables directly.
- An API spoke must not depend on UI source or mobile source.
- A breaking integration change must be a contract change with review and versioning.
- Each spoke should pin to a contract version, tag, or package version rather than "whatever is on main."

## Database Boundary Rules

Prefer the lightest isolation level that enforces service ownership:

| Level | When to use |
|---|---|
| Private tables per service | Early systems sharing one database where ownership can still be enforced. |
| Private schema per service | Default for many relational systems; clearer ownership without extra server overhead. |
| Database server per service | Use when scaling, compliance, tenancy, blast radius, or workload differences justify it. |

Every service should use credentials scoped to its own data boundary. Other services should call its API or consume its events instead of bypassing it with database access.

## Coordination Rules

A single GitHub Projects board can coordinate all spokes, but each work item must make layer identity visible.

Recommended labels:

```text
layer:web-ui
layer:api
layer:worker
layer:data
layer:infra
service:career-api
contract:career-contracts
```

Recommended issue or PR body fields:

```text
Layer:
Service:
Contracts:
Runtime:
Impacted spokes:
```

Cross-spoke work should name one integration owner. Reviewers may advise across layers, but only the owning spoke edits its implementation unless the work item explicitly says otherwise.

## Diagnostics Rules

Each spoke should also declare service diagnostics through `agentarmy.services.json` or `.agent/services.json` when it has runnable services.

The AgentArmy doctor CLI should eventually read `.agent/layer.json` and include `system`, `layer`, `service`, and `runtime_kind` in `doctor.v1` output. Until then, the manifest is the human and agent source of truth for layer identity.

Container spokes may copy the optional local Docker smoke workflow from `templates/local-docker-ci/`. That workflow should stay manual-only, run on a trusted `docker-local` self-hosted runner, and publish doctor artifacts plus container logs for handoff.

## What Not To Do

- Do not split a cohesive bounded context into many repos only because containers are available.
- Do not share one mutable `.venv`, `node_modules`, `.env`, or compose project across spokes.
- Do not commit personal agent permissions, plugin state, provider keys, or machine paths.
- Do not let one spoke depend on another spoke's private source or database.
- Do not let a GitHub board item omit its layer and service when it affects a spoke.
- Do not duplicate hub workflow logic into every spoke when a reusable workflow or template caller will work.
