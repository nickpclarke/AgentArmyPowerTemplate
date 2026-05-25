# ARC-ADR-006 — HITL for Destructive Ops (delete_source: admin role + renderAndWaitForResponse)

| Field | Value |
|---|---|
| ID | ARC-ADR-006 |
| Status | Accepted |
| Date | 2026-05-25 |
| Deciders | Architecture Review; accepted by hub owner 2026-05-25 |
| Supersedes | — |
| Superseded by | — |
| Tags | hitl, security, copilotkit, middle-core, frontend-core, delete, rbac |

---

## Context and Problem Statement

The CopilotKit agent in middle-core includes a `delete_source` tool that calls `DELETE /api/v1/sources/{id}` on backend-core. This is a **destructive, irreversible operation** — a deleted knowledge source and its associated vectors/objects cannot be recovered without re-ingestion.

Two HITL patterns exist in the AgentArmy platform:

1. **ARC-ADR-001 pattern** — a GitHub Issue is created as a Decision Artifact on the board; a human or AI app closes the issue to unblock work. This is designed for **asynchronous, board-level architectural decisions**.
2. **CopilotKit `renderAndWaitForResponse` pattern** — the agent pauses mid-run and renders a custom UI confirmation card in the chat; the user clicks "Confirm" or "Cancel" in the browser before the agent proceeds. This is designed for **synchronous, in-session user confirmations**.

The decision to be made is: **which HITL pattern governs the `delete_source` tool, and what are the precise preconditions (role check, confirmation UI) that must be satisfied before the delete is executed?**

---

## Decision Drivers

| # | Driver |
|---|---|
| D1 | Destructive operations must require explicit user confirmation — the agent must not delete without an acknowledgment. |
| D2 | The confirmation must be **synchronous and in-session** — a user asking the copilot to delete a source expects to confirm or cancel in the same conversation turn. |
| D3 | RBAC enforcement stays in backend-core — only admin-role JWTs are accepted by `DELETE /api/v1/sources/{id}`. |
| D4 | A non-admin user asking to delete a source should receive a clear permission-denied message, not a confusing 403 from backend-core. |
| D5 | The confirmation UI must clearly identify what will be deleted (source name, ID, estimated object count). |

---

## Considered Options

1. **CopilotKit `renderAndWaitForResponse` + admin role pre-check in tools.py** (proposed) — the tool pre-checks the user's role claim from the JWT; if not admin, returns a permission-denied message without calling backend-core; if admin, renders a confirmation card and waits for user approval before calling the delete endpoint.
2. **No HITL — call delete directly after admin RBAC check** — trust backend-core's 403 response as the sole guard; no confirmation UI.
3. **ARC-ADR-001 GitHub Issue pattern** — create a Decision Artifact on the hub board and wait for it to be closed before proceeding with the delete.
4. **Soft delete only** — middle-core never calls the hard delete endpoint; all deletes are soft (marked inactive) and require a separate admin batch process.

---

## Decision Outcome

**To be decided.** The Architecture Review recommends Option 1 as the correct pattern for in-session destructive operations: `renderAndWaitForResponse` provides the synchronous user-facing confirmation, while the admin role pre-check prevents non-admin users from ever reaching the confirmation step.

### Proposed decision: Option 1 — renderAndWaitForResponse + admin pre-check

**In `tools.py` (`delete_source` tool):**
1. Extract the user's role from the JWT claims (decoded in `app.py` and injected into the LangGraph run config).
2. If role is not `admin`: return a structured error message to the LLM ("Permission denied: admin role required to delete sources."). Do not call backend-core.
3. If role is `admin`: invoke `renderAndWaitForResponse` with a confirmation card showing source name, source ID, and estimated object count (fetched from `list_sources` if available).
4. If user clicks "Confirm": call `BackendClient.delete_source(source_id)` with the forwarded admin JWT. Return success/failure to the LLM.
5. If user clicks "Cancel" (or times out): return a cancellation message. Do not call backend-core.

**In `app/api/copilotkit/route.ts` (frontend-core):**
- The confirmation card is rendered via CopilotKit's `renderAndWaitForResponse` generative UI hook.
- Card must show: "Are you sure you want to delete source '{name}' ({id})? This action cannot be undone."
- Two buttons: "Delete permanently" (confirm) and "Cancel".

### Confirmation criteria

- A reader-role user asking to delete a source receives a permission-denied message; backend-core is never called.
- An admin-role user asking to delete a source sees the confirmation card before any delete is executed.
- Clicking "Cancel" leaves the source intact; backend-core `DELETE` is not called.
- Clicking "Delete permanently" calls `DELETE /api/v1/sources/{id}` with the admin JWT and returns a success message.
- The test suite asserts all four paths: non-admin denied, admin confirmed, admin cancelled, backend error handled.

---

## Affected Layers / Repos

| Layer | Repo | Impact |
|---|---|---|
| middle-core | nickpclarke/middle-core | `tools.py` `delete_source` tool; JWT role extraction in `app.py`; issues #17, #20 |
| frontend-core | nickpclarke/frontend-core | Confirmation card component rendered via `renderAndWaitForResponse`; issue #17 (Phase 3) |
| backend-core | nickpclarke/backend-core | No change — `DELETE /api/v1/sources/{id}` already requires admin role; issue #19 confirms this |

---

## Pros and Cons of the Options

### Option 1 — renderAndWaitForResponse + admin pre-check (proposed)

**Pros:**
- Synchronous confirmation — user sees and acts on the confirmation in the same conversation turn.
- Admin pre-check prevents non-admin users from ever reaching the confirmation step (better UX than a raw 403).
- CopilotKit's `renderAndWaitForResponse` is purpose-built for this pattern — no custom infrastructure.

**Cons:**
- Role extraction from JWT in `tools.py` creates a secondary RBAC check (primary is in backend-core). This is intentional for UX but must be kept in sync with backend-core's role model.
- If the JWT role claim format changes, both `app.py` (extraction) and `tools.py` (check) must be updated.

### Option 2 — No HITL

**Cons:**
- An accidental "delete all sources" from a misunderstood prompt would execute immediately.
- Violates the plan's stated requirement: "destructive ops need admin + HITL confirmation."

### Option 3 — ARC-ADR-001 GitHub Issue pattern

**Cons:**
- Asynchronous — the user would need to go to GitHub, close an issue, and come back to the chat. Unacceptable UX for an in-session conversational action.
- ARC-ADR-001 is designed for architectural decisions, not runtime user confirmations.

### Option 4 — Soft delete only

**Cons:**
- Changes the backend-core contract (soft delete endpoint does not currently exist).
- Adds complexity to backend-core without a clear benefit over HITL confirmation.

---

## Positive Consequences (if Option 1 accepted)

- Destructive operations are guarded by two independent gates: UX pre-check (role) + explicit user confirmation (HITL).
- The confirmation pattern is reusable for other future destructive operations (bulk delete, purge, etc.).

## Negative Consequences (if Option 1 accepted)

- Role claim extraction in middle-core creates a soft dependency on the JWT claim schema — must be documented.
- `renderAndWaitForResponse` timeout behavior must be specified (what happens if the user never responds?).

---

## Related Decisions

- **ARC-ADR-001:** HITL Decision Artifacts (board-level async decisions) — distinct from this synchronous in-session pattern.
- **ARC-ADR-002:** JWT-forwarding auth contract — governs how the admin JWT reaches backend-core.
- **ARC-ADR-005:** backend-core OpenAPI contract — the `DELETE /api/v1/sources/{id}` endpoint definition.

---

## Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-25 | Scrum Master (hub decomposition) | Initial proposed ADR stub |
