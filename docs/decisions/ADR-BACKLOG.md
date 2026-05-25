# ADR Backlog — Forward Architecture-Decision Queue (ARC-ADR-007 onward)

The forward queue of architecture decisions the platform trajectory makes **inevitable**. These
are not yet decided — they are *foreseen*. Each entry names the decision to be made, the work it
gates, a priority, a target Program Increment (PI), and a status.

> **Why this exists.** ARC-ADR-001..006 cover the CopilotKit three-hop runtime that is being
> built *now*. The next waves of work — agent streaming/memory, the Universal Data Adapter (UDA)
> multi-connector platform, observability, deployment promotion, the ontology slice, and the
> identity/secret model — each carry cross-cutting decisions that will block implementation if
> they're discovered late. This page queues them so the Architecture Review (and `hitl-coordinator`
> when an option needs a human/AI-app call) can drive them ahead of the gated work, not behind it.

> **House process.** Producing an ADR: design the option space (often with `api-designer`,
> `solution-architect`, or the relevant specialist), draft the stub in `docs/decisions/` in the
> ARC-ADR format (see [architecture-decisions.md](../architecture-decisions.md) and any of
> ARC-ADR-002/005/006 as the canonical shape), then move it `Backlog` → `Proposed` → `Accepted`.
> A cross-cutting contract decision also gets registered in [contracts.md](../contracts.md).

## Legend

| Field | Meaning |
|---|---|
| **ID** | Proposed ARC-ADR number (reserved on drafting; renumber only if a higher-priority decision jumps the queue). |
| **Priority** | P0 = gates active/imminent work this PI · P1 = should be settled this PI · P2 = horizon decision, settle before the gated RT starts. |
| **Status** | `Backlog` (foreseen, not drafted) · `Proposed` (stub drafted, options open) · `Accepted` (decided). |
| **Gates** | The work/release-train that cannot safely start until this decision lands. |

## Status snapshot

