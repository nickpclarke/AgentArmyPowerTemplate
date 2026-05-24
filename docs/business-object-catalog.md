# Business Object Catalog

The business object catalog is the first functional slice of the `middle-core` vision.

`middle-core` should be a deployable core container that sits between `backend-core` provider capabilities and the platform operational APIs. It is not a nostalgic three-tier entity layer. Its job is to hold semantic contracts, scenario definitions, safety policy, evidence expectations, and future MCP readiness for reusable platform workflows.

## Ontology Principle

Business objects should be understood through the supporting ontology, not as isolated records.

The ontology gives the platform a shared language for describing the phenomena the system cares about: work being routed, knowledge being landed, evidence being assembled, decisions being made, capabilities being exercised, and tools becoming safe enough for agents to use. Those phenomena become observable through activities. Activities become useful through use cases. Use cases matter because they support target personas in achieving their goals.

The modeling chain is:

```text
persona -> goal -> use case -> activity -> phenomenon -> ontology concept -> business object -> provider projection
```

This is the basic rule for `middle-core`:

- a business object should name an ontology concept,
- the concept should describe a phenomenon or state change the platform needs to observe,
- the phenomenon should appear in one or more activities,
- each activity should support a real use case,
- each use case should map to a target persona and goal,
- provider records should remain projections behind that meaning, not the meaning itself.

Example:

| Persona | Goal | Use case | Activity | Phenomenon | Business object |
|---|---|---|---|---|---|
| Platform operator | Know whether a new ArcadeDB capability is healthy and safe to expose. | Run a capability exercise and inspect proof. | Execute `schema-scout`, collect diagnostics, inspect graph/schema output. | Capability health has been observed and evidenced. | `capability-exercise`, `evidence-pack`, `knowledge-graph-snapshot` |
| Agent orchestrator | Route work and prove the result without leaking private details. | Assign a work packet to a specialist pod and require gates. | Evaluate routing policy, assign pod, attach diagnostics. | Work moved from intent to auditable execution. | `work-packet`, `decision-record`, `evidence-pack` |
| Agent/tool consumer | Ask for safe knowledge context without knowing ArcadeDB internals. | Run semantic search and inspect related graph context. | Query, retrieve chunks, project neighboring nodes. | Knowledge relevance has been discovered and bounded. | `knowledge-source`, `knowledge-chunk`, `knowledge-graph-snapshot` |

This keeps `middle-core` modern: it is an ontology-backed semantic service for describing platform activities and their evidence, not a storage-shaped business-logic bucket.

## Service Role

| Service family | What it owns | What it should avoid |
|---|---|---|
| ArcadeDB capability services | Ingest, raw object storage, async jobs, schema inventory, graph snapshots, vector search, guarded read-only query. | Product workflow decisions, MCP exposure, cross-service policy. |
| Platform operational services | Work packets, routing decisions, diagnostics, evidence gates, environments, integrations, audit. | Raw database access or provider-specific query language in public APIs. |
| Meta-services | Scenario templates, scenario runs, capability exercises, tool offerings, learning loops, MCP binding candidates. | Becoming a hidden monolith or bypassing provider/ops policy. |

`middle-core` can host the second and third columns of meaning: business objects, scenarios, and tool-safe projections. It should call `backend-core` for ArcadeDB facts instead of owning ArcadeDB storage directly.

## Current Functional Asset

The repo includes a versioned catalog example:

```powershell
templates/business-object-catalog.example.json
```

It names the initial reusable objects:

| Object | Primary layer | Purpose |
|---|---|---|
| `knowledge-source` | ArcadeDB capability services | Landed files, images, documents, reports, and datasets. |
| `knowledge-chunk` | ArcadeDB capability services | Searchable text or image-derived fragments with citations. |
| `knowledge-graph-snapshot` | ArcadeDB capability services | Safe graph/schema/query projection for cockpit inspection. |
| `capability-exercise` | Meta-services | Reusable proof that a platform capability works in a scenario. |
| `evidence-pack` | Platform operational services | Diagnostics, artifacts, scenario outputs, and contract proof. |
| `work-packet` | Platform operational services | Work item, route decision, pod assignment, blockers, and gates. |
| `decision-record` | Platform operational services | HITL, policy, audit, or architecture decision. |
| `tool-offering` | Meta-services | Safe backend action or scenario eligible for MCP exposure. |
| `scenario-template` | Meta-services | Reusable recipe that composes capabilities into proof-producing flows. |

