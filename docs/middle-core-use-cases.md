# Middle-Core Use Cases

Middle-core exists only if it helps humans and machine users get work done. The business objects are not valuable because they are tidy nouns. They are valuable when they let a user ask for a meaningful platform activity without knowing provider internals.

Use this rule before adding or changing any business object:

```text
actor -> goal -> use case -> activity -> business objects -> data objects -> provider projections -> evidence
```

## Actor Groups

| Actor | Human or machine | What they need from middle-core |
|---|---|---|
| Platform operator | Human | Inspect health, exercise capabilities, approve or disable platform features. |
| Knowledge worker | Human | Add knowledge and ask questions with citations and safe graph context. |
| Project lead | Human | See routed work, blockers, readiness, evidence, and review posture. |
| Governance reviewer | Human | Understand why a decision, promotion, route, or tool exposure is allowed. |
| Developer/operator | Human | Debug schema, graph, query, and ingestion behavior without raw provider access. |
| Agent orchestrator | Machine | Route work to the right specialist pod and prove completion. |
| MCP client or LLM agent | Machine | Discover and invoke safe scenario-level tools with typed inputs and outputs. |
| CI/release automation | Machine | Run readiness checks and attach evidence after deploys or contract changes. |
| Runbook automation | Machine | Detect failures, select playbooks, execute safe steps, and escalate when needed. |
| Catalog/code generator | Machine | Generate constants, DTO stubs, schemas, and projection tests from catalog contracts. |

## Use Case Matrix

| ID | Use case | Primary actor | Main business objects | Current scenario |
|---|---|---|---|---|
| UC-01 | Land knowledge and prove it is searchable | Knowledge worker | `knowledge-source`, `knowledge-chunk`, `capability-exercise`, `evidence-pack` | `knowledge-drop` |
| UC-02 | Ask for a semantic constellation | Knowledge worker or LLM agent | `knowledge-chunk`, `knowledge-graph-snapshot` | `semantic-constellation` |
| UC-03 | Inspect ArcadeDB schema safely | Developer/operator | `knowledge-graph-snapshot`, `capability-exercise`, `evidence-pack` | `schema-scout` |
| UC-04 | Run a bounded read-only query | Developer/operator or MCP client | `scenario-template`, `knowledge-graph-snapshot`, `evidence-pack` | `read-only-query-lab` |
| UC-05 | Route work to a specialist pod | Project lead or agent orchestrator | `work-packet`, `decision-record`, `evidence-pack` | `agent-route-and-prove` |
| UC-06 | Prove work is done | Project lead or agent orchestrator | `work-packet`, `evidence-pack`, `decision-record` | `evidence-pack` |
| UC-07 | Exercise a capability before promotion | Platform operator or CI automation | `scenario-template`, `capability-exercise`, `evidence-pack` | `schema-scout`, `semantic-constellation` |
| UC-08 | Promote a scenario into an MCP tool | Platform operator or governance reviewer | `tool-offering`, `scenario-template`, `decision-record`, `evidence-pack` | Future `tool-promotion` |
| UC-09 | Disable or degrade an unsafe tool/capability | Runbook automation or platform operator | `tool-offering`, `capability-exercise`, `decision-record`, `evidence-pack` | Future `capability-incident` |
| UC-10 | Generate typed object contracts | Catalog/code generator | `scenario-template`, `tool-offering`, all catalog object types | Future `catalog-codegen` |
| UC-11 | Review a decision and its downstream effects | Governance reviewer | `decision-record`, `work-packet`, `tool-offering`, `evidence-pack` | `agent-route-and-prove` |
| UC-12 | Recover a failed ingest or scenario run | Runbook automation | `knowledge-source`, `capability-exercise`, `evidence-pack`, `decision-record` | Future `runbook-execution` |
| UC-13 | Curate a trusted knowledge source | Platform admin or domain curator | `knowledge-source`, `decision-record`, `tool-offering` | Future `knowledge-source-curation` |
| UC-14 | Review chunks before promotion | Domain expert | `knowledge-source`, `knowledge-chunk`, `evidence-pack` | Future `knowledge-curation-review` |
| UC-15 | Retrieve approved context for a task | Planning, coding, or docs agent | `knowledge-source`, `knowledge-chunk`, `knowledge-graph-snapshot`, `work-packet` | `semantic-constellation` |
| UC-16 | Recommend a tool offering | Tool-routing agent or MCP planner | `tool-offering`, `work-packet`, `scenario-template`, `decision-record` | Future `tool-recommendation` |

