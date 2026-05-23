# Agent Spec Template

Use this file as the canonical template when creating a new agent definition. Copy the frontmatter block, fill in the fields, and replace the prompt body below the `---` separator.

Fields marked **required** must be present. Fields marked *optional* may be omitted; the audit tooling will flag required-field violations but will not fail on missing optional fields.

---

## Frontmatter Schema Reference

```yaml
---
# ── REQUIRED ──────────────────────────────────────────────────────────────────

name: <agent-slug>
# Kebab-case identifier. Must be unique across all agents.
# Convention: <role>-<specialty> or <domain>-<function>
# Examples: api-designer, python-pro, hitl-coordinator

description: "Use this agent when …"
# Single-sentence trigger condition starting with "Use this agent when" or
# "Use when". This is what Claude Code matches against to auto-route.
# Must be unique — no two agents should have meaningfully identical descriptions.

tools: Read, Write, Edit, Bash, Glob, Grep
# Comma-separated list of approved tools. Only request what the agent needs.
# Known tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch, computer-use
# Infra/DevOps agents may include Bash; web research agents may include WebFetch/WebSearch.

model: sonnet
# One of: sonnet | opus | haiku
# sonnet  → implementation, design, multi-step problem-solving (default)
# opus    → complex reasoning: architecture, security, strategy, cross-service orchestration
# haiku   → lightweight tasks, simple routing, fast responses

# ── OPTIONAL (but recommended) ────────────────────────────────────────────────

category: "01-core-development"
# The category directory this agent belongs to. One of:
#   01-core-development | 02-language-specialists | 03-infrastructure
#   04-quality-security | 05-data-ai | 06-developer-experience
#   07-specialized-domains | 08-business-product | 09-meta-orchestration
#   10-research-analysis | 11-enterprise-architecture

primary_skills:
  - "REST and GraphQL API design"
  - "OpenAPI 3.1 specification authoring"
  - "API versioning strategy"
  - "Authentication pattern selection"
  - "Developer experience optimization"
# 3–5 concise capability labels. Used by the capability matrix and audit tooling
# to detect MECE gaps and overlaps.

routing_conditions:
  - "Designing a new REST or GraphQL API from scratch"
  - "Authoring or updating an OpenAPI specification"
  - "Defining API versioning or deprecation strategy"
  - "Selecting authentication patterns (OAuth 2.0, JWT, API keys)"
  - "Reviewing API contracts for consistency before implementation"
# Human-readable list of specific triggers. More granular than `description`.
# Each item should be a concrete task or concern type, not a vague keyword.

routing_anti_patterns:
  - "Implementing API handlers — use backend-developer or the relevant language specialist"
  - "GraphQL schema optimization in an existing schema — use graphql-architect"
  - "API gateway policy (rate limiting, edge auth) — use api-gateway-engineer"
  - "Async event schema governance (Kafka/RabbitMQ) — use async-messaging-engineer"
# Explicit list of what this agent does NOT handle.
# Each item should name the alternative agent to route to.

prerequisites:
  - "Business domain model or data entity list (from business-analyst or product-manager)"
  - "Client use-case list or user stories (from business-analyst)"
# Agents or context that should be available before invoking this agent.
# Use agent names when a prior agent output is expected.

escalates_to:
  - "error-coordinator — on tool failure or unrecoverable error"
  - "hitl-coordinator — when design requires a strategic call (e.g., breaking change acceptance)"
  - "knowledge-synthesizer — after completing a complex design (feeds patterns learned)"
# Agent(s) this agent escalates to. Required fields per ARMY_PRINCIPLES.md:
#   - error-coordinator: always present unless agent IS error-coordinator
#   - hitl-coordinator: when human judgment is needed
#   - knowledge-synthesizer: when learning should be captured

known_limits:
  - "Cannot implement code — produces design artifacts (specs, schemas) only"
  - "Does not verify runtime performance — use performance-engineer for load-testing strategies"
  - "Limited GraphQL federation expertise — delegate complex federation to graphql-architect"
# Explicit failure modes and capability boundaries. Honest and specific.
# These are surfaced in the capability matrix and help users pick the right agent.

example_prompts:
  - "Design a REST API for an e-commerce order management system with pagination, filtering, and webhooks"
  - "Write an OpenAPI 3.1 spec for our user authentication service using OAuth 2.0 and JWT"
  - "Review our current /v1/orders endpoint and propose a versioning strategy for breaking changes in v2"
# 2–3 concrete invocation examples. Should be copy-paste ready.
---
```

---

## Filled-in Example: `api-designer`

