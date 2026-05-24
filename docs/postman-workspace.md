# Postman Workspace for Contract-Driven API Work

AgentArmy is a template and coordination hub, not an application API. Use Postman as a companion workspace for designing, mocking, documenting, and validating API contracts owned by spoke repositories.

This works best when a project uses the N-layer Hub & Spoke model:

- Hub: AgentArmy repo, agent routing, GitHub Projects, docs, workflow standards
- Contracts spoke or API spoke: OpenAPI, GraphQL, AsyncAPI, examples, generated mocks
- Consumer spokes: UI, mobile, workers, data jobs, and integration tests that depend on versioned contracts

## Recommended Workspace Shape

Create one Postman workspace per product or program increment, then organize it around contracts rather than implementation teams.

| Postman asset | Purpose | AgentArmy owner lens |
|---|---|---|
| API definition | OpenAPI 3.1 source of truth for REST APIs | `api-designer` |
| Collections | Request suites grouped by user workflow and contract area | `api-documenter`, `test-automator` |
| Mock servers | Stable stubs for UI/mobile/worker spokes | `integration-architect`, `qa-expert` |
| Environments | Local, mock, dev, staging, production endpoint variables | `deployment-engineer`, `security-auditor` |
| Monitors | Scheduled smoke checks for deployed APIs | `sre-engineer`, `qa-expert` |
| Examples | Canonical success/error payloads for docs and tests | `technical-writer`, `api-documenter` |

## Naming Conventions

Use predictable names so agents can reason about the workspace from exported files.

```text
Workspace: <Product> API Contracts
API: <Product> REST API v1
Collection: <Domain> - <Workflow>
Environment: <product>-local
Environment: <product>-mock
Environment: <product>-dev
Environment: <product>-staging
Environment: <product>-prod
Mock: <product>-api-v1-mock
Monitor: <product>-api-v1-smoke
```

## Lifecycle Alignment

Postman environments should mirror the platform workload lifecycle:

| Environment | Lifecycle meaning |
|---|---|
| `<product>-local` | Local runner, local API, local Docker, or local dev server target. |
| `<product>-mock` | Contract/mock target for examples and consumer-spoke development. |
| `<product>-dev` | Shared platform-development runtime where built containers first run as services. |
| `<product>-staging` | Production-like validation runtime. |
| `<product>-prod` | Production runtime. |

For the AgentArmy platform examples, use:

```text
agentarmy-local
agentarmy-mock
agentarmy-dev
agentarmy-staging
agentarmy-prod
```

`mock` is intentionally separate from runtime promotion. It supports contract-first development and UI/mobile/worker consumers while the real runtime moves through `local -> dev -> staging -> prod`.

AgentArmy template development is simpler: local validation and then merge to `main`. Postman examples in this repo model platform APIs; they do not make AgentArmy itself an application API or workload container.

Collections should be workflow-oriented, not just CRUD folders. For example:

- `Identity - Sign in and session`
- `Users - Profile lifecycle`
- `Admin - Tenant management`
- `Integration - Webhook delivery`
- `Health - Readiness and diagnostics`

## Environment Variables

Keep secrets out of exported collections and committed docs. Store placeholder variables in Postman and use secret/current values locally.

| Variable | Scope | Notes |
|---|---|---|
| `base_url` | environment | API endpoint for local/mock/dev/staging/prod |
| `api_version` | environment | Example: `v1` |
| `access_token` | secret/current value | Never commit exported real tokens |
| `tenant_id` | environment | Use fake values in shared examples |
| `correlation_id` | collection or request | Useful for logs and support workflows |
| `admin_user_id` | environment | Fake or seeded test identity only |

## Postman AI Prompt

Paste this into Postman AI when creating the workspace. Replace bracketed values first.

```text
You are helping set up a Postman workspace for an AgentArmy-managed project.

Context:
- AgentArmy is a template and coordination hub, not the app API itself.
- The product uses contract-driven development across spoke repos.
- API contracts are the source of truth for UI, mobile, worker, data, and integration spokes.
- Collections must help agents and humans design, mock, test, and document the API.

Create a Postman workspace structure for:
- Product name: [PRODUCT_NAME]
- API name: [API_NAME]
- API style: REST with OpenAPI 3.1
- Version: v1
- Main domains: [DOMAIN_1], [DOMAIN_2], [DOMAIN_3]
- Auth pattern: [AUTH_PATTERN]
- Environments: local, mock, dev, staging, prod

Please create:
1. An API definition scaffold with OpenAPI 3.1 conventions.
2. Workflow-oriented collections, not only CRUD folders.
3. Example requests and responses for success, validation error, authorization error, not found, conflict, and server error cases.
4. Collection-level tests that check status codes, response shape, error envelope, correlation IDs, and basic latency.
5. Environment variables for base_url, api_version, access_token, tenant_id, correlation_id, and any domain-specific IDs.
6. A mock server plan with realistic sample data that UI and mobile spokes can use before the API is implemented.
7. A monitor plan for health, auth, and one critical user workflow.
8. Documentation notes that explain each workflow in business language.

Use these conventions:
- Do not put real secrets in examples.
- Use fake IDs and clearly fake tokens.
- Use plural nouns for REST resources.
- Include request examples for idempotency where needed.
- Include pagination, filtering, and sorting examples where list endpoints exist.
- Include standard headers: Authorization, Content-Type, Accept, X-Correlation-ID.
- Use a consistent error envelope:
  {
    "error": {
      "code": "string",
      "message": "string",
      "details": [],
      "correlationId": "string"
    }
  }

Output the assets in a way that can later be exported and committed into a contracts or API spoke repo under:
- postman/collections/
- postman/environments/
- openapi/
- docs/api/
```

## AgentArmy Routing

Use this pod when Postman work is more than a tiny setup task:

| Role | Agent lens | Deliverable |
|---|---|---|
| Contract owner | `api-designer` | OpenAPI resource model, status codes, auth shape |
| Integration reviewer | `integration-architect` | Cross-spoke boundaries, event/webhook implications |
| Test owner | `test-automator` | Postman test scripts and monitor coverage |
| Security reviewer | `security-auditor` | Token handling, auth flows, secret hygiene |
| Docs owner | `api-documenter` or `technical-writer` | Examples and developer-facing workflow docs |

For REST API changes, create a GitHub issue and label it based on scope:

- `copilot-task`: bounded collection/test cleanup, typo fixes, one endpoint example
- `agent-army-task`: new API area, multi-workflow collection, auth model, mock server, monitor suite, OpenAPI contract change

## What to Commit Back to Repos

Postman is useful, but Git remains the durable source of truth. Export and commit only sanitized artifacts.

Recommended layout for an API or contracts spoke:

```text
openapi/
  api-v1.yaml
postman/
  collections/
    product-api-v1.postman_collection.json
  environments/
    product-local.postman_environment.json
    product-mock.postman_environment.json
    product-dev.postman_environment.json
docs/
  api/
    workflow-examples.md
```

Do not commit:

- real access tokens
- personal workspace IDs
- production credentials
- private customer data
- generated examples that contain sensitive values

## Definition of Done

A Postman API workspace task is done when:

- OpenAPI or API definition exists for the intended contract surface.
- Collections cover critical happy paths and error cases.
- Environments are present with sanitized placeholder values.
- Mock server examples unblock consumer spokes.
- Tests assert status, schema shape, error envelope, and correlation ID behavior.
- Any exported artifacts are committed only after secret review.
- The GitHub issue or PR body links the work with `Closes #ISSUE_NUMBER`.