## UC-01 - Land Knowledge And Prove It Is Searchable

**Actor:** Knowledge worker, platform operator, or ingestion automation.

**Goal:** Add a file, image, report, dataset, or mailbox export and know that it became searchable with evidence.

**Trigger:** A user uploads content or an automation submits a new `knowledge-source`.

**Business objects used:** `knowledge-source`, `knowledge-chunk`, `capability-exercise`, `evidence-pack`.

**Data objects:** `KnowledgeSourceData`, `KnowledgeChunkData`, `IngestJobData`, `EvidencePackData`, `ProviderRecordRef`.

**Provider projections:** ArcadeDB `RawObject`, `StoredFile`, `IngestJob`, `Chunk`, `ImageObject`, `Embedding`.

**Happy path:**

1. Middle-core validates source metadata, tenant scope, file type, size, and retention class.
2. Middle-core starts the `knowledge-drop` scenario.
3. Backend-core lands the raw object and starts ingestion.
4. Backend-core creates chunks, captions, embeddings, and indexes.
5. Middle-core records a `capability-exercise`.
6. Middle-core assembles an `evidence-pack` with redaction status, counts, timings, and links.
7. UI and agents see a searchable `knowledge-source` and bounded `knowledge-chunk` summaries.

**Exception path:** If ingestion fails, middle-core marks the source `failed`, attaches diagnostics, selects `RB-KNOW-001`, and leaves the source unavailable for MCP use.

**Acceptance criteria:**

- A user can see whether the source is `landed`, `ingesting`, `indexed`, `searchable`, or `failed`.
- The response never exposes raw bytes or local paths by default.
- The evidence pack shows ingest status, chunk count, redaction status, and provider refs.

## UC-02 - Ask For A Semantic Constellation

**Actor:** Knowledge worker, LLM agent, or MCP client.

**Goal:** Ask a question and receive relevant chunks plus a safe graph snapshot around those results.

**Trigger:** A user or machine submits a query and optional source scope.

**Business objects used:** `knowledge-chunk`, `knowledge-graph-snapshot`, `capability-exercise`.

**Data objects:** `SearchQueryData`, `KnowledgeChunkData`, `GraphSnapshotData`, `ProviderRecordRef`.

**Provider projections:** ArcadeDB vector search result, graph node, graph edge, index summary.

**Happy path:**

1. Middle-core validates query length, limit, source scope, and tenant scope.
2. Backend-core executes vector search and returns bounded results.
3. Middle-core requests a graph projection around the result set.
4. Middle-core redacts raw embeddings and sensitive sample values.
5. UI or MCP client receives chunks, citations, relationship summary, and graph snapshot ID.

**Exception path:** If the query is too broad, middle-core narrows or rejects it with a policy result and suggested filters.

**Acceptance criteria:**

- Results include citations or source refs.
- Graph snapshot is bounded and expires.
- Raw embeddings and provider credentials are not exposed.

## UC-03 - Inspect ArcadeDB Schema Safely

**Actor:** Developer/operator or platform operator.

**Goal:** Understand current ArcadeDB types, fields, indexes, counts, and safe samples without direct database access.

**Trigger:** User opens schema cockpit or CI runs a schema readiness check.

**Business objects used:** `knowledge-graph-snapshot`, `capability-exercise`, `evidence-pack`.

**Data objects:** `SchemaInventoryData`, `GraphSnapshotData`, `CapabilityExerciseData`.

**Provider projections:** ArcadeDB type inventory, index summary, graph node and edge type summaries.

**Happy path:**

1. Middle-core starts `schema-scout`.
2. Backend-core collects type, field, index, count, and safe sample summaries.
3. Middle-core validates sample bounds and redaction policy.
4. Middle-core emits a `knowledge-graph-snapshot`.
5. Evidence records schema inventory time, counts, and any drift warnings.

**Exception path:** If sensitive samples appear, middle-core marks the snapshot summarized-only and opens a decision or incident runbook.