It also defines scenario families that exercise the core platform capabilities:

| Scenario | What it proves |
|---|---|
| `knowledge-drop` | Upload, land, ingest, chunk, and index mixed content. |
| `semantic-constellation` | Cross-modal search plus graph projection around related knowledge. |
| `schema-scout` | ArcadeDB schema, type, index, count, and sample inspection. |
| `read-only-query-lab` | Guarded read-only query with limits, redaction, and metrics. |
| `evidence-pack` | Proof bundle assembly for work completion or capability promotion. |
| `agent-route-and-prove` | Route work, require gates, import diagnostics, and capture learning. |

## CLI

Validate the catalog:

```powershell
node tools/business-object-catalog.mjs validate
```

Render the deployable `middle-core` view:

```powershell
node tools/business-object-catalog.mjs render --format markdown
```

Write an optional generated artifact:

```powershell
node tools/business-object-catalog.mjs render --format markdown --output tests/artifacts/business-objects/latest.md
```

Generated business-object artifacts are ignored by Git, matching the doctor artifact pattern.

## Deployment Shape

`middle-core` should deploy as its own container when the platform leaves template-only mode:

| Port | Service | Responsibility |
|---:|---|---|
| `8000` | `backend-core` | ArcadeDB provider spoke and low-level platform capability service. |
| `8001` | `middle-core` | Business object catalog, scenario contracts, evidence projections, MCP readiness. |
| `8080` | `frontend-core` | Console, cockpit, and contract-consuming user interface. |

The service manifest examples now include `middle-core` as an optional backend service. In a workload repo, make it required only after the container exists and the health endpoint is stable.

The local host port is `18001` to avoid colliding with existing local backend services. The container still listens on `8001` internally.

The starter container template lives at:

```powershell
templates/middle-core/
```

It is a typed C#/.NET minimal API, not a JavaScript service. It exposes the first read model:

| Endpoint | Purpose |
|---|---|
| `GET /health` | Service and catalog readiness. |
| `GET /catalog` | Full business-object catalog. |
| `GET /objects` | Business object type list. |
| `GET /objects/{id}` | One business object type contract. |
| `GET /scenarios` | Scenario definition list. |
| `GET /scenarios/{id}` | One scenario contract. |

The JavaScript CLI in `tools/business-object-catalog.mjs` remains repo tooling because AgentArmy already uses dependency-light Node tools. The deployable `middle-core` template is typed and object-oriented enough to grow real domain services behind these read models.

## Local Deployment

Reviewers can deploy and smoke-test the draft service locally from the repository root:

```powershell
.\scripts\middle-core\Start-MiddleCoreLocal.ps1
```

The script:

- builds `templates/middle-core/Dockerfile`,
- replaces any existing `middle-core-local` container,
- maps container port `8001` to localhost port `18001`,
- waits for `GET /health`,
- confirms the explorer page contains `Business Object Catalog`,
- prints the useful local URLs.

Expected local URLs:

| URL | Use |
|---|---|
| `http://127.0.0.1:18001/` | Visual business-object and scenario explorer. |
| `http://127.0.0.1:18001/health` | Service readiness and catalog counts. |
| `http://127.0.0.1:18001/catalog` | Full catalog JSON. |
| `http://127.0.0.1:18001/objects/tool-offering` | MCP-ready business object example. |
| `http://127.0.0.1:18001/scenarios/read-only-query-lab` | Guarded ArcadeDB query scenario example. |

To stop the local container:

```powershell
docker rm -f middle-core-local
```

## Modernity Check

This is still a tiered architecture, but not an old-school three-tier stack.

The modern pattern is:

- provider capabilities stay close to the provider,
- business objects are versioned semantic contracts and policy surfaces,
- meta-services compose capabilities into scenarios and tools,
- operational services enforce readiness, audit, evidence, and routing,
- clients consume scenario/object projections instead of raw provider mechanics.

That makes `middle-core` useful for multi-agent systems: agents can ask for a `semantic-constellation` or `evidence-pack` without needing ArcadeDB credentials, raw SQL, repo-specific routing rules, or artifact redaction details.
