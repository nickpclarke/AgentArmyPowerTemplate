---
tags: [contracts, registry, function-tier, backlog, snapshot]
date: 2026-05-27
status: snapshot
related:
  - "[[API Strategy — Internal, External, Open & Monetized]]"
  - "[[Data Products & Semantic Contracts]]"
  - "[[Cloud Agents → Local Docker — Control Plane Plan]]"
---

# Contract Backlog 2026-05-27

Snapshot of the contract-landscape expansion + sub-container strategy that landed in **ARC-ADR-027** and the bundled PR `feat/contract-backlog-and-function-tiers`. This note is the cross-agent visibility layer (cloud agents in microVMs can read this through the in-repo Obsidian vault per memory `project_docs_collaboration_surface`).

## What changed today

1. **Contract registry expanded** with a `## Backlog (anticipated contracts)` section in [docs/contracts.md](../../../docs/contracts.md). 35 anticipated contracts across 5 sub-tables:
   - Design system / frontend-core (8)
   - Middle-core (5)
   - Backend-core (6)
   - Cross-cutting (10)
   - Upstream vendored (6)

2. **Three near-term contracts authored** in `contracts/`:
   - `health.openapi.yaml` — `/livez` / `/readyz` / `/healthz` standard for every spoke.
   - `problem-details.openapi.yaml` — RFC 7807 error envelope `$ref`'d by every other spec.
   - `llm-gateway.openapi.yaml` — extended with SSE event taxonomy + tool-call delta + stream-usage event + mid-stream error envelope.

3. **One Registry entry added** — `backend-core/contracts/agent-gateway.openapi.yaml` (A2A + MCP gateway). Clears the fleet-heartbeat `unregistered-contract` warning.

4. **Five Function-tier image scaffolds** under `templates/*/`:
   - `otel-collector-image/` — sidecar + standalone OTel Collector (XC-2, ADR-024 OTel-init remediation).
   - `local-embedder-image/` — local embeddings for ArcadeDB RAG (BE-4, hub #184).
   - `hmac-verify-image/` — reusable signed-webhook verifier (lifts pattern out of event-bridge).
   - `schema-migrator-image/` — Postgres + ArcadeDB migration init container.
   - `jwt-introspect-image/` — sidecar realizing ARC-ADR-002's verify-side.

5. **ARC-ADR-027** — codifies the Backlog discipline + names the five Function-tier additions + documents the splits explicitly declined (BE micro-split, MC tier-split, FE service-server).

## The non-obvious decision

The user asked for "sub-container approach for microservices rapid build/deploy parallelism." There's an apparent tension with ADR-023's "Don't pre-split" anti-rule. The resolution: **Application tier stays one-per-spoke** (backend-core #93 is correct), and parallelism comes from the **Function tier** where ADR-023's split rule actually justifies separate images.

Specifically:

- backend-core stays as ONE container (FastAPI + Rust v2 → merged per #93).
- middle-core stays as ONE container.
- frontend-core stays as ONE container.
- New Function-tier images come into existence only when one of {hardware profile, scale curve, release cadence, blast-radius isolation} truly diverges.

This way the user gets the deploy parallelism they want (more pieces shipping independently), without paying the distributed-systems cost on the parts of the stack that don't need it yet.

## Where the work goes next

After the bundled PR merges, the orchestration agent dispatches **one issue per Backlog row** to the producing spoke with `agent-army-task` label, body linking back to the row + this Labs note. Roughly 30 issues across the fleet. The two armies (Claude via `@claude`, Copilot via `copilot-coding-agent`) pick them up over time.

The five Function-tier scaffolds become individual implementation issues — each one mechanical enough to be a `copilot-task` once the design is locked.

## Open questions / risks

- **The agent-gateway ADR is missing.** `backend-core/contracts/agent-gateway.openapi.yaml`'s `info.description` cites "ARC-ADR-025" but that number is taken by `ARC-ADR-025-gcp-scope-narrowing.md`. Either author a new agent-gateway ADR or re-number. Tracked in the Registry row.
- **ADR-010 referenced but not verified.** `templates/otel-collector-image/image.json` and the new ADR-027 both reference ARC-ADR-010 (observability standard); I didn't verify it exists on disk. If it doesn't, add it as a Backlog row in its own right (an ADR is a kind of contract too).
- **Backlog rows can rot.** Each carries a Horizon (`near` / `mid` / `later`). Items at `later` should be deletable without ceremony if they no longer apply.

## Links

- PR: `feat/contract-backlog-and-function-tiers` (TBD once opened)
- ADR: [[../../../docs/decisions/ARC-ADR-027-contract-backlog-discipline.md|ARC-ADR-027]]
- Registry: [[../../../docs/contracts.md|docs/contracts.md]]
- Container tiering parent: [[../../../docs/decisions/ARC-ADR-023-container-tiering-strategy.md|ARC-ADR-023]]
- Platform maturity audit: [[../../../docs/decisions/ARC-ADR-024-platform-maturity-audit.md|ARC-ADR-024]]
