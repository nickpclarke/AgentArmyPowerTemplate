# Middle-Core Ontology And Data Objects

Use cases tell us what must exist. Ontology gives those use cases stable language. Data objects give the C# layer a typed, provider-neutral shape it can validate and transform.

## Semantic Trace

Every shared middle-core object should be traceable through this chain:

```text
persona -> goal -> use case -> activity -> phenomenon -> ontology concept -> business object -> data object -> provider projection -> physical record
```

Example:

| Trace point | Example |
|---|---|
| Persona | Platform operator |
| Goal | Know whether ArcadeDB schema inspection is safe to expose |
| Use case | Inspect ArcadeDB schema safely |
| Activity | Run schema scout |
| Phenomenon | Capability health has been evidenced |
| Ontology concept | `CapabilityObservation` |
| Business object | `capability-exercise` |
| Data object | `CapabilityExerciseData` |
| Provider projection | Backend-core schema inventory response |
| Physical record | ArcadeDB type/index/sample summaries |

## Business Object vs Data Object

| Layer | Meaning | Example | Public? |
|---|---|---|---|
| Business object | What the platform means to users, agents, UI, scenarios, and MCP tools. | `evidence-pack` | Yes |
| Data object | What middle-core needs to validate, compose, redact, persist, and exchange that meaning. | `EvidencePackData` | Internal contract |
| Provider projection | How a provider represents the data object. | Doctor artifact, GitHub check run, ArcadeDB graph snapshot | Adapter boundary |
| Physical record | Concrete record or response owned by a provider. | ArcadeDB `Chunk`, GitHub issue, artifact file | Provider-owned |

The data-object layer is useful, but it must stay narrow. It is not a second public API and it is not a duplicate of backend-core provider DTOs.

## Initial Ontology Concepts

| Concept | Meaning | Business objects |
|---|---|---|
| `ActorIntent` | A person, agent, or automation has a goal that can become platform work. | `work-packet` |
| `SemanticAsset` | Knowledge has been landed, chunked, indexed, cited, or related. | `knowledge-source`, `knowledge-chunk`, `knowledge-graph-snapshot` |
| `CapabilityObservation` | A platform capability has been exercised and observed. | `capability-exercise` |
| `EvidenceBundle` | Proof has been collected for work, readiness, or a capability. | `evidence-pack` |
| `GovernedDecision` | A human, agent, or policy decision affects system behavior. | `decision-record` |
| `ScenarioContract` | A repeatable workflow has typed inputs, outputs, policy, and evidence expectations. | `scenario-template` |
| `ToolCandidate` | A scenario or action may become safe for MCP exposure. | `tool-offering` |
| `RunbookAction` | A failure or operational signal maps to a repeatable response. | future `runbook-execution` |

## State Machines As Ontology Commitments

The ontology should treat state machines as a top-level modeling concern. A state is not merely an enum value; it is a lifecycle classification of a business object. A transition is not merely a setter; it is an event with preconditions, evidence, and downstream effects.

The prototype now captures this in `model/middle-core/model.yaml` through generated `StateMachineContract` records. Each business object points to exactly one state machine, and validation rejects unknown states or invalid transitions. This gives future RDF/SHACL, BPMN, DMN, and OntoUML checks a stable target:

```text
UFO/OntoUML kind -> business object kind -> lifecycle state machine -> transition event -> scenario evidence
```

Recommended top-level distinction:

| Ontology level | Examples | Why it matters |
|---|---|---|
| Foundational | UFO/gUFO notions of object kind, event type, situation, role, and relator. | Keeps upper semantics consistent as domain ontologies expand. |
| Middle-core core | `BusinessObjectKind`, `LifecycleState`, `StateTransition`, `ScenarioExecution`, `EvidenceBundle`. | Defines reusable platform semantics. |
| Domain/mid-level | `SemanticAsset`, `CapabilityObservation`, `GovernedDecision`, `ToolCandidate`. | Describes platform phenomena without provider leakage. |
| Lower/provider | ArcadeDB `RawObject`, `Chunk`, `Embedding`, diagnostics artifacts. | Keeps persistence and provider mechanics behind projections. |

