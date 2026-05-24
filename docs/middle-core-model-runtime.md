# Middle-Core Model Runtime Prototype

Status: prototype ADR

## Decision

Middle-core should become a model-driven scenario runtime, not a handwritten CRUD service. The first prototype uses YAML as the canonical authoring model and compiles it into generated C# contracts that a small in-memory graph runtime can execute.

```text
model specs -> deterministic generator -> generated C# contracts -> in-memory object graph -> scenario runtime -> evidence output
```

Generated code is disposable. Hand-authored behavior belongs in runtime classes, workflow handlers, projection ports, evidence sinks, partial classes, or future plugins.

## Why This Shape

The platform needs business objects that carry semantics, use-case traceability, workflow meaning, and evidence expectations. A pure three-tier CRUD model would make the objects anemic and push the actual intelligence into controllers or adapters. A fully generated model runtime gives us a modern middle ground:

| Concern | Owner |
|---|---|
| Provider capabilities and ArcadeDB operations | backend-core |
| Canonical model authoring | `model/middle-core/model.yaml` |
| Generated C# IDs, records, contracts, and fixtures | `templates/middle-core/generated` |
| Scenario orchestration, graph mutation, policy, evidence | hand-authored middle-core runtime |
| UI, MCP tools, runbooks, and agents | projections over business objects and scenario results |

## Top-Level Ontology And State Machines

Middle-core should treat lifecycle states as first-class ontology commitments, not UI labels. The top-level model now follows a UFO/OntoUML-inspired stance:

| Top-level idea | Middle-core interpretation |
|---|---|
| Object kind | A durable business object kind such as `knowledge-source`, `evidence-pack`, or `tool-offering`. |
| Lifecycle state | A phase or situation that classifies an object during a bounded part of its lifecycle. |
| State transition | An event type that moves an object from one lifecycle state to another. |
| Scenario execution | An event that causes object creation, graph linking, state movement, and evidence production. |
| Evidence bundle | A proof object that supports claims about scenario execution or capability readiness. |

The referenced prototype top-level ontology lives at `model/middle-core/ontology/top-level-ufo-lite.ttl`. It uses gUFO-style vocabulary references as a lightweight bridge toward RDF/OWL while the YAML model remains authoritative for v1.

`model.yaml` now includes `state_machines`, and every business object declares a `state_machine`. The generator validates that:

- every object references an existing state machine;
- each state machine belongs to a known object type;
- object states and state-machine states match exactly;
- `initial_state`, `terminal_states`, and transition endpoints are valid states;
- transition triggers are stable kebab-case event names.

This gives us a useful place to plug OntoUML/OLED/gUFO validation later. The current official OntoUML documentation describes OntoUML as a UFO-based ontology-driven conceptual modeling language, the OntoUML tooling page lists OLED support for verification, simulation, model checking, inference, and semantic anti-pattern detection, and gUFO provides the Semantic Web/OWL-friendly path for UFO-style ontologies.

## Model Workspace

The prototype model workspace is:

| Path | Purpose |
|---|---|
| `model/middle-core/model.yaml` | Canonical v1 model for objects, data objects, relationships, workflows, scenarios, projections, and use-case traceability. |
| `model/middle-core/ontology/*.ttl` | RDF/Turtle ontology artifact references. |
| `model/middle-core/workflows/*.bpmn` | BPMN workflow artifact references. |
| `model/middle-core/decisions/*.dmn` | DMN decision artifact references. |
| `model/middle-core/projections/*.yaml` | Provider projection artifact references. |

In v1, RDF, BPMN, DMN, and projection files are first-class referenced artifacts, but YAML remains authoritative. Later slices can parse SHACL/BPMN/DMN directly and make the generator fail on semantic drift.

## Generator Usage

Validate the model:

```powershell
python tools/modelgen/validate_middle_core.py --model model/middle-core/model.yaml
```

Regenerate contracts:

```powershell
python tools/modelgen/generate_middle_core.py --model model/middle-core/model.yaml --out templates/middle-core/generated
```

The generator emits only generated surfaces:

| File | Purpose |
|---|---|
| `BusinessObjectTypes.g.cs` | Business object IDs and generated object catalog. |
| `ScenarioIds.g.cs` | Scenario IDs. |
| `DataObjects.g.cs` | Canonical data records. |
| `WorkflowContracts.g.cs` | Workflow step IDs and scenario contracts. |
| `ProjectionContracts.g.cs` | Provider projection contracts. |
| `StateMachineContracts.g.cs` | Lifecycle state machine contracts and transition events. |
| `GeneratedModelValidator.g.cs` | Generated model description and lookup helpers. |
| `ModelSummary.g.md` | Generated summary table for reviewers. |
| `model-runtime.fixture.json` | Deterministic fixture for tests and agents. |

The generator refuses to overwrite files that do not carry its generated marker.

## Runtime Slice

The hand-authored runtime lives under `templates/middle-core/Runtime` and includes:

