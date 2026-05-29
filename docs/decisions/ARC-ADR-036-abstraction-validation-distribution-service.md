# ARC-ADR-036 — Abstraction, Validation & Distribution: the Canonical-Interface Meta-Service

| Field | Value |
|---|---|
| ID | ARC-ADR-036 |
| Status | Accepted |
| Date | 2026-05-29 |
| Deciders | Hub owner (Nicky Clarke) — accepted 2026-05-29 |
| Supersedes | — (extends [ARC-ADR-034](ARC-ADR-034-fleet-cross-repo-access-and-contract-distribution.md) vending; builds on [ARC-ADR-032](ARC-ADR-032-ontology-sift-sort-authoring-loop.md)) |
| Tags | abstraction, anti-corruption-layer, canonical-model, mcp, vending, contract-distribution, validation, adapters, meta-service, ontology |

---

## Context and Problem Statement

The API-interface abstraction tool ([ARC-ADR-032](ARC-ADR-032-ontology-sift-sort-authoring-loop.md) use case) discovers a canonical model + per-source **adapters** by mapping concepts (and fields) across schemas via embedding cosine. Three things became clear in use:

1. **Every layer keeps needing it.** frontend's BFF, middle's agent runtime, the Holonic Board ([#334](https://github.com/nickpclarke/AgentArmy/issues/334)) — each builds an interface and re-faces the same "align N systems' concepts" problem. Hand-rolling adapters per layer means duplication and drift.
2. **It overlaps "vending."** [ARC-ADR-034](ARC-ADR-034-fleet-cross-repo-access-and-contract-distribution.md) decided how canonical artifacts are *distributed* to spokes. The abstraction tool *produces* exactly those artifacts. Abstraction and distribution are two halves of one capability.
3. **Output must be runtime-safe.** A discovered adapter applied blindly fails at runtime — a generic field name (`number`, `state`) misfires at the low-confidence band, a required canonical field goes unmapped, a type mismatches. Plausible adapters are not enough; they must be **proven**.

## Decision

Build a single **meta-service** in backend-core (the canonical / anti-corruption-layer tier per backend-core's application-tier ADR), exposed over **MCP** (agent-callable) and the `/api/v1/ontology/*` routes, that the platform's agent-coders call and the platform eventually **self-hosts**. It has three responsibilities:

### 1. Abstract (build-time)
Schemas (OpenAPI / AsyncAPI / JSON-Schema / GraphQL) → canonical **concepts** + **field adapters** + bottom-up **proposals** (divergence clusters). The embedding-cosine mapper + the seed vocabularies (`api-interface.ttl`, `board.ttl`, `workitem-fields.ttl`).

### 2. Validate (the gate — "snapped, not plausible" for adapters)
The sift discipline ([ARC-ADR-032](ARC-ADR-032-ontology-sift-sort-authoring-loop.md)) applied to adapter output. An adapter is **snapped** (runtime-usable) only when it passes, else **quarantined** with the report:

- **Coverage** — every *required* canonical field has a source mapping (no silent nulls at runtime).
- **Confidence floor** — mappings below the floor are quarantined, not applied; ambiguous ones escalate to the cited gateway model ([ARC-ADR-021](ARC-ADR-021-llm-gateway.md)) — never a silent guess.
- **Type compatibility** — source field type is compatible with the canonical field type.
- **Round-trip** — apply the adapter to representative sample payloads and assert the canonical output is schema-valid (a JSON-Schema gate on the canonical shape).
- **No-collision** — no canonical field fed ambiguously from conflicting sources; no required source field silently dropped.

This is the answer to "comprehensive subroutines so we don't have failure in the runtime": a proven adapter ships; an unproven one is quarantined for review, never run.

### 3. Vend (distribute)
The **proven** canonical artifacts + adapters become versioned, pull-able outputs (extends [ARC-ADR-034](ARC-ADR-034-fleet-cross-repo-access-and-contract-distribution.md)). An agent-coder building a layer's interface calls the MCP tool to fetch the current canonical contract + field adapters for its layer, instead of hand-authoring or hand-vendoring. The `contracts/fleet-interface/` registry is the materialized output.

## Consequences

- **DRY + coherent:** one engine, N consumers; the board, the BFFs, the agent runtime all bind to the same proven canonical layer.
- **Runtime-safe:** only validated adapters are vended/applied; the validation gates prevent the field-level failure modes observed (false maps, missing coverage).
- **Self-hosting meta-service:** the platform's agent-coders use it to build their own interfaces; it runs as a backend-core capability (MCP + routes), no per-layer reimplementation.
- **Build-time vs runtime split:** the service discovers+validates (build-time, needs the embedder); thin runtime consumers apply the *proven* adapter to live payloads (no embedder, no per-item service call).

## Alternatives considered

- **Per-layer libraries** — each layer vendors the abstraction logic. Rejected: duplication + drift; each needs the embedder + vocab.
- **One-off integration containers** (e.g. a board-only sync) — solves a single case; doesn't serve the fleet's recurring abstraction needs.
- **Doc-only vending (ARC-ADR-034 as-is)** — distributes artifacts but doesn't generate or validate them; this ADR makes the producer a service and adds the runtime-safety gate.

## Implementation status (incremental)

- ✅ Abstract: concept-level + field-level (`schema_abstract.py`, `/api/v1/ontology/abstract`), bottom-up proposals.
- ✅ Validate: the adapter gates (`adapter_validate.py` — coverage / confidence-floor / collision / round-trip) **+ the escalate→re-validate→snap loop** (`escalate_below`, method-aware validation). Proven: Linear work-item adapter snaps; GitHub precisely quarantined.
- ◻ Wire validation+escalation into the `/abstract` route (field-level mode) — **next**.
- ◻ Vend: versioned artifact pull via the MCP tool.
- ◻ MCP tool surface + self-host packaging.
- ◻ `board-sync` runtime consumer + container (applies a proven adapter to live GitHub v2 / Linear).
