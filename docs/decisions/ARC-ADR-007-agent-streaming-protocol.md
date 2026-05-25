# ARC-ADR-007 — Agent Streaming Protocol (frontend-core ⇄ middle-core): SSE vs WebSocket vs CopilotKit-Native

| Field | Value |
|---|---|
| ID | ARC-ADR-007 |
| Status | Proposed |
| Date | 2026-05-25 |
| Deciders | Architecture Review (HITL — to be decided) |
| Supersedes | — |
| Superseded by | — |
| Tags | streaming, copilotkit, middle-core, frontend-core, sse, websocket, transport |

---

## Context and Problem Statement

The CopilotKit generative-UI initiative renders **incremental** output: LLM tokens stream into the
chat as they are generated, tool-call status updates appear mid-run, and `renderAndWaitForResponse`
cards ([ARC-ADR-006](ARC-ADR-006-hitl-destructive-ops.md)) interrupt and resume the stream. All of
this travels the path frontend-core (`/api/copilotkit` route) → middle-core (`/copilotkit` FastAPI
endpoint, middle-core #22) → LangGraph agent (#21), with the user JWT forwarded unchanged
([ARC-ADR-002](ARC-ADR-002-jwt-forwarding-auth-contract.md)).

Phase 0 (smoke test) can survive on request/response. **Phase 1 onward** (citation cards, ingest
progress, cockpit metrics — middle-core #20, frontend-core #15/#16/#18) needs a streaming transport.

The decision to be made is: **what wire transport carries the agent's streamed tokens, tool-status
events, and interrupt/resume signals between frontend-core and middle-core — and is that transport
chosen explicitly, or inherited from whatever CopilotKit's runtime defaults to?**

Decided late, this surfaces as proxy buffering bugs (a reverse proxy that buffers an SSE stream
breaks token streaming), Azure Container Apps (ACA) ingress timeout/idle-connection limits killing
long-lived sockets, and a frontend that can't cancel an in-flight agent run. Decided early, both
layers agree on one transport, its keep-alive/timeout behavior, its cancellation semantics, and how
the JWT rides it.

---

## Decision Drivers

| # | Driver |
|---|---|
| D1 | Tokens and tool-status events must reach the browser **incrementally**, with low first-token latency — not buffered until the run completes. |
| D2 | The transport must carry the forwarded user JWT and respect ARC-ADR-002 (token unchanged, single-source RBAC in backend-core). |
| D3 | It must support the CopilotKit interrupt/resume pattern (`renderAndWaitForResponse`) without a bespoke side-channel. |
| D4 | It must survive the **deployment topology**: ACA/ACI ingress, idle-connection and request timeouts, and any reverse proxy between the layers (no silent buffering). |
| D5 | The browser must be able to **cancel** an in-flight agent run (user clicks stop) and have middle-core actually abort the LangGraph run. |
| D6 | Prefer the path that adds the least bespoke transport code — lean on CopilotKit's runtime contract rather than re-implementing it, unless that contract is the constraint. |

---

## Considered Options

1. **CopilotKit-native transport (adopt the runtime's default; do not hand-roll)** — let the
   `CopilotRuntime` in the Next.js route and the CopilotKit Python SDK in middle-core negotiate the
   transport CopilotKit ships (today an HTTP streaming / SSE-style protocol over the GraphQL-ish
   runtime contract). We bind to CopilotKit's contract and configure the *deployment* (disable proxy
   buffering, set ingress timeouts) around it.
2. **Server-Sent Events (SSE) explicitly** — middle-core exposes a `text/event-stream` response;
   frontend-core's route streams it through. One-way server→client, simple, proxy-friendly *if*
   buffering is disabled; client→server (cancel, interrupt response) rides a separate POST.
3. **WebSocket** — a full-duplex socket between the Next.js route (or directly the browser, behind
   the JWT boundary) and middle-core. Native bidirectional flow for tokens *and* interrupt/cancel on
   one channel.

---

## Decision Outcome

**To be decided.** This is an HITL decision — the Architecture Review (or hub owner) must choose,
because the trade-off (lock-in to CopilotKit's evolving transport vs. control over an explicit
SSE/WebSocket contract) is a strategic coupling call, not a mechanical one.

### Recommendation note (not a decision)

Lean toward **Option 1 (CopilotKit-native)** as the default, *with an explicit fallback to Option 2
(SSE)* documented, because:

- D6 strongly favors not re-implementing a transport CopilotKit already negotiates end-to-end with
  generative UI and interrupt/resume built in — re-rolling it risks drift against the CopilotKit
  React hooks frontend-core already depends on (#14).
- The real risk is **deployment**, not protocol choice: whichever option wins, the binding decision
  is "disable response buffering on every hop and set ACA ingress idle-timeout > longest expected
  agent run," and confirm cancellation propagates to a LangGraph run abort.
- Option 3 (WebSocket) is the escape hatch *only if* CopilotKit's transport can't satisfy D5
  (cancel) or D4 (ACA timeouts) cleanly — adopt it deliberately, not by default, given its higher
  ops surface (sticky sessions, socket lifecycle, JWT-on-upgrade handling).

A spike (`spike-researcher`) over Phase 1 to confirm CopilotKit's current transport survives the ACA
ingress + any reverse proxy, with working token streaming and cancel, would settle Option 1 vs 2.

---

## Affected Layers / Repos

| Layer | Repo | Impact |
|---|---|---|
| frontend-core | nickpclarke/frontend-core | `/api/copilotkit` route streaming behavior; cancel/stop UI; #13, #15, #16, #18 |
| middle-core | nickpclarke/middle-core | `/copilotkit` endpoint streaming + run-cancellation handling in `app.py`/`agent.py`; #20, #21, #22, #32 |
| backend-core | nickpclarke/backend-core | No direct impact — backend-core is request/response behind middle-core (tool calls), not in the stream |

---

## Pros and Cons of the Options

### Option 1 — CopilotKit-native transport (recommended default)

**Pros:**
- Zero bespoke transport code; generative UI + interrupt/resume + cancel are part of the contract frontend-core's hooks already use.
- Stays in lockstep with the CopilotKit React side (#14) — no transport drift between the two layers.
- Consistent with ARC-ADR-003/004's "thin proxy in frontend-core" posture.

**Cons:**
- Couples the wire protocol to CopilotKit's roadmap — a transport change upstream is a forced migration.
- The transport is somewhat opaque; debugging streaming/proxy issues means reverse-engineering CopilotKit's framing.
- Must still solve the deployment problem (buffering, ACA timeouts) ourselves.

### Option 2 — Server-Sent Events (SSE) explicitly

**Pros:**
- Simple, well-understood, proxy-friendly (when buffering is off); trivially observable on the wire.
- One-way server→client maps cleanly to token streaming; full control over the event schema.

**Cons:**
- Client→server actions (cancel, `renderAndWaitForResponse` answers) need a second channel — more glue.
- We'd be hand-mapping CopilotKit's event model onto our SSE frames; risk of diverging from #14's hooks.
- Browsers cap concurrent SSE connections per origin (minor at our scale).

### Option 3 — WebSocket

**Pros:**
- Single full-duplex channel for tokens, interrupts, and cancel — cleanest fit for D3 + D5.
- No per-origin connection cap issues; lowest per-message overhead.

**Cons:**
- Highest ops surface: socket lifecycle, reconnection, sticky sessions on ACA, JWT presented on upgrade.
- ACA/proxy WebSocket support and idle-timeout behavior must be verified; harder to debug than HTTP.
- More bespoke code on both ends than Option 1.

---

## Related Decisions

- **ARC-ADR-002:** JWT-forwarding auth contract — whatever transport wins must carry the JWT unchanged and keep RBAC single-sourced in backend-core.
- **ARC-ADR-003:** No LLM key in browser — the streaming path keeps frontend-core a thin proxy; the LLM stays in middle-core.
- **ARC-ADR-004:** LLM provider = Cerebras — Cerebras token-streaming behavior and rate limits constrain D1 (first-token latency).
- **ARC-ADR-006:** HITL for destructive ops — `renderAndWaitForResponse` rides this transport (D3).
- **ARC-ADR-008** (proposed): Agent memory store — resumable threads and mid-stream interrupts interact with where thread state lives.
- **ARC-ADR-015** (backlog): Deployment & release-promotion model — the ACA vs ACI + ingress-timeout decision that D4 depends on.

---

## Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-25 | architect-reviewer (forward ADR backlog) | Initial proposed stub — options open, HITL decision pending |
