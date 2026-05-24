# Issue 93 - Middle-Core Use Cases And Object Semantics

## Goal

Turn the middle-core prototype from an object catalog into a use-case-led specification for human and machine users. The object model should explain what people, agents, runbooks, and MCP clients can do with business objects.

## Context

- Issue: `#93 Prototype middle-core ontology UI and runbooks`
- Draft service PR: `#92`
- Frontend prototype PR: `frontend-core#10`
- Current service: C#/.NET `templates/middle-core`
- Current catalog: `templates/business-object-catalog.example.json`

## Non-goals

- Do not implement persistent storage in this slice.
- Do not move provider ownership out of backend-core.
- Do not expose raw ArcadeDB records as public middle-core contracts.
- Do not promote MCP mutation tools before schemas, evidence, auth, and audit are specified.

## Subagents Used

- `information-architect`: ontology and data-object layering.
- `dotnet-core-expert`: modern C# domain model and adapter shape.
- `workflow-orchestrator`: BPMN-style flows, runbooks, playbooks.
- `business-analyst`: use-case review in progress while this spec is drafted.

## Work Breakdown

1. Add a use-case-first specification.
2. Add ontology/data-object architecture guidance behind the use cases.
3. Add workflow/runbook/playbook guidance.
4. Link the new docs from MkDocs navigation.
5. Validate docs and catalog.
6. Update issue #93 with the new spec artifacts.
7. Add the isolated model-driven runtime prototype slice.

## File Ownership

- Integration owner: Codex.
- New docs:
  - `docs/middle-core-use-cases.md`
  - `docs/middle-core-ontology-and-data-objects.md`
  - `docs/middle-core-runbooks-playbooks.md`
- Existing docs to update:
  - `docs/business-object-catalog.md`
  - `mkdocs.yml`
- Model/runtime prototype:
  - `model/middle-core/`
  - `tools/modelgen/`
  - `templates/middle-core/generated/`
  - `templates/middle-core/Runtime/`
  - `docs/middle-core-model-runtime.md`

## Decisions

- Use cases come before object modeling.
- Business objects are public semantic contracts.
- Data objects are internal canonical payloads for validation, composition, redaction, and projection.
- Backend-core owns provider capability APIs and ArcadeDB-facing data.
- Middle-core owns application use cases, ontology/domain rules, scenario orchestration, and safe projections.
- The modern shape is hexagonal/clean architecture inside the deployable service, not an anemic three-tier CRUD layer.

## Validation

- `node tools/business-object-catalog.mjs validate`
- `python -m mkdocs build --strict`

## Risks

- Use cases may still be too internal-platform-heavy; revisit with real target users.
- Data object layer could become a second public API unless explicitly marked internal.
- MCP tool promotion can expand blast radius if schemas, auth, redaction, and audit are weak.
- Generated contracts should start with IDs/constants and DTOs, not generated business behavior.
- YAML is the canonical v1 authoring format for the prototype; RDF/BPMN/DMN are referenced artifacts until later compiler slices.
- Middle-core can prove an EnterpriseWeb-style model runtime through generated contracts plus an in-memory hypergraph before committing to persistence.