## Recommended Catalog Fields

Add these fields when the catalog moves from prototype to contract:

| Field | Applies to | Purpose |
|---|---|---|
| `ontology_concept_id` | object type | Stable semantic concept. |
| `phenomenon` | object type, scenario | What became observable or true. |
| `persona_goal_refs` | object type, scenario | Human/machine goals supported. |
| `canonical_data_object` | object type | Internal C# data payload name. |
| `identity_policy` | object type | How object IDs relate to provider refs. |
| `lifecycle_policy` | object type | Allowed transitions and terminal states. |
| `classification` | object type, scenario | Sensitivity and exposure posture. |
| `retention_policy` | object type | Evidence/data retention. |
| `relationship_constraints` | object type | Valid relationship types and direction. |
| `projection_contracts` | object type | Provider projection IDs and rules. |
| `ontology_activity_id` | scenario | Activity modeled by the scenario. |
| `preconditions` | scenario | What must be true before execution. |
| `postconditions` | scenario | What must be true after success. |
| `evidence_requirements` | scenario | Proof required for success/promotion. |
| `data_objects_read` | scenario | Canonical data payloads consumed. |
| `data_objects_written` | scenario | Canonical data payloads produced. |
| `audit_events` | scenario | Events emitted during execution. |

## C# Architecture Shape

Use a hexagonal/clean architecture shape inside the deployable service:

```text
API DTOs
  -> Application Use Cases
  -> Domain/Ontology Objects
  -> Canonical Data Objects
  -> Ports
  -> Adapters for backend-core, ArcadeDB, GitHub, diagnostics, MCP
```

The current C# minimal API can remain a starter, but the next implementation slice should split behavior into:

| Package/folder | Owns |
|---|---|
| `Contracts` | Request/response DTOs, catalog DTOs, generated IDs/constants. |
| `Application` | Use case handlers such as `RunSchemaScout` or `AssembleEvidencePack`. |
| `Domain` | Smart business objects, policies, lifecycle transitions, redaction decisions. |
| `DataObjects` | Internal canonical payloads such as `EvidencePackData` and `ProviderRecordRef`. |
| `Ports` | Interfaces for backend-core, diagnostics, GitHub, MCP registry. |
| `Adapters` | Concrete HTTP/OpenAPI clients and provider projectors. |

## Generation Strategy

Generate stable plumbing, not business behavior:

- Generate backend-core API clients from OpenAPI.
- Generate catalog constants such as `BusinessObjectTypes.KnowledgeSource`.
- Generate scenario input/output DTO stubs from JSON Schema.
- Generate validation tests that prove catalog references still resolve.
- Do not generate domain methods, redaction decisions, lifecycle transitions, or tool-promotion decisions.

The prototype implementation now anchors this in `model/middle-core/model.yaml`, `tools/modelgen/`, and generated C# under `templates/middle-core/generated`. See [Middle-Core Model Runtime](middle-core-model-runtime.md) for the runtime ADR, generator commands, and generated-vs-hand-authored boundary.

## Source-Of-Truth Rules

| Item | Source of truth |
|---|---|
| ArcadeDB storage and raw provider operation | backend-core |
| Business object meaning and lifecycle policy | middle-core |
| Scenario contract and MCP eligibility | middle-core |
| Evidence artifacts and diagnostics | platform operational service, projected by middle-core |
| UI card/read model | middle-core projection |
| MCP tool descriptor | middle-core tool-offering contract |

## Guardrails

- A business object must map to at least one use case.
- A shared business object must declare an ontology concept.
- A data object must not be exposed directly to UI or MCP clients unless promoted to a business object contract.
- A provider projection must declare direction, freshness, source of truth, redaction stage, and identity mapping.
- MCP-eligible scenarios need strict input/output schemas, auth scopes, rate limits, redaction, audit events, and recent capability evidence.