The block below shows the template populated for the `api-designer` agent. Use it as a reference for tone, level of detail, and field completeness.

```yaml
---
name: api-designer
description: "Use this agent when designing new APIs, creating API specifications, or refactoring existing API architecture for scalability and developer experience. Invoke when you need REST/GraphQL endpoint design, OpenAPI documentation, authentication patterns, or API versioning strategies."
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet

category: "01-core-development"

primary_skills:
  - "REST and GraphQL API design"
  - "OpenAPI 3.1 specification authoring"
  - "API versioning and deprecation strategy"
  - "Authentication pattern selection (OAuth 2.0, JWT, API keys)"
  - "Developer experience and documentation"

routing_conditions:
  - "Designing a new REST or GraphQL API from scratch"
  - "Authoring or updating an OpenAPI 3.1 specification"
  - "Defining an API versioning or sunset strategy"
  - "Selecting or designing authentication and authorization flows"
  - "Creating API documentation, Postman collections, or SDK guidance"
  - "Reviewing API contracts for consistency, naming, or HATEOAS compliance"

routing_anti_patterns:
  - "Implementing API route handlers — route to backend-developer or the language specialist (python-pro, node-specialist, etc.)"
  - "Optimizing an existing GraphQL schema — use graphql-architect"
  - "Configuring API gateway rate-limiting or edge auth — use api-gateway-engineer"
  - "Governing async event schemas (Kafka/RabbitMQ/AsyncAPI) — use async-messaging-engineer"
  - "Load-testing or performance benchmarking of an existing API — use performance-engineer"

prerequisites:
  - "Business domain model or entity list (output from business-analyst or product-manager)"
  - "Client use-case list or user stories"
  - "Performance and scalability requirements (optional but helpful)"

escalates_to:
  - "error-coordinator — on any unrecoverable tool failure"
  - "hitl-coordinator — when a design choice has strategic implications (e.g., adopting GraphQL federation, accepting a breaking change)"
  - "knowledge-synthesizer — after completing a complex API design (feeds patterns and anti-patterns learned)"
  - "graphql-architect — when GraphQL federation or advanced schema complexity exceeds scope"

known_limits:
  - "Produces design artifacts (OpenAPI specs, schema docs) — cannot implement server code"
  - "Does not validate runtime performance — use performance-engineer for load-test strategy"
  - "Limited federation expertise — escalates to graphql-architect for complex federation"
  - "Does not configure infrastructure (API gateway, CDN) — use api-gateway-engineer or devops-engineer"

example_prompts:
  - "Design a REST API for an e-commerce order management system including pagination, filtering, webhooks, and an OpenAPI 3.1 spec"
  - "Write authentication flows for our user service using OAuth 2.0 authorization code flow with PKCE and refresh tokens"
  - "Review our /v1/orders endpoint and propose a backward-compatible v2 migration with a 12-month deprecation timeline"
---
```

---

## Agent Prompt Body (below the second `---`)

After the closing `---`, write the agent's system prompt. Conventions:

1. **Role statement** — one sentence establishing identity and specialty.
2. **Invocation protocol** — numbered steps the agent follows when activated.
3. **Domain checklists** — bullet lists covering the agent's primary responsibility areas.
4. **Communication protocol** — JSON request/response patterns for multi-agent coordination (if applicable).
5. **Integration references** — explicit list of agents this agent collaborates with and why.
6. **Closing principle** — one sentence summarizing the agent's north-star priority.

Minimum length: ~50 lines. Complex agents typically run 150–300 lines.

---

## Field Quick-Reference

| Field | Required | Type | Notes |
|---|---|---|---|
| `name` | **Yes** | string | Unique kebab-case slug |
| `description` | **Yes** | string | Starts with "Use this agent when" or "Use when" |
| `tools` | **Yes** | comma list | From approved tool set |
| `model` | **Yes** | enum | `sonnet` \| `opus` \| `haiku` |
| `category` | Optional | enum | One of the 11 category IDs |
| `primary_skills` | Optional | list | 3–5 skill labels |
| `routing_conditions` | Optional | list | Specific trigger conditions |
| `routing_anti_patterns` | Optional | list | What agent does NOT handle + where to route |
| `prerequisites` | Optional | list | Prior agents or context needed |
| `escalates_to` | Optional | list | Escalation targets (include error-coordinator) |
| `known_limits` | Optional | list | Explicit failure modes |
| `example_prompts` | Optional | list | 2–3 copy-paste invocations |

> **Backward compatibility:** All new fields are optional, so existing agent files without them remain valid. The audit script reports coverage but does not fail on missing optional fields.