| Existing (built / being built) | Forward queue (this page) |
|---|---|
| ARC-ADR-001..006 — HITL pattern, JWT forwarding, no-LLM-key-in-browser, Cerebras LLM, backend OpenAPI contract, HITL destructive ops · **ARC-ADR-007..013 now Accepted** (streaming, memory, canonical model, observability, secret resolution, query caching, per-connection RBAC) | ARC-ADR-014..019 below — contract versioning, deployment promotion, ontology reification, connector egress/SSRF, async/job execution, ontology+reasoning layer (#019 Proposed), plus horizon entries |

---

## Index

| ID | Title | Decision to be made | Gates | Priority | Target PI | Status |
|---|---|---|---|---|---|---|
| **ARC-ADR-007** | Agent streaming protocol | SSE vs WebSocket vs CopilotKit-native transport for streaming agent tokens/UI events frontend-core ⇄ middle-core | CopilotKit Phase 1+ streaming UX; middle-core `/copilotkit` endpoint (#22); frontend-core runtime route (#13) | **P0** | PI-1 | **Accepted** ([adr](ARC-ADR-007-agent-streaming-protocol.md)) |
| **ARC-ADR-008** | Agent conversation-memory / thread-state store | Where thread state + conversation memory lives, and how it is isolated per-user/per-thread (in-proc vs Redis vs ArcadeDB vs LangGraph checkpointer backend) | Multi-turn agent memory; resumable threads; middle-core #32/#33; CopilotKit Phase 2+ | **P0** | PI-1 | **Accepted** ([adr](ARC-ADR-008-agent-memory-store.md)) |
| **ARC-ADR-009** | Canonical data model + Arrow type vocabulary | The cross-connector Common Data Model and the canonical Arrow/ADBC type vocabulary every UDA connector normalizes into | UDA multi-connector normalization (backend-core #35/#43); BigQuery/Postgres/object-store connectors; convergence with middle-core `model.yaml` | **P0** | PI-1 | **Accepted** ([adr](ARC-ADR-009-canonical-data-model-arrow.md)) |
| **ARC-ADR-010** | Observability standard | OpenTelemetry semantic conventions + Prometheus/Grafana metric naming/cardinality across all three layers (C#, Python, FastAPI) | RT7 MCR-F3 OTel/Prometheus (middle-core #36/#10/#16); backend-core UDA telemetry; SRE/SLO work | **P0** | PI-1 | **Accepted** ([adr](ARC-ADR-010-observability-standard.md)) |
| **ARC-ADR-011** | Runtime secret-resolution & workload identity | Formalize the secret-resolver scheme: `env:` (local/CI) vs `akv:` + managed identity (prod) vs OIDC/WIF (deploy), and the resolution precedence | Every spoke's prod config; UDA connection credentials; deployment workflows; Key Vault wiring | **P1** | PI-1 | **Accepted** ([adr](ARC-ADR-011-runtime-secret-resolution-workload-identity.md)) |
| **ARC-ADR-012** | Read-query caching & invalidation | Whether/where to cache UDA read results, the cache key (per-connection + per-principal), TTL/invalidation, and isolation | UDA read-path performance (backend-core #45); cross-connector query lab; cost control | **P1** | PI-2 | **Accepted** ([adr](ARC-ADR-012-read-query-caching-invalidation.md)) |
| **ARC-ADR-013** | Per-connection RBAC + role taxonomy | Extend ARC-ADR-002's role model to per-connection authorization: who can read/query/admin which UDA connection, and the role taxonomy | UDA per-connection RBAC (backend-core #46); governance plane; connection registry | **P1** | PI-2 | **Accepted** ([adr](ARC-ADR-013-per-connection-rbac-role-taxonomy.md)) |
| **ARC-ADR-014** | Contract versioning & drift governance | `SchemaVersion` semantics, deprecation/sunset policy, and the drift-gate contract across OpenAPI + generated C# projection contracts | MCR-F4/F5 schema-version + drift gate (middle-core #11/#12); UDA binding to middle-core projections; all inter-layer contracts | **P1** | PI-2 | Backlog |
| **ARC-ADR-015** | Deployment & release-promotion model | localhost → dev → prod promotion path; ACI vs ACA per service; the IaC standard (Bicep vs Terraform) and the promotion gate | All spoke deploys; MCR-EN2 ACA manifest (middle-core #14); UDA prod; release trains | **P1** | PI-2 | Backlog |
| **ARC-ADR-016** | Ontology representation (reification + hyperedges) | Adopt the relator-vertex + typed role-binding reification design (and its bitemporal/PROV placement) as the canonical n-ary relationship representation | Ontology reification slice (middle-core #96 follow-on); ArcadeDB schema; canonical model (ADR-009) | **P2** | PI-2 | Backlog |
| **ARC-ADR-017** | Connector egress / SSRF policy | Allow/deny-list + network egress controls for UDA connectors that take user/operator-supplied connection targets (URLs, hosts, object-store endpoints) | UDA connector onboarding (backend-core #43); object-storage + arbitrary-DSN connectors; security review | **P1** | PI-2 | Backlog |
| **ARC-ADR-018** | Async/job-execution & long-running-tool model | How long-running tools (ingest, large queries, pipeline runs) execute and report progress: in-request vs background worker vs durable-execution library vs external orchestrator vs dlt pipeline + job-status polling | CopilotKit Phase 2 ingest progress card; UDA dlt pipelines; backend-core job-status endpoints | **P2** | PI-2 | **Proposed** ([adr](ARC-ADR-018-async-job-execution-model.md)) — spike backend-core #67 done; recommend pilot DBOS reversibly |
| **ARC-ADR-019** | Ontology + reasoning layer | Architecture of the inference layer: where it runs, how foundational ontologies plug in (pluggable gUFO ‖ BFO profiles), and which reasoner powers it — `export snapshot → RDF → OWL reasoner → materialize back to ArcadeDB` as a UDA `ReasonerCapable` capability. *Distinct from #016 (ontology **representation**/reification); the two compose.* | RT-reasoning slice; backend-core spike #65 (gUFO PoC); research #60/#62; middle-core #49 (gUFO OWL emitter) | **P2** | PI-2 | **Proposed** ([adr](ARC-ADR-019-ontology-reasoning-layer.md)) — spike #65 complete; recommend Accept Option 1 (rdflib+owlrl seed) |
| **ARC-ADR-020** | Self-hosted CI runner trust & isolation | Policy that keeps self-hosted CI safe from untrusted `pull_request` code execution and prevents silent regression (private-only invariant + fork-origin job guard + fork-PR approval + least-privilege runner identity) | All self-hosted CI across hub + spokes; runner templates (`aca-github-runner`, `local-docker-runner`); any future public/external-contributor scenario | **P1** | PI-2 | **Proposed** ([adr](ARC-ADR-020-self-hosted-runner-trust-isolation.md)) — Codex finding; **no forks in the threat model** (owner-confirmed) so fork mitigations out of scope; lightweight posture = document the private/trusted/no-forks invariant + optional least-privilege runner |

---

## Horizon (foreseen, lower confidence — promote to numbered when the gating RT firms up)

These are inevitable *enough* to name, but their option space or trigger is still soft. They are
not yet assigned ARC-ADR numbers to avoid reserving IDs that may reorder.

| Candidate | Decision to be made | Likely trigger / gate | Priority |
|---|---|---|---|
| Multi-tenancy / data-isolation boundary | Tenant model across UDA connections + agent memory + caches (row-level vs connection-level vs deployment-level isolation) | First multi-tenant customer or shared-deployment requirement | P2 |
| Cost / FinOps guardrails for connectors | Per-connection query budgets, BigQuery slot/cost caps, LLM token budgets, and where they're enforced | BigQuery connector live + real spend; `finops-engineer` involvement | P2 |
| Embedding model + vector-store strategy | Embedding provider/dimensionality (Azure Foundry embed-v-4 1536-d today) + which store owns vectors as connectors multiply | Second embedding source or a non-ArcadeDB vector need | P2 |
| Agent tool-authorization / capability gating | Which tools a given agent/principal may invoke (capability map → tool offering), beyond endpoint RBAC | Agent roster growth; MCP tool projection from `model.yaml` | P2 |
| PII / data-governance & audit-log standard | Classification, redaction, retention, and the audit-trail format spanning agent actions + UDA queries | Governance plane work; regulated data in a connector | P2 |
| Rate limiting & API-gateway/edge policy | Edge authN/Z, rate limits, and routing across spoke APIs (`api-gateway-engineer`) | Public exposure of any spoke API | P2 |

---

## Related

- [architecture-decisions.md](../architecture-decisions.md) — the ADR guide and format.
- [contracts.md](../contracts.md) — inter-layer contract registry (every cross-cutting contract ADR is mirrored here).
- [plans/copilotkit-rollout-coordination.md](../plans/copilotkit-rollout-coordination.md) — the active CopilotKit work ADR-007/008 gate.
- [release-trains/RT7-middle-core-runtime.md](../release-trains/RT7-middle-core-runtime.md) — RT7 (MCR-*) which ADR-009/010/014/015/016 gate.
- ARC-ADR-001 — the HITL Decision Artifact pattern: the escalation path when any queued option needs a human/AI-app call rather than an Architecture Review call.
