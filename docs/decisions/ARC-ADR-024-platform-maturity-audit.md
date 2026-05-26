# ARC-ADR-024 — Platform Maturity Audit (run vs design)

| Field | Value |
|---|---|
| ID | ARC-ADR-024 |
| Status | Accepted |
| Date | 2026-05-26 |
| Deciders | Hub owner |
| Supersedes | — |
| Superseded by | — |
| Tags | maturity, audit, ops, design, slo, finops, security, observability, release |

---

## Context

The fleet shipped [ARC-ADR-023](ARC-ADR-023-container-tiering-strategy.md) (container tiering) + the hub-owned ArcadeDB deploy lane + the application-tier `image.json` for backend-core + the LLM gateway extracted as a function-tier container. With those landed, the platform has its first internally consistent shape — but several gaps were obvious enough that the hub owner asked for a **Platform Maturity Audit**, segregating **design/architecture** from **platform ops**.

Eight specialist agents ran in two waves:

**Wave 1 — Design/Architecture** (target-state + strategy):
- `cloud-architect` — env promotion model, dual-ACR resolution, multi-cloud question
- `platform-architect` — golden paths, IDP/catalog question, DORA metrics, Team Topologies fit
- `security-architect` — threat model, secrets lifecycle, ingress posture, supply chain
- `release-manager` — release-train rhythm, semver per repo, contract-version coordination

**Wave 2 — Platform Ops** (current-state + concrete gaps):
- `azure-infra-engineer` — running ACA + ACR + Storage + Log Analytics inventory
- `observability-engineer` — OTel + Log Analytics + dashboards
- `sre-engineer` — first-pass SLOs/SLIs, error budgets, on-call at solo scale
- `finops-engineer` — cost map across the 4 RGs + LLM provider spend kill-switch

This ADR captures **what the audit found, what we'll do about it, the maturity baseline going forward, and the segregation rule for future audits.**

## Decision Drivers

| # | Driver |
|---|---|
| D1 | **Run vs design separation** — hub owner explicitly asked for it; design agents produce target state, ops agents produce current-state gap reports. Don't mix the two. |
| D2 | **The fleet has fires** — three P0 findings need same-day action; the ADR must surface them, not bury them. |
| D3 | **Solo-team realism** — every recommendation must be sized for 1-2 humans + an AI army. No SLOs that need 24×7 humans; no platform that needs a team to operate. |
| D4 | **Specialist agents are leverage, not work** — the audit took 8 agents running in parallel ~10 minutes wall-clock. Future audits should reuse this pattern. |
| D5 | **Maturity is measurable, not vibes** — score each domain on a 5-level scale; track improvement over time via the heartbeat. |

## Decision Outcome

### Run vs design segregation (formal rule)

| Track | Owns | Output shape | Example agents |
|---|---|---|---|
| **Design / Architecture** | Target state, ADRs, strategies, golden paths | Decision documents, target architectures, ADR amendments | `cloud-architect`, `platform-architect`, `security-architect`, `release-manager`, `enterprise-architect`, `solution-architect`, `togaf-adm-advisor`, `wardley-strategist`, `business-architect` |
| **Platform Ops** | Running infra, telemetry, SLOs, cost | Gap reports against live systems, IaC fixes, runbooks, dispatched issues | `azure-infra-engineer`, `gcp-infra-engineer`, `aws-infra-engineer`, `observability-engineer`, `sre-engineer`, `finops-engineer`, `deployment-engineer`, `devops-engineer`, `chaos-engineer`, `incident-responder` |