**Acceptance criteria:**

- Schema output distinguishes document, vertex, and edge projections.
- Counts and indexes are visible.
- Samples are bounded, redacted, and optional.

## UC-04 - Run A Bounded Read-Only Query

**Actor:** Developer/operator, platform operator, or read-only MCP client.

**Goal:** Explore data safely with policy-checked read-only queries.

**Trigger:** A query is submitted through UI or a future MCP tool.

**Business objects used:** `scenario-template`, `knowledge-graph-snapshot`, `capability-exercise`, `evidence-pack`.

**Data objects:** `ReadOnlyQueryData`, `QueryResultData`, `QueryMetricsData`, `PolicyDecisionData`.

**Provider projections:** ArcadeDB SQL or graph query response.

**Happy path:**

1. Middle-core validates the query against allowed verbs, timeout, row limit, and tenant scope.
2. Backend-core runs the query using server-side credentials.
3. Middle-core redacts rows and records metrics.
4. Middle-core returns columns, rows, metrics, and a graph snapshot ref when useful.

**Exception path:** Mutation keywords, unbounded scans, disallowed types, or missing scope return a policy denial and audit event.

**Acceptance criteria:**

- Read-only constraints are enforced before provider call.
- Outputs are schema-bound.
- Query metrics and redaction status are attached to evidence.

## UC-05 - Route Work To A Specialist Pod

**Actor:** Project lead, developer lead, or agent orchestrator.

**Goal:** Turn a vague work request into an assigned, gated, auditable work packet.

**Trigger:** Issue, project item, PR review, or user request becomes work.

**Business objects used:** `work-packet`, `decision-record`, `evidence-pack`.

**Data objects:** `WorkPacketData`, `RoutingDecisionData`, `AgentPodData`, `EvidenceRequirementData`.

**Provider projections:** GitHub issue, project item, PR, review thread.

**Happy path:**

1. Middle-core normalizes the incoming work into a `work-packet`.
2. It validates Definition of Ready.
3. It evaluates routing policy and candidate agents.
4. It records a `decision-record` with selected owner/pod and policy version.
5. It attaches evidence requirements and updates the work state.

**Exception path:** If routing is ambiguous or privileged, middle-core creates a decision record and sets the work packet to `awaiting-decision`.

**Acceptance criteria:**

- Work packet shows actor, goal, repo, scope, risk, owner/pod, gates, blockers, and state.
- Routing decision is explainable.
- Security-sensitive work requires the right sidecars.

## UC-06 - Prove Work Is Done

**Actor:** Project lead, reviewer, CI automation, or agent orchestrator.

**Goal:** Know whether a work packet can move to done.

**Trigger:** PR, diagnostics, review, or manual evidence is attached.

**Business objects used:** `work-packet`, `evidence-pack`, `decision-record`.

**Data objects:** `EvidencePackData`, `EvidenceRequirementData`, `DiagnosticRunData`, `ArtifactRef`.

**Provider projections:** GitHub check run, PR review state, local doctor artifact, screenshot, build log.

**Happy path:**

1. Middle-core reads the work packet's evidence requirements.
2. It imports diagnostics, checks, screenshots, review status, and artifact refs.
3. It validates hashes, redaction status, and freshness.
4. It marks evidence requirements satisfied.
5. It allows transition to `done` or leaves a clear missing-evidence report.

**Exception path:** Missing required evidence blocks transition and starts `RB-WORK-001`.

**Acceptance criteria:**

- Done state is derived from evidence, not vibes.
- Missing gates are named.
- Waivers require a decision record.

## UC-07 - Exercise A Capability Before Promotion

**Actor:** Platform operator or CI/release automation.

**Goal:** Prove a capability is ready before exposing it to users or agents.

**Trigger:** New backend-core capability, deploy, schema change, or scheduled readiness check.

**Business objects used:** `scenario-template`, `capability-exercise`, `evidence-pack`, `decision-record`.

**Data objects:** `CapabilityExerciseData`, `ScenarioRunData`, `ReadinessPostureData`.

**Provider projections:** Backend-core health, ArcadeDB schema/search/query responses, diagnostic artifacts.

**Happy path:**

