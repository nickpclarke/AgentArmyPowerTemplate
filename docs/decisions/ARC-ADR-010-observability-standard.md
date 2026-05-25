# ARC-ADR-010 — Observability Standard: OpenTelemetry + Prometheus/Grafana Conventions Across Layers

| Field | Value |
|---|---|
| ID | ARC-ADR-010 |
| Status | Accepted |
| Date | 2026-05-25 |
| Deciders | Architecture Review; accepted by hub owner 2026-05-25 |
| Supersedes | — |
| Superseded by | — |
| Tags | observability, opentelemetry, otel, prometheus, grafana, middle-core, backend-core, frontend-core, sre |

---

## Context and Problem Statement

The platform is becoming a multi-service, multi-language distributed system: frontend-core (Next.js),
middle-core (Python LangGraph runtime **and** the C#/.NET model factory + RT7 runtime), and
backend-core (FastAPI UDA). A single user action already crosses three hops with a forwarded JWT
(ARC-ADR-002). When something is slow or fails, there is currently no agreed way to **correlate** a
request across those hops or to compare metrics emitted by services written in three different
languages.

RT7 (MCR-F3, middle-core #36/#10) is already adding OpenTelemetry traces + Prometheus metrics to the
C# runtime, with specific span and metric names (`scenario.run`, `middle_core_scenario_runs_total`,
`middle_core_scenario_duration_seconds`, etc.) and a cardinality spike (MCR-S2, #16). If each
service picks its own naming, attribute keys, label sets, and exporter config independently, traces
won't join up, metric names won't be comparable, and Grafana dashboards become per-service one-offs.

The decision to be made is: **what is the platform-wide observability standard — OpenTelemetry
semantic conventions (trace context propagation, span/attribute naming), Prometheus metric naming +
label/cardinality rules, the exporter/collector topology, and the Grafana dashboarding convention —
that every layer adopts, in its own language SDK?**

Decided late, RT7's choices become an accidental de-facto standard the Python and Next.js layers may
diverge from; cross-service traces never correlate; and `middle_core_*` vs an ad-hoc `backend_*`
naming makes fleet-wide dashboards impossible. Decided early, all three layers emit a coherent,
correlatable telemetry surface.

---

## Decision Drivers

| # | Driver |
|---|---|
| D1 | A single user request must be **traceable across all three hops** — W3C `traceparent` context propagated frontend-core → middle-core → backend-core (alongside the JWT, ARC-ADR-002). |
| D2 | Metric and span naming must be **consistent and comparable** across C#, Python, and Node services — one convention, three SDKs. |
| D3 | **Cardinality must be controlled** — label sets must not explode (no per-user, per-thread, or raw-URL labels on counters/histograms); MCR-S2 (#16) already flags this for RT7. |
| D4 | The standard must build on what RT7 (MCR-F3) is already shipping — adopt/normalize its choices, don't fork a competing one. |
| D5 | The exporter/collector topology must fit the Azure deployment (ACA/ACI) and be configurable per environment (console exporter in dev, OTLP → collector in prod) without code changes. |
| D6 | Secrets and PII must **never** land in telemetry — no JWT, no token, no raw query results, no connection credentials in spans/logs/labels. |

---

## Considered Options

1. **OTel as the single standard for traces + metrics + logs (OTLP everywhere), Prometheus scrapes
   the collector, Grafana dashboards from one convention** (recommended) — every service uses its
   native OpenTelemetry SDK (.NET, Python, Node) with shared semantic conventions; all signals export
   via OTLP to an OpenTelemetry Collector; the collector exposes Prometheus metrics and forwards
   traces; Grafana reads from a Prometheus + a trace backend. One naming/attribute spec in this ADR.
2. **OTel for traces, Prometheus client libraries directly for metrics** (the RT7 shape, generalized)
   — keep RT7's current split (OTel traces + Prometheus `/metrics` endpoint per service); standardize
   only the *naming* and label conventions across services; each service exposes its own `/metrics`
   for Prometheus to scrape directly.
3. **Per-service / minimal observability (no platform standard yet)** — let each layer instrument as
   it sees fit; defer a fleet-wide convention until an SRE/SLO need forces it.

---

## Decision Outcome

**Accepted 2026-05-25 — Option 1: OpenTelemetry for all signals (OTLP everywhere) + Prometheus/Grafana, generalizing RT7's naming convention.** The HITL framing that produced this choice: HITL — the Architecture Review (with `observability-engineer` / `sre-engineer`
input) must choose, because this sets a fleet-wide convention every spoke inherits and partly
ratifies/redirects what RT7 is already building.

### Recommendation note (not a decision)

Lean **Option 1** as the destination, reached by **generalizing Option 2's RT7 work** rather than
discarding it:

- **Ratify RT7's naming as the seed convention** (D4): `{service}_{subsystem}_{name}_{unit}` for
  metrics (e.g. RT7's `middle_core_scenario_runs_total`,
  `middle_core_scenario_duration_seconds`); backend-core mirrors it as `backend_uda_*`, frontend-core
  as `frontend_*`. Spans use dotted, hierarchical names (`scenario.run`, `uda.query`,
  `copilotkit.run`).
- **Mandate W3C trace-context propagation** (D1): every outbound call forwards `traceparent`
  alongside the JWT, so a CopilotKit request → middle-core agent → backend-core UDA query → ArcadeDB
  is one correlated trace.
- **Pin the cardinality rules** (D3): enumerate allowed label keys per metric; ban high-cardinality
  labels (user id, thread id, raw path, source id) — fold those into trace attributes, not metric
  labels. Adopt MCR-S2's (#16) confirmed attribute set as the template.
- **Exporter topology** (D5): OTLP → an OpenTelemetry Collector as the single sink, configurable per
  env (console in dev, OTLP in prod) — mirroring RT7's "OTLP with console fallback in Development."
  Whether Prometheus scrapes the collector (Option 1) or each service directly (Option 2) is the main
  open sub-question; the collector path is cleaner for a growing fleet.
- **Hard rule (D6):** a telemetry-redaction checklist — no JWT/token, no credentials, no query
  results, no PII in any span/attribute/log/label — referenced from ARC-ADR-002's secret-handling and
  ARC-ADR-011's secret model.

Avoid **Option 3**: deferring guarantees divergence, since RT7 is instrumenting *now*.

---

## Affected Layers / Repos

| Layer | Repo | Impact |
|---|---|---|
| middle-core | nickpclarke/middle-core | C# RT7 OTel/Prometheus already in flight (MCR-F3 #10, MCR-S2 #16, epic #36); Python LangGraph runtime must adopt the same conventions for `copilotkit.run` spans |
| backend-core | nickpclarke/backend-core | FastAPI UDA must emit `backend_uda_*` metrics + `uda.query` spans; propagate inbound `traceparent`; UDA telemetry per the standard |
| frontend-core | nickpclarke/frontend-core | Originate `traceparent`; emit `frontend_*` metrics; instrument the `/api/copilotkit` route hop |
| (infra) | hub templates | OpenTelemetry Collector + Prometheus/Grafana deployment convention; ACA/ACI exporter config |

---

## Pros and Cons of the Options

### Option 1 — OTel for all signals, Collector + Prometheus + Grafana (recommended)

**Pros:**
- One vendor-neutral SDK family across .NET/Python/Node; one place (the collector) to fan out, sample, and redact.
- Cross-service traces correlate cleanly (D1); metrics + traces + logs share resource attributes.
- Backend/exporter swaps are a collector-config change, not a code change (D5).

**Cons:**
- Running and securing a collector is added ops surface.
- Larger migration for RT7 if it standardizes on direct Prometheus scraping today.

### Option 2 — OTel traces + direct Prometheus metrics (generalized RT7 shape)

**Pros:**
- Smallest delta from what RT7 is already building (D4); each service's `/metrics` is independently scrapeable.
- Prometheus client libraries are mature and simple per language.

**Cons:**
- Two instrumentation models (OTel + Prometheus client) per service to keep aligned.
- No single redaction/sampling chokepoint; metric label discipline must be enforced service-by-service.

### Option 3 — No platform standard yet

**Pros:** No upfront design cost; each team moves fast locally.

**Cons:** Guaranteed divergence (RT7 is instrumenting now); traces won't join; dashboards become per-service; retrofitting a standard later is more expensive than setting it now.

---

## Related Decisions

- **ARC-ADR-002:** JWT-forwarding auth contract — `traceparent` is propagated *alongside* the JWT; neither the JWT nor decoded claims may appear in telemetry (D6).
- **ARC-ADR-007** (proposed): Agent streaming protocol — the streaming path is a key span (`copilotkit.run`) whose latency this standard must capture.
- **ARC-ADR-011** (backlog): Runtime secret-resolution — the redaction rules here reference its secret model; collector/exporter endpoints resolve via that scheme.
- **ARC-ADR-015** (backlog): Deployment & release-promotion — where the collector + Prometheus + Grafana run (ACA vs ACI) and per-env exporter config.
- **RT7 MCR-F3 / MCR-S2** (middle-core #10/#16/#36) — the in-flight C# instrumentation this standard ratifies and generalizes.

---

## Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-25 | architect-reviewer (forward ADR backlog) | Initial proposed stub — options open, HITL decision pending |
