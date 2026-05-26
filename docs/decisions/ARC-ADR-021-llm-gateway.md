# ARC-ADR-021 — LLM Gateway: OpenAI-Compatible, in backend-core, for Guardrails

| Field | Value |
|---|---|
| ID | ARC-ADR-021 |
| Status | Accepted |
| Date | 2026-05-26 |
| Deciders | Hub owner (HITL — placement decided: backend-core, for guardrails) |
| Supersedes | — |
| Superseded by | — |
| Tags | llm, gateway, streaming, openai-compatible, guardrails, security, contract, backend-core |

---

## Context and Problem Statement

Every layer wants to call LLMs — chat completions (with **streaming**), embeddings, model
discovery — across **OpenAI and other OpenAI-compatible providers** (OpenAI, Cerebras
[[ARC-ADR-004]], Azure Foundry, a local OpenAI-compatible server e.g. Ollama / vLLM / LM Studio, and
**Anthropic/Claude** via an adapter — see the provider note below). Two hard constraints already
exist: the **browser must never
hold an LLM key** ([[ARC-ADR-003]]), and provider choice should be swappable without rewiring
consumers.

The open question was **where the gateway lives** and **what contract** binds the layers. The hub
owner decided: **it goes through backend-core, for guardrails** — backend-core is the trusted
server boundary that already enforces JWT auth + per-connection RBAC ([[ARC-ADR-013]]), so it is the
right place to centralize policy/safety enforcement on all LLM traffic.

## Decision Drivers

| # | Driver |
|---|---|
| D1 | **Guardrails** — one enforcement point for safety/policy on LLM I/O (the deciding driver). |
| D2 | **Keys off the browser** ([[ARC-ADR-003]]) — provider keys live server-side only. |
| D3 | **Provider-agnostic** — swap OpenAI ↔ Cerebras ↔ Foundry ↔ local without touching consumers. |
| D4 | **Reuse the trusted boundary** — backend-core already does JWT auth + RBAC; don't duplicate it. |
| D5 | **One egress** for rate-limiting, cost attribution, and observability. |

## Considered Options

1. **backend-core hosts the gateway** *(chosen)* — the trusted boundary already enforcing
   auth/RBAC; guardrails sit naturally where the policy engine already is. One server-side egress.
2. **middle-core** — it's the agent runtime (LangGraph/CopilotKit) and a heavy LLM *consumer*, but
   it's a consumer, not the platform's auth/policy boundary; putting guardrails there mixes
   orchestration with policy.
3. **Dedicated LLM-gateway spoke** — cleanest separation, but new infra + it would have to
   re-implement the auth/RBAC backend-core already has.

## Decision Outcome

**Chosen: Option 1 — the LLM gateway runs in backend-core**, exposing an **OpenAI-compatible**
surface (`/v1/chat/completions` with SSE streaming, `/v1/embeddings`, `/v1/models`) defined by
[`contracts/llm-gateway.openapi.yaml`](../../contracts/llm-gateway.openapi.yaml). middle-core and
frontend-core are **consumers**; the browser goes browser → BFF → backend-core (no key in the
browser). Callers forward the user JWT ([[ARC-ADR-002]]); backend-core attaches the provider key
server-side.

### Guardrails backend-core enforces (the "why")

- **AuthN/Z** — reuse JWT + per-connection RBAC ([[ARC-ADR-013]]); deny unauthorized model use.
- **Model allow-listing** — only approved logical models per role/tenant; map logical → provider.
- **Safety / content filtering** — moderate prompts + completions; block disallowed content.
- **Prompt-injection / jailbreak defense** — inspect tool/agent inputs before they reach the model.
- **PII redaction** — scrub sensitive data on the way out and (optionally) in.
- **Rate, quota & cost limits** — per-tenant/per-agent caps; cost attribution via request metadata.
- **Audit** — log who asked what (decision-observability principle), keys never logged.

> Prefer well-tested guardrail tooling over bespoke filters — e.g. provider **moderation
> endpoints**, **LLM Guard** / **NeMo Guardrails**, and standard input-validation libs — wired as a
> backend-core middleware around the gateway router.

### Provider note — Anthropic/Claude (not OpenAI-shaped)

The fleet is Claude-first, so Anthropic is a **first-class provider** — but unlike OpenAI / Cerebras / Foundry / local OpenAI-compatible servers, Claude's native **Messages API** (`/v1/messages`) is **not** OpenAI-shaped: `system` is a top-level param (not a message), `max_tokens` is required, responses are `content` blocks with `stop_reason`, and streaming uses different SSE events (`content_block_delta`, …). So the gateway needs an **adapter** for `claude-*` models that translates **OpenAI ↔ Messages** (system param, `max_tokens` default, `stop_reason`→`finish_reason`, `content_block_delta.text_delta`→`chunk.delta.content`). The contract (consumer-facing) does **not** change — consumers keep speaking OpenAI.

- **Routing:** Claude is reachable via the Anthropic API directly, or via **Bedrock** (AWS) / **Vertex** (GCP) — the gateway selects by deployment config.
- **Alternative:** Anthropic also ships an OpenAI-compat endpoint (`/v1/chat/completions`) — quick to wire but **lossy** (no extended thinking, prompt caching, citations, fine-grained content blocks). Prefer the adapter for control.
- **Caveat:** the OpenAI-compatible surface is lowest-common-denominator. Claude-only capabilities (extended thinking, prompt caching, tool use, vision, citations) don't express cleanly in chat-completions; add an **optional native Messages passthrough / extension fields** if the platform needs them.

## Consequences

- **+** Single guardrail/policy point; provider swap behind a stable contract; keys contained; key
  reuse of existing auth/RBAC; one place for cost/observability.
- **−** Adds an LLM-egress concern to backend-core (coupling with the Data API) — **mitigate** by
  isolating it as its own router/module (`app/llm/…`) with the guardrail middleware, so it can later
  be extracted to a dedicated spoke if egress volume warrants (the contract wouldn't change).
- **−** Guardrail + SSE pass-through add latency/complexity — stream chunks through, run cheap
  guards inline and heavier checks async where possible.

## Relationship to other contracts

Distinct from the **AG-UI agent stream** ([[ARC-ADR-007]], `agui-stream.asyncapi.yaml`): that
carries higher-level *agent-run* events (CopilotKit); this carries **raw model tokens**
(chat/completions). Don't conflate them. The gateway is registered in
[docs/contracts.md](../contracts.md).