1. Middle-core selects the right scenario template.
2. It runs preflight policy checks.
3. It executes the capability through backend-core.
4. It captures metrics, errors, redaction status, and outputs.
5. It computes readiness posture and attaches evidence.

**Exception path:** Failed readiness degrades the capability and opens `RB-CAP-001`.

**Acceptance criteria:**

- Readiness states are visible: `candidate`, `ready`, `degraded`, `disabled`.
- Evidence is recent enough for promotion.
- Failures produce an actionable runbook.

## UC-08 - Promote A Scenario Into An MCP Tool

**Actor:** Platform operator, governance reviewer, or tool registry automation.

**Goal:** Expose a proven scenario as a safe tool for agents.

**Trigger:** Scenario has passing capability exercises and is marked MCP-eligible.

**Business objects used:** `tool-offering`, `scenario-template`, `capability-exercise`, `decision-record`, `evidence-pack`.

**Data objects:** `ToolOfferingData`, `McpToolBindingData`, `ScenarioContractData`, `PolicyDecisionData`.

**Provider projections:** MCP tool descriptor, JSON input schema, JSON output schema, backend-core endpoint.

**Happy path:**

1. Middle-core creates a `tool-offering` candidate.
2. It validates input and output schemas.
3. It checks auth scope, tenant scope, rate limits, redaction, and audit requirements.
4. It links recent capability evidence.
5. It records promotion approval and publishes a read-only tool binding first.

**Exception path:** Schema, evidence, or policy failure keeps the tool in `candidate` or `disabled` state.

**Acceptance criteria:**

- Tool offers scenario-level operations, not raw provider access.
- Tool descriptor is strict, versioned, and auditable.
- Emergency disable has a documented runbook.

## UC-09 - Disable Or Degrade An Unsafe Tool Or Capability

**Actor:** Runbook automation, platform operator, or governance reviewer.

**Goal:** Stop unsafe or degraded behavior quickly while preserving evidence.

**Trigger:** Failing scenario, abuse signal, security concern, schema drift, or integration degradation.

**Business objects used:** `tool-offering`, `capability-exercise`, `decision-record`, `evidence-pack`.

**Data objects:** `IncidentSignalData`, `RunbookExecutionData`, `ReadinessPostureData`.

**Provider projections:** MCP registry state, backend-core health response, diagnostics.

**Happy path:**

1. Middle-core correlates the signal with affected scenarios and tools.
2. It selects a runbook.
3. It disables or degrades the tool/capability if policy permits automation.
4. It re-runs diagnostics.
5. It records evidence and audit events.

**Exception path:** If automated action is unsafe, middle-core creates a decision record and alerts a human owner.

**Acceptance criteria:**

- Unsafe tool exposure can be disabled without code deploy.
- Consumers can see degraded posture.
- Evidence and audit explain why the action happened.

## UC-10 - Generate Typed Object Contracts

**Actor:** Catalog/code generator, CI automation, or developer.

**Goal:** Generate useful code from the catalog without generating business behavior.

**Trigger:** Catalog changes, build runs, or source generator executes.

**Business objects used:** `scenario-template`, `tool-offering`, all catalog object types.

**Data objects:** `CatalogContractData`, `ScenarioContractData`, generated ID constants, DTO stubs.

**Provider projections:** OpenAPI client types, JSON Schema, future C# generated constants.

**Happy path:**

1. Generator reads the business object catalog.
2. It validates object IDs, states, scenarios, and MCP schemas.
3. It emits strongly typed IDs/constants and DTO stubs.
4. Tests confirm generated contracts match backend-core OpenAPI and catalog references.

**Exception path:** Drift blocks generation and reports unresolved object, scenario, or provider capability refs.

**Acceptance criteria:**

- Generated code includes IDs and DTO shapes, not lifecycle decisions.
- Business methods remain hand-authored in domain objects.
- CI fails on catalog/backend-core drift.

## UC-11 - Review A Decision And Downstream Effects

**Actor:** Governance reviewer, platform operator, or agent orchestrator.

**Goal:** Understand why work was routed, a gate waived, a tool promoted, or a capability disabled.

**Trigger:** User opens a decision record or policy audit trail.

**Business objects used:** `decision-record`, `work-packet`, `tool-offering`, `evidence-pack`.