When commissioning either, brief explicitly with track + output shape. Design produces *what should be true*; Ops measures *what is actually true*. The synthesis (this ADR's role) is where they merge.

See [`docs/agent-tracks.md`](../agent-tracks.md) for the full 178-agent roster classified by track.

### Maturity scorecard (baseline + targets)

Levels: **0 ad-hoc** → **1 named** → **2 measured** → **3 enforced** → **4 optimizing**.

| Domain | Current | 90-day target | Owning track |
|---|---|---|---|
| Container tiering | **3 enforced** (ADR-023 + heartbeat checks) | 4 optimizing | Design + Ops |
| Contract-first | **2 measured** (heartbeat catches drift) | 3 enforced (gated PRs) | Design + Ops |
| Env separation (dev/stg/prd) | **0 ad-hoc** (one unlabeled RG) | 2 measured (`rg-aa-<env>-<tier>`) | Design |
| Identity & secrets | **1 named** (KV exists, no rotation) | 2 measured (rotation policy + KV refs everywhere) | Design + Ops |
| Observability | **1 named** (ADR-010 accepted, zero impl) | 2 measured (OTel collector live, day-1 dashboards) | Ops |
| SLOs / error budgets | **0 ad-hoc** | 2 measured (per-service SLOs + heartbeat burn-rate probe) | Ops |
| FinOps | **0 ad-hoc** | 2 measured (budget alerts + weekly digest) | Ops |
| Release coordination | **0 ad-hoc** | 1 named (semver tags, milestone-driven trains) | Design |
| Public ingress posture | **0 ad-hoc** (naked ACA ingress) | 2 measured (Front Door + WAF) | Design + Ops |
| Container supply chain | **1 named** (Image Standard) | 3 enforced (digest pin + Trivy + SBOM) | Ops |
| Incident response | **0 ad-hoc** | 1 named (Sev1/2/3 + postmortem template) | Ops |

The heartbeat (`tools/fleet-heartbeat.mjs`) is extended over time to *measure* the right-hand column: tier coverage (today), SLO burn rate, OTel readiness, contract version skew, weekly cost digest. **What's measured improves; what isn't, doesn't.**

### P0 (this week — fires)

1. **`frontend-core` revision `--0000023` is FAILED and holds 100% traffic.** Public endpoint returning errors right now. Route traffic to `--0000011` and diagnose the failed deploy. **Owner: hub.**
2. **Hardcoded passwords in ACA env vars.** `arcadedb` JVM args contain root password as plain string; `backend-core` carries `ARCADEDB_PASSWORD` as plain env. Rotate to `secretRef` + Key Vault references. **Owner: hub + backend-core.**
3. **`arcadedb-dev` ACI zombie burning ~$40/mo** in `rg-arcadedb-dev` for no value. Stateless ACI with no volume — pure waste. `az container delete`. **Owner: hub.**
4. **Set LLM provider hard spend caps NOW** ($50/mo OpenAI + $50/mo Anthropic) before any traffic reaches the LLM gateway. **Owner: hub** (provider dashboards).

### P1 (this month — foundations)

5. Converge to one ACR (`agentarmy.azurecr.io`); mirror `arcadeplatformacr` tags via `az acr import` then decommission. Saves ~$15/mo + collapses RBAC surface.
6. Establish `rg-aa-<env>-<tier>` naming convention; stand up `rg-aa-dev-platform` + `rg-aa-dev-app` from the converged ACR. Retire `rg-arcade-platform`'s unlabeled form.
7. Add Azure Front Door + WAF in front of `frontend-core`; lock ACA ingress to FD origin IPs only.
8. Deploy shared OTel Collector + wire Application Insights exporter; emit `traceparent` from `frontend-core` BFF; instrument `backend-core` UDA + LLM gateway spans.
9. Define + ship SLOs/SLIs per service (see Ops agent report — committed as `docs/slos.md`); add SLO burn-rate probe to heartbeat.
10. Add subscription budget ($150/mo all-up dev) + 4-threshold email alerts via Bicep; add weekly cost digest via heartbeat.
11. Document secret rotation cadences (JWT 90d, providers 180d, KV-backed DB roots 180d with ACA revision reload).
12. Migrate `PROJECT_TOKEN` from classic PAT to GitHub App (fine-grained, auto-rotating).

### P2 (this quarter — maturity)

13. Add `scripts/new-spoke.sh` scaffolder + `templates/contract-scaffold/` (`platform-architect`'s biggest leverage call).
14. Ship `docs/catalog.yaml` as the fleet's flat catalog (no Backstage at this scale).
15. DORA baseline via heartbeat `--dora` flag.
16. Trivy scan + SBOM emission gate in image-build workflows; digest-pin all Platform image bases (Renovate).
17. Conventional commits + `git-cliff` per-spoke changelogs; hub GitHub Releases aggregate trains.
18. ArcadeDB restart game day; document Sev1/2/3 + postmortem template under `docs/incidents/`.
19. Define LLM provider outage attribution rule; per-tenant rate limiter + cost-attribution metadata in `/v1/chat/completions`.

### Open decisions (HITL required)

- **Edge provider** — Azure Front Door (recommended, single trust boundary) vs Cloudflare (best DX, separate plane).
- **Single vs dual ACR** — collapse vs document dual-ACR RBAC model. Recommended: collapse.
- **First-tag moment** — concrete trigger for cutting `v0.1.0` across spokes (RT6 Phase 2 complete? first green E2E?).
- **LLM gateway versioning bond** — share backend-core's tag (recommended), or independent tag.
- **GCP scope** — formally narrow to "BigQuery-only, no compute" via a separate ADR-025, or keep open.
- **Postmortem ownership at solo scale** — hub owner writes, or fleet heartbeat agent drafts first pass from issue timeline.

## Implementation

This ADR is the strategy + the baseline scorecard; **execution is dispatched as ~30 labelled issues** across the 4 repos (see the PR body for the full backlog, sourced from each of the 8 specialist reports). Each issue links back to ADR-024 + the originating specialist domain.

The hub fleet heartbeat (`tools/fleet-heartbeat.mjs`) becomes the **maturity-tracking surface** going forward: tier inventory (today), then SLO burn (P1), OTel readiness (P1), cost digest (P1), DORA metrics (P2), contract version skew (P2). When the heartbeat reports a domain at the target level for ≥30 days, the scorecard advances.

The 8 specialist reports are preserved in the PR body for traceability; this ADR captures the synthesized decisions, not the analyses.

## Consequences

- **+** First measurable maturity baseline. Every domain has a current level + a 90-day target.
- **+** Run-vs-design segregation is now a formal rule with a roster classification ([`docs/agent-tracks.md`](../agent-tracks.md)). Future audits reuse the pattern.
- **+** P0 fires are surfaced, not buried.
- **+** Every recommendation is sized for solo-team operation.
- **−** Substantial backlog (~30 issues) dispatched across the fleet — short-term work increase.
- **−** Maturity scorecard requires periodic re-evaluation (proposed: quarterly). Without that cadence the scorecard rots.

## References

- [ARC-ADR-010 — Observability Standard](ARC-ADR-010-observability-standard.md)
- [ARC-ADR-021 — LLM Gateway](ARC-ADR-021-llm-gateway.md)
- [ARC-ADR-022 — Event Bus Bridges](ARC-ADR-022-event-bus-bridges.md)
- [ARC-ADR-023 — Fleet Container Tiering](ARC-ADR-023-container-tiering-strategy.md)
- [`docs/agent-tracks.md`](../agent-tracks.md) — full roster classified by Design vs Ops
- `tools/fleet-heartbeat.mjs` — the measurement surface
- PR body of this ADR's hub PR — full text of all 8 specialist reports
