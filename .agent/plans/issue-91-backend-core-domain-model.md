# ExecPlan: Backend-Core Platform Domain Model

Issue: https://github.com/nickpclarke/AgentArmy/issues/91

## Goal

Define the intended backend-core object model and business rules behind the AgentArmy Platform API. The output should make the OpenAPI contract useful as a control-plane contract for agent routing, work coordination, diagnostics evidence, platform configuration, and the learning loop.

## Context

AgentArmy is a starter template and coordination hub, not an application. The current repository has an OpenAPI contract (`index.yaml` and `postman/specs/index.yaml`) and an optional `backend-core` service declaration in `agentarmy.services.json`.

The sibling repos clarify the platform direction:

- `C:\Dev\backend-core` is a provider spoke over ArcadeDB. It supports ingest, async jobs, durable raw objects, vector search, cockpit endpoints, and a Rust `/api/v2` platform control-plane seed.
- `C:\Dev\frontend-core` is a contract consumer and console/cockpit surface. It exercises backend-core over OpenAPI-generated clients and makes ArcadeDB capabilities visible.

The API describes useful resource areas: health, agents, work items, diagnostics, environments, integrations, and platform config. The missing layer is the domain model and business policy that explains how these nouns behave together.

The better framing is that the core platform should support three service families:

- ArcadeDB capability services that exercise concrete graph, vector, raw-object, schema, and query features;
- platform operational services that serve work, routing, diagnostics, environments, integrations, evidence, and audit;
- meta-services that coordinate scenarios, control-plane work, diagnostics, routing, evidence, learning, and future MCP tool exposure.

The business-object layer can deploy as `middle-core`: a separate core container that owns semantic contracts, scenario contracts, and tool-safe projections while calling `backend-core` for ArcadeDB facts.

## Non-goals

- Do not create a backend service implementation in this pass.
- Do not add database migrations, app code, or provider SDKs.
- Do not replace GitHub Projects as the coordination plane.
- Do not store secrets or personal provider keys in committed config.
- Do not make breaking OpenAPI changes without a migration path.

## Relevant Docs And Source Of Truth

- `AGENTS.md`
- `index.yaml`
- `postman/specs/index.yaml`
- `agentarmy.services.json`
- `templates/business-object-catalog.example.json`
- `templates/middle-core/`
- `tools/business-object-catalog.mjs`
- `C:\Dev\backend-core\README.md`
- `C:\Dev\backend-core\app\main.py`
- `C:\Dev\backend-core\app\store.py`
- `C:\Dev\backend-core\rust-api-v2\src\platform.rs`
- `C:\Dev\frontend-core\README.md`
- `C:\Dev\frontend-core\src\App.svelte`
- `C:\Dev\frontend-core\src\components\Cockpit.svelte`
- `C:\Dev\frontend-core\agentarmy-console\README.md`
- `docs/routing-decision-tree.md`
- `docs/routing-matrix.md`
- `docs/github-projects.md`
- `docs/diagnostics-standards.md`
- `docs/platform-diagnostics-cli.md`
- `planning/roadmap/PLATFORM_ROADMAP.md`
- `.agent/plans/issue-80-platform-diagnostics-cli.md`

## Subagents Used

- `product-manager`: inferred product intent, use cases, and platform capabilities.
- `api-designer`: advisory review for aggregates, workflows, and contract gaps.
- `security-architect`: advisory review for authorization, audit, secrets, and evidence rules.

## Work Breakdown

1. Inspect the current API contract, diagnostics docs, routing docs, roadmap, board conventions, and service manifest.
2. Create a backend-core domain model document that covers:
   - intended platform goal,
   - aggregate model,
   - business rules,
   - workflow policies,
   - security and evidence constraints,
   - OpenAPI mapping and additive contract gaps,
   - implementation slices for future work.
3. Link the document from the MkDocs navigation.
4. Validate YAML/docs build where tooling is available.

## File Ownership

Owner:

- `.agent/plans/issue-91-backend-core-domain-model.md`
- `docs/backend-core-object-model.md`
- `docs/business-object-catalog.md`
- `templates/business-object-catalog.example.json`
- `templates/middle-core/Dockerfile`
- `templates/middle-core/MiddleCore.csproj`
- `templates/middle-core/Program.cs`
- `templates/service-manifest.example.json`
- `tools/business-object-catalog.mjs`
- `tools/business-objects/business-object-catalog.v1.schema.json`
- `mkdocs.yml`

Do not edit unrelated user changes such as `docs/hooks.md`.

## Tests And Validation

Run as applicable:

```powershell
node tools/validate-routing.mjs
node tools/business-object-catalog.mjs validate
docker build -f templates/middle-core/Dockerfile -t middle-core:local .
node tools/agentarmy-doctor.mjs
python -m mkdocs build --strict
```

For this pass, validation should prove the new documentation can be rendered and that existing routing/platform checks still parse.

## Risks

- Over-modeling could make the future backend feel heavy. Keep rules modular and implementable in slices.
- Under-modeling routing decisions would miss the roadmap's keystone move: executable policy and auditable delegation.
- Duplicating GitHub Projects semantics could create two conflicting coordination planes. Model GitHub as the durable external source where appropriate.
- Diagnostics and artifacts can leak sensitive values if redaction is not part of the object model from the start.

## Decision Log

- Treat backend-core as the future control-plane service behind the existing OpenAPI contract.
- Keep current OpenAPI additions additive until an implementation branch is ready to version the contract.
- Model `RoutingPolicy`, `RoutingDecision`, `AgentPod`, `EvidenceRequirement`, and `LearningSignal` as first-class domain concepts because they connect the roadmap, routing docs, diagnostics standards, and work-item lifecycle.
- Model `PlatformCapability`, `Scenario`, and `McpToolBinding` as first-class concepts because the sibling frontend/backend repos show the platform is also a modular capability exerciser over ArcadeDB and future service surfaces.
- Add a business-object middle layer so scenarios, UI cards, diagnostics, graph views, and MCP tools can share stable nouns instead of binding directly to raw provider records or generic control-plane tables.
- Treat `middle-core` as the deployable home for business-object contracts, scenario contracts, and meta-service projections. It should not own raw ArcadeDB storage; it composes `backend-core` capability services and platform operational services.
- Use a typed service implementation for deployable `middle-core`. The repo-local catalog CLI can stay JavaScript because it follows AgentArmy's dependency-light tooling pattern, but the container starter is C#/.NET with records, enums, and nullable checks.