**Data objects:** `DecisionRecordData`, `AuditEventData`, `PolicyDecisionData`.

**Provider projections:** GitHub decision issue/comment, audit artifact, PR review state.

**Happy path:**

1. Middle-core retrieves the decision and target object refs.
2. It shows options considered, actor, policy version, outcome, and downstream effects.
3. It links evidence and affected work/tools/capabilities.
4. It marks superseded decisions when a later decision replaces them.

**Exception path:** Sensitive rationale is summarized unless caller has the right scope.

**Acceptance criteria:**

- Decision records are traceable to affected objects.
- Sensitive context follows redaction policy.
- Superseded decisions are visible but not active.

## UC-12 - Recover A Failed Ingest Or Scenario Run

**Actor:** Runbook automation or platform operator.

**Goal:** Recover a failed scenario safely, or escalate with evidence.

**Trigger:** Scenario run, ingest job, or capability exercise fails.

**Business objects used:** `knowledge-source`, `capability-exercise`, `evidence-pack`, `decision-record`.

**Data objects:** `RunbookExecutionData`, `ScenarioRunData`, `DiagnosticRunData`.

**Provider projections:** Backend-core job status, ArcadeDB operation result, diagnostic artifact.

**Happy path:**

1. Middle-core classifies failure type.
2. It selects a runbook by scenario, capability, environment, and severity.
3. It runs safe retry or compensation steps.
4. It re-runs diagnostics.
5. It updates object state and evidence.

**Exception path:** Repeated failure creates a decision record and learning signal.

**Acceptance criteria:**

- Runbook execution has entry criteria, steps, approval points, rollback, evidence, and success criteria.
- Repeated failures become learning signals.
- Object state reflects the latest validated posture.

## UC-13 - Curate A Trusted Knowledge Source

**Actor:** Platform admin, domain curator, product owner, or governance reviewer.

**Goal:** Register and govern a trusted source before agents can use it as context.

**Trigger:** A repo, document set, wiki, runbook library, decision archive, mailbox export, or external reference should become usable by agents.

**Business objects used:** `knowledge-source`, `decision-record`, `tool-offering`.

**Data objects:** `KnowledgeSourceData`, `AccessPolicyData`, `FreshnessPolicyData`, `DecisionRecordData`.

**Provider projections:** ArcadeDB `RawObject` or source registry record, GitHub repo/document refs, external URI refs.

**Happy path:**

1. Human defines source owner, type, URI/location, access policy, refresh cadence, classification, and intended use cases.
2. Middle-core validates required metadata and checks whether the source needs a decision or license review.
3. Middle-core marks the source `landed` or `approved-for-ingest`.
4. Any downstream tool offering inherits allowed consumers and restrictions.

**Exception path:** Missing owner, license clarity, access permission, retention, or freshness policy blocks activation and creates a required `decision-record`.

**Acceptance criteria:**

- Source has owner, source type, location/ref, access policy, refresh cadence, allowed consumers, status, and intended use cases.
- Restricted sources cannot be returned to agents or MCP tools until approved.
- Source metadata is visible without leaking credentials or local paths.

## UC-14 - Review Knowledge Chunks Before Promotion

**Actor:** Domain expert, curator, governance reviewer, or analyst.

**Goal:** Approve extracted chunks before they become agent-usable context.

**Trigger:** Ingestion creates candidate chunks from a source.

**Business objects used:** `knowledge-source`, `knowledge-chunk`, `evidence-pack`.

**Data objects:** `KnowledgeChunkData`, `ChunkReviewData`, `EvidencePackData`.

**Provider projections:** ArcadeDB `Chunk`, `ImageObject`, `Embedding`, review artifact.

**Happy path:**

1. Middle-core presents candidate chunks with source provenance, labels, classification, and confidence.
2. Human approves, rejects, merges, relabels, or marks chunks sensitive.
3. Approved chunks become searchable and agent-usable within policy.
4. Middle-core attaches review evidence to the source and chunk set.

**Exception path:** Duplicate, stale, sensitive, too-broad, or unsupported chunks are rejected or quarantined.

**Acceptance criteria:**

