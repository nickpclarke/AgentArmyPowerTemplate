# ARC-ADR-004 — LLM Provider = Cerebras (+ OpenAI-Compatible Fallback; Tool-Calling Caveats)

| Field | Value |
|---|---|
| ID | ARC-ADR-004 |
| Status | Accepted |
| Date | 2026-05-25 |
| Deciders | Architecture Review; accepted by hub owner 2026-05-25 |
| Supersedes | — |
| Superseded by | — |
| Tags | llm, cerebras, langchain, tool-calling, middle-core |

---

## Context and Problem Statement

middle-core requires an LLM to power the LangGraph `create_react_agent`. The LLM must support **tool calling** (function calling) — the agent's primary interaction model with backend-core is via structured tool invocations, not free-form text generation.

Cerebras has been selected by the user as the preferred LLM provider (`langchain-cerebras`, `ChatCerebras`, model `llama-3.3-70b`). However, Cerebras has known tool-calling edge cases — specifically, an **empty-content tool-call bug** where the assistant message in a tool-calling response may have empty `content`, which can cause downstream JSON parsing failures in some LangChain/LangGraph versions.

The decision to be made is: **how should `llm.py` be structured to use Cerebras reliably for tool calling, and what is the fallback strategy when Cerebras cannot handle a specific tool-calling pattern?**

---

## Decision Drivers

| # | Driver |
|---|---|
| D1 | The LLM must support tool calling reliably for the seven LangGraph tools in `tools.py`. |
| D2 | The primary provider is Cerebras (`langchain-cerebras`, `ChatCerebras`) — this is a locked user decision. |
| D3 | A fallback path must exist for the known empty-content tool-call bug without requiring a provider swap in production. |
| D4 | The LLM factory must be testable with a mocked LLM — no live Cerebras calls in CI. |
| D5 | Context window and rate limits must be managed (Cerebras has lower limits than GPT-4 class models). |

---

## Considered Options

1. **`ChatCerebras` primary + `ChatOpenAI` (Cerebras OpenAI-compatible base URL) fallback** (proposed) — `llm.py` exposes both paths; fallback activated via `LLM_PROVIDER=openai-compat` env var; empty-content bug mitigated by ensuring non-empty assistant content.
2. **`ChatCerebras` only** — use Cerebras exclusively; accept the empty-content bug risk; mitigate at the LangGraph message-processing layer.
3. **OpenAI directly as primary** — use `gpt-4o` or `gpt-4o-mini` as primary; Cerebras as cost-optimized fallback.
4. **Anthropic Claude as primary** — use `claude-3-haiku` or `claude-3-5-sonnet` as primary via the Anthropic adapter.

---

## Decision Outcome

**To be decided.** The Architecture Review recommends Option 1 as the most pragmatic path: Cerebras is the locked primary choice, and the OpenAI-compatible endpoint at `https://api.cerebras.ai/v1` provides a fallback that uses the same API key and model but via the more battle-tested LangChain OpenAI integration.

### Proposed decision: Option 1 — ChatCerebras primary + OpenAI-compat fallback

- `llm.py` implements `get_llm()` which reads `LLM_PROVIDER` (default: `cerebras`).
- `LLM_PROVIDER=cerebras` → returns `ChatCerebras(model=CEREBRAS_MODEL, api_key=CEREBRAS_API_KEY)`.
- `LLM_PROVIDER=openai-compat` → returns `ChatOpenAI(model=CEREBRAS_MODEL, base_url=CEREBRAS_BASE_URL, api_key=CEREBRAS_API_KEY)` where `CEREBRAS_BASE_URL=https://api.cerebras.ai/v1`.
- Empty-content mitigation: `agent.py` ensures the assistant message content is never empty before tool-call responses are processed (implementation detail for the `agent.py` author to resolve via `llm.bind_tools` or message post-processing).
- RAG context is trimmed to fit Cerebras context limits before being returned to the LLM.
- `CEREBRAS_MODEL` defaults to `llama-3.3-70b`.

### Confirmation criteria

- `get_llm()` returns `ChatCerebras` when `LLM_PROVIDER=cerebras`.
- `get_llm()` returns `ChatOpenAI` (with Cerebras base URL) when `LLM_PROVIDER=openai-compat`.
- Tool-calling smoke test with a mocked Cerebras response (including an empty-content case) completes without exception.
- No live Cerebras API calls in CI — `FakeLLM` or `MagicMock` used in tests.

---

## Affected Layers / Repos

| Layer | Repo | Impact |
|---|---|---|
| middle-core | nickpclarke/middle-core | `llm.py`, `requirements.txt`, config; issues #17, #18 |
| frontend-core | nickpclarke/frontend-core | No impact — LLM key never reaches this layer (ARC-ADR-003) |
| backend-core | nickpclarke/backend-core | No impact |

---

## Known Caveats — Cerebras Tool Calling

1. **Empty-content tool-call bug:** Cerebras may return an assistant message with `content: ""` or `content: null` in tool-calling responses. LangChain's message serialization may raise on this. Mitigation: intercept the message post-generation and set content to a non-empty string (e.g., `" "`) before passing to LangGraph.
2. **Context window:** `llama-3.3-70b` on Cerebras has a smaller effective context window than GPT-4 class models. RAG chunks must be trimmed (e.g., top-3 chunks, max 500 tokens each) before synthesis.
3. **Rate limits:** Cerebras free-tier rate limits may throttle concurrent tool calls. Monitor and add retry logic with exponential backoff in `backend_client.py`.
4. **Model availability:** Cerebras model lineup evolves; `CEREBRAS_MODEL` must be configurable to allow model swaps without code changes.

---

## Pros and Cons of the Options

### Option 1 — ChatCerebras primary + OpenAI-compat fallback (proposed)

**Pros:** Single API key for both paths; no additional vendor; fallback is zero-config for the operations team.

**Cons:** `langchain-cerebras` adds a dependency; fallback uses `langchain-openai` pointing at a third-party base URL — version compatibility must be verified.

### Option 2 — ChatCerebras only

**Pros:** Simpler; one LangChain integration class.

**Cons:** No mitigation path for the empty-content bug beyond message post-processing; any tool-calling regression requires a code change to switch providers.

### Option 3 — OpenAI directly as primary

**Cons:** Violates the user's locked decision to use Cerebras as primary.

### Option 4 — Anthropic Claude as primary

**Cons:** Different SDK, different tool-calling format, different rate limits; violates the user's locked decision.

---

## Positive Consequences (if Option 1 accepted)

- Cerebras is the default path (cost-efficient, fast inference).
- Operational fallback requires only an env var change — no deployment change.
- `langchain-cerebras` + `langchain-openai` both maintained by the LangChain ecosystem.

## Negative Consequences (if Option 1 accepted)

- Two LangChain LLM integrations to maintain (`langchain-cerebras` + `langchain-openai`).
- Empty-content bug requires active mitigation code in `agent.py` or a custom message post-processor.

---

## Related Decisions

- **ARC-ADR-003:** No LLM key in browser — the complementary constraint that keeps the Cerebras key in middle-core only.
- **ARC-ADR-005:** backend-core OpenAPI contract — the tools that the LLM calls are defined against this contract.

---

## Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-25 | Scrum Master (hub decomposition) | Initial proposed ADR stub |
