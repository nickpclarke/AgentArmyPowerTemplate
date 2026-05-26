# ARC-ADR-025 — GCP Scope: BigQuery-only, no compute

| Field | Value |
|---|---|
| ID | ARC-ADR-025 |
| Status | Proposed |
| Date | 2026-05-26 |
| Deciders | Hub owner (HITL) |
| Supersedes | — |
| Superseded by | — |
| Tags | gcp, multi-cloud, scope, bigquery, finops, landing-zone |

---

## Context

GCP project `agentarmy-497217` exists (per memory) and is referenced from:

- `.claude/agents/categories/03-infrastructure/gcp-infra-engineer.md` — full GCP infra specialist
- `templates/gcp-cloud-run/` — Cloud Run deploy scaffold (bicep equivalent for GCP)
- `docs/gcp-cloud-run-pipeline.md` — GCP container pipeline guide
- claude.ai MCP connectors — BigQuery + Compute Engine wired via OAuth (per memory)

But the live state in GCP today:
- Zero Cloud Run services
- Zero GKE clusters
- Zero Compute Engine VMs deployed by us
- All actual deployments live in Azure (`rg-arcade-platform`, `rg-github-runner-ci`, `rg-arcadedb-dev`)

This is an **open HITL decision** flagged in [ARC-ADR-024 (Platform Maturity Audit)](ARC-ADR-024-platform-maturity-audit.md) — "GCP exists in tooling, absent in deploys. Either commit to multi-cloud or kill the GCP branch." Three of the eight specialist agents (cloud-architect, security-architect, finops-engineer) independently flagged the dual-cloud surface area as a maturity tax with no current benefit.

This ADR proposes the resolution.

## Decision Drivers

| # | Driver |
|---|---|
| D1 | **Operational simplicity** — single-cloud deploys means single IAM model, single secret store, single observability sink, single billing surface, single landing zone. The fleet has 1-2 humans and one cloud's operational complexity is already non-trivial. |
| D2 | **Don't pay for optionality we don't use** — every quarter we maintain GCP templates / agents / docs that no live workload touches. Maintenance tax with zero traffic. |
| D3 | **BigQuery is genuinely Azure's weak spot** — analytics at scale on petabyte data, ad-hoc SQL exploration, ML feature stores. Azure Synapse is fine but the AI/data ecosystem around BigQuery (Looker, dbt-Cloud, Vertex AI BQ integration, public-dataset reach) is meaningfully ahead. Keep this lane open. |
| D4 | **MCP connectors prove read access works** — the BigQuery + Compute MCP connectors via claude.ai OAuth are configured and connected (per memory `reference_gcp_environment`). Whatever GCP integration exists is *already* read-only ML/analytics-shaped. |
| D5 | **Compute deploy on GCP is a future option, not a current need** — closing this branch today is reversible. Vertex AI's GPU offerings or a specific BigQuery write workload could re-open it, but that's a decision to make at the moment of the requirement. |

## Considered Options

1. **Multi-cloud — Azure (platform) + GCP (some workloads)** — gives optionality. Costs: dual identity, dual secrets, dual deploy pipelines, dual on-call surface area. Real cost; uncertain benefit until a workload actually requires GCP.

2. **Single-cloud — Azure only, kill the GCP branch** — Simplest. Loses BigQuery + Vertex AI as future options. Reversible (re-enable the templates / re-open the project) but not free to reverse.

3. **Single-cloud Azure + BigQuery-only GCP usage** *(proposed)* — Keep `agentarmy-497217` for **analytics / data warehousing / ML feature store** (BigQuery + read-side connectors). Do NOT deploy compute (no Cloud Run, no GKE, no Vertex training jobs paying GPU hourly). Retire `templates/gcp-cloud-run/`, mark `gcp-infra-engineer` as "Read-only / BigQuery-focused" in the agent roster.

## Decision Outcome (proposed)

**Option 3 — BigQuery-only, no compute.**

- **Keep**: `agentarmy-497217` project, BigQuery datasets, GCP MCP connectors (BigQuery + Compute Engine read-only), `docs/gcp-mcp-env.md` reference.
- **Narrow**: `gcp-infra-engineer` agent description to "BigQuery + GCP MCP — read-side, no Cloud Run / GKE provisioning. For compute, use `azure-infra-engineer`."
- **Retire (move to `archive/`)**: `templates/gcp-cloud-run/`, `docs/gcp-cloud-run-pipeline.md`. Available if the decision reverses; gone from the active surface.
- **Reaffirm in CLAUDE.md** under "Routing — Cloud provider / stack choice": Azure is default for compute; GCP for BigQuery / ML feature analytics; AWS not in scope.

Re-opens when:
- A workload concretely requires Vertex AI GPU training or inference, and the cost is justified vs. Azure ML.
- A team consolidation or partner integration brings GCP-native workloads into scope.

Until then, the fleet operates Azure-only for compute + GCP-only for analytics read.

## Consequences

- **+** One landing zone, one identity model, one secret store, one observability pipeline. Maturity gains across every domain in [ADR-024](ARC-ADR-024-platform-maturity-audit.md)'s scorecard.
- **+** `gcp-infra-engineer` becomes a narrower, sharper specialist (read-side data, not Cloud Run ops it never does).
- **+** `templates/gcp-cloud-run/` no longer rots in the active templates dir.
- **−** Loses optionality on Vertex AI / Cloud Run / GKE without a re-open ADR. If a Vertex-AI training workload appears, that's a fresh decision point.
- **−** Some prior docs and the `gcp-cloud-run-pipeline.md` reference become archived rather than active. Discoverability cost is real but small.

## Implementation

If accepted, a follow-up PR:

1. `git mv templates/gcp-cloud-run/ templates/archive/gcp-cloud-run/` + commit message linking this ADR.
2. Update `docs/cloud-serving.md` "Cloud provider / stack choice" to: Azure for compute, GCP BigQuery for analytics, AWS not in scope.
3. Narrow `gcp-infra-engineer` agent description.
4. Add a "How to re-open" subsection here once the archive lands.

Until accepted, the templates stay in place and `gcp-infra-engineer` retains its full description. **This is the open HITL surface — hub owner decides.**

## References

- [ARC-ADR-024 — Platform Maturity Audit](ARC-ADR-024-platform-maturity-audit.md) (this is the source of the open HITL)
- [`docs/cloud-serving.md`](../cloud-serving.md) — current cloud-stack guidance
- [`docs/gcp-mcp-env.md`](../gcp-mcp-env.md) — GCP MCP connector setup (stays in scope under Option 3)
- Memory: `reference_gcp_environment` — current state of the GCP project + MCP wiring