- Approved chunks link to source, reviewer, timestamp, classification, provenance, and allowed usage.
- Rejected chunks retain enough evidence for audit without being used as context.
- Agent retrieval can filter to approved-only chunks.

## UC-15 - Retrieve Approved Context For A Task

**Actor:** Planning agent, coding agent, documentation agent, review agent, or analyst agent.

**Goal:** Get relevant approved context without reading the whole repository or raw provider store.

**Trigger:** Agent receives a user request, issue, work packet, or scenario.

**Business objects used:** `knowledge-source`, `knowledge-chunk`, `knowledge-graph-snapshot`, `work-packet`.

**Data objects:** `TaskIntentData`, `SearchQueryData`, `KnowledgeChunkData`, `GraphSnapshotData`.

**Provider projections:** ArcadeDB vector results, source refs, graph projection.

**Happy path:**

1. Agent submits task intent and optional work-packet context.
2. Middle-core translates intent into bounded retrieval and policy scope.
3. Backend-core returns ranked chunks and graph context.
4. Middle-core filters to approved context and returns provenance, confidence, restrictions, and object links.

**Exception path:** No approved context, conflicting chunks, stale source, or restricted source returns a context gap with suggested human action.

**Acceptance criteria:**

- Response includes relevant chunks, source provenance, confidence, restrictions, and links to business objects.
- Restricted or unreviewed chunks are excluded unless explicitly authorized.
- Conflicts are surfaced rather than silently collapsed.

## UC-16 - Recommend A Tool Offering

**Actor:** Tool-routing agent, MCP planner, workflow orchestrator, or agent orchestrator.

**Goal:** Match a user goal or work packet to available safe tools.

**Trigger:** A task needs execution support such as ingestion, graph query, schema inspection, evidence assembly, or runbook execution.

**Business objects used:** `tool-offering`, `work-packet`, `scenario-template`, `decision-record`.

**Data objects:** `ToolOfferingData`, `ToolFitData`, `ScenarioContractData`, `PolicyDecisionData`.

**Provider projections:** MCP tool descriptor, scenario contract, backend-core endpoint.

**Happy path:**

1. Agent evaluates the task goal, work packet, and policy context.
2. Middle-core returns eligible tool offerings with required inputs, expected outputs, constraints, and readiness posture.
3. Agent recommends a tool or sequence of tools with rationale.
4. Middle-core records the recommendation if it affects routing, execution, or a decision.

**Exception path:** Tool is unavailable, unauthorized, deprecated, lacks required contract, or has stale readiness evidence; agent proposes fallback or blocks execution.

**Acceptance criteria:**

- Recommendation includes tool ID, fit rationale, required inputs, expected outputs, constraints, and policy status.
- Disabled or degraded tools are not recommended as normal path.
- Raw provider operations are not recommended when a scenario-level tool exists.

## What This Means For The C# Layer

The C# service should be organized around application use cases, not object tables:

```text
HTTP/API DTOs
  -> application use cases
  -> domain/ontology business objects
  -> canonical data objects
  -> ports
  -> backend-core, ArcadeDB, GitHub, diagnostics, MCP adapters
```

Example application use case names:

- `LandKnowledgeSource`
- `RunSemanticConstellation`
- `RunSchemaScout`
- `RunReadOnlyQueryLab`
- `RouteWorkPacket`
- `AssembleEvidencePack`
- `ExerciseCapability`
- `PromoteToolOffering`
- `DisableToolOffering`
- `GenerateCatalogContracts`
- `ReviewDecisionRecord`
- `ExecuteRunbook`

This is still layered, but it is not an old-school anemic three-tier model. The domain objects should enforce invariants. The data objects should normalize and validate payloads. The adapters should keep provider details outside the public contract.

## References

- Microsoft .NET microservices guidance on DDD/CQRS and internal architecture: <https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/>
- Azure Architecture Center tactical DDD guidance: <https://learn.microsoft.com/en-us/azure/architecture/microservices/model/tactical-domain-driven-design>
- Microservices.io Saga pattern for cross-service workflows: <https://microservices.io/patterns/data/saga>
- Model Context Protocol security best practices: <https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices>
- ArcadeDB multi-model overview: <https://docs.arcadedb.com/arcadedb/tutorials/what-is-arcadedb.html>