| Runtime type | Role |
|---|---|
| `ModelObject`, `ModelEdge`, `ModelObjectGraph` | In-memory hypergraph primitives. |
| `ScenarioRuntime` | Executes generated workflow step IDs through registered handlers. |
| `IWorkflowStepHandler<TInput,TOutput>` | Step behavior boundary. |
| `IProjectionPort` | Fake provider adapter boundary for backend-core/ArcadeDB projection data. |
| `IEvidenceSink` | Evidence recording boundary. |
| `KnowledgeDropScenarioRunner` | First end-to-end scenario runner. |

The first scenario is `knowledge-drop`. It creates a graph containing `knowledge-source`, `knowledge-chunk`, `capability-exercise`, `decision-record`, and `evidence-pack` objects, then links them with typed relationships.

Run it locally after setting the catalog path:

```powershell
$env:BUSINESS_OBJECT_CATALOG=(Resolve-Path "templates/business-object-catalog.example.json")
dotnet run --project templates/middle-core/MiddleCore.csproj
```

The prototype template targets .NET 10 so it can run on the current local SDK/runtime and the matching `mcr.microsoft.com/dotnet/*:10.0` container images.

Then open:

```text
http://127.0.0.1:5000/model/demo
```

The scenario lab gives a human-facing test surface with a generated model summary, workflow step timeline, graph visualization, evidence output, raw result, and a button for the disabled-handler failure path.

Failure behavior can be exercised with:

```text
http://127.0.0.1:5000/model/scenarios/knowledge-drop/run?disableLastHandler=true
```

## Authoring Rules

- Every business object must reference a canonical data object and at least one use case.
- Every scenario must reference known workflow steps, input objects, output objects, use cases, and external design artifacts.
- Every projection must target a known business object.
- Generated files must not contain hand-authored business behavior.
- Hand-authored runtime behavior must use generated IDs rather than stringly typed copies.
- Backend-core remains the source of truth for provider capabilities and ArcadeDB-facing operations.

## Future Compiler Path

| Slice | Direction |
|---|---|
| RDF/SHACL | Validate ontology concepts, cardinality, and relationship constraints against the YAML model. |
| BPMN | Compile workflow step order, compensation, retries, and human approval gates. |
| DMN | Compile policy decisions into explicit guard contracts. |
| ArcadeDB projection | Generate projection ports and schema-mapping tests from provider model references. |
| Temporal snapshots | Record graph deltas and evidence packs as time-aware scenario traces. |
| OntoUML/OLED | Use model checking, simulation, anti-pattern detection, and solver-backed validation against top-level state-machine commitments. |
| MCP tools | Promote validated scenario contracts into MCP tool descriptors only after auth, redaction, rate limits, audit, and evidence gates exist. |

## Validation

Use the following checks for this slice:

```powershell
python tools/modelgen/validate_middle_core.py --model model/middle-core/model.yaml
python tools/modelgen/generate_middle_core.py --model model/middle-core/model.yaml --out templates/middle-core/generated
python -m unittest tests.test_middle_core_modelgen
dotnet build templates/middle-core/MiddleCore.csproj
dotnet test templates/middle-core/MiddleCore.csproj
node tools/business-object-catalog.mjs validate
node tools/middle-core-ui-smoke.mjs http://127.0.0.1:18001
$env:MIDDLE_CORE_BASE_URL="http://127.0.0.1:18001"; npx playwright test tests/e2e/middle-core-scenario-lab.spec.js --project=chromium
python -m mkdocs build
```

For a single localhost pipeline that runs the checks, starts the service, exercises the runtime endpoints, and shuts the process down:

```powershell
.\scripts\middle-core\Test-MiddleCoreLocalPipeline.ps1
```

The pipeline uses `http://127.0.0.1:18001` by default and verifies:

| Endpoint | Expected result |
|---|---|
| `/health` | Catalog-backed service health is `ok`. |
| `/model` | Generated model ID is `middle-core-runtime-prototype`. |
| `/model/demo` | Scenario lab renders the graph/evidence test controls. |
| `/model/scenarios/knowledge-drop/run` | Scenario result is `passed`. |
| `/model/scenarios/knowledge-drop/run?disableLastHandler=true` | Scenario fails cleanly with HTTP 400. |

The pipeline also runs the Playwright scenario-lab spec. That browser test clicks the disabled-handler path, checks that the UI moves to failed/no-evidence state, then clicks back to the success path and verifies 6 graph nodes, 5 graph edges, and completed evidence.

For the broader browser-testing pattern and Playwright MCP notes, see [Playwright Browser Testing](playwright.md).

For the reusable template-owned generation harness that can later target backend-core and frontend-core too, see [Generator Platform Tests](generator-platform-tests.md).

For the Docker/container version:

```powershell
.\scripts\middle-core\Start-MiddleCoreLocal.ps1
```

## References

- OntoUML specification documentation: <https://ontouml.readthedocs.io/>
- OntoUML tooling page, including OLED capabilities: <https://ontouml.org/ontouml/tooling/>
- gUFO lightweight UFO implementation: <https://nemo-ufes.github.io/gufo/>
