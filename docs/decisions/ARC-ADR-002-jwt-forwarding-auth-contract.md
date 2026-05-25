# ARC-ADR-002 — JWT-Forwarding Auth Contract (frontend-core → middle-core → backend-core)

| Field | Value |
|---|---|
| ID | ARC-ADR-002 |
| Status | Accepted |
| Date | 2026-05-25 |
| Deciders | Architecture Review; accepted by hub owner 2026-05-25 |
| Supersedes | — |
| Superseded by | — |
| Tags | auth, jwt, copilotkit, middle-core, frontend-core, backend-core, security |

---

## Context and Problem Statement

The CopilotKit generative-UI initiative introduces a three-hop request path:

1. A signed-in user's browser (frontend-core) opens a CopilotKit session.
2. The Next.js API route (`/api/copilotkit`) forwards the request to the middle-core Python agent (`/copilotkit`).
3. The middle-core agent calls backend-core REST endpoints (`/api/v1/*`) to execute tools on behalf of the user.

At each hop, backend-core must be able to enforce its existing RBAC policy (`require_principal` in `app/auth.py`) — without modification. This requires that the user's JWT reaches backend-core unchanged from the original token issued to the browser.

The decision to be made is: **how should the JWT be carried across the three layers, and what contract governs its format, lifetime, and forwarding fidelity?**

Without a documented contract, each layer could interpret the JWT differently, leading to auth failures, silent permission elevation, or debugging nightmares when RBAC gates reject unexpected token shapes.

---

## Decision Drivers

| # | Driver |
|---|---|
| D1 | RBAC must be enforced **once**, in backend-core — no re-checking in middle-core or frontend-core. |
| D2 | The user's JWT must reach backend-core **unchanged** — no re-signing, no claims augmentation, no token exchange. |
| D3 | The contract must be implementable without new auth infrastructure in middle-core (no token validator, no OAuth server). |
| D4 | The contract must be consistent with the existing `require_principal` implementation in `app/auth.py`. |
| D5 | The contract must be auditable: the JWT flow should be visible in logs (token type, not value) and verifiable in tests. |

---

## Considered Options

1. **Pass-through Bearer forwarding** (proposed) — frontend-core attaches the JWT as `Authorization: Bearer <token>`; each downstream layer reads it from the inbound request header and forwards it unchanged in the outbound request header.
2. **Token exchange** — middle-core exchanges the user's JWT for a service-level token with embedded user claims before calling backend-core.
3. **mTLS service identity + user claim header** — middle-core authenticates to backend-core via mTLS and passes the user identity as a separate `X-User-ID` header.
4. **API key for service-to-service + no user token** — middle-core authenticates with a shared API key; RBAC is pre-checked in middle-core before calling backend-core.

---

## Decision Outcome

**Accepted 2026-05-25 — Option 1 (pass-through Bearer forwarding).** The zero-infrastructure path consistent with the existing `require_principal` implementation. Implementation may proceed in all three layers.

### Decision: Option 1 — Pass-through Bearer forwarding

- frontend-core: reads the signed-in user's JWT from the session; attaches it to the `/api/copilotkit` route request to middle-core as `Authorization: Bearer <jwt>`.
- middle-core: reads the inbound `Authorization` header; injects the token into the LangGraph run config; `backend_client.py` attaches it as `Authorization: Bearer <jwt>` on every outbound request to backend-core.
- backend-core: `require_principal` validates the token as-is; no changes to `app/auth.py`.
- The JWT is **never logged** (only `Bearer` type confirmed in debug logs); **never stored** in middle-core beyond the request lifetime.

### Confirmation criteria

- A valid reader JWT forwarded through the three-hop path returns 200 on `GET /api/v1/search`.
- A reader JWT returns 403 on `POST /api/v1/ingest` (contributor required).
- An admin JWT is required for `DELETE /api/v1/sources/{id}` (HITL delete path).
- A request with no JWT returns 401 at backend-core.
- middle-core rejects requests that arrive at `/copilotkit` without a bearer token (401) — does not forward unauthenticated requests to backend-core.

### Concrete claim shape (backend-core authoritative)

Read from backend-core `app/auth.py` + `app/config.py`. middle-core/frontend-core pre-checks must bind to this, not to guessed "common shapes":

- **Role claim key:** `roles` (default — `settings.role_claim`, env `ROLE_CLAIM`). If absent, backend falls back **in order** to `role` → `scp` → `scope`.
- **Value format:** JSON array (`"roles": ["admin","contributor"]`) **or** space/comma-separated string (`"roles": "admin contributor"`); both parse to a role set (`_roles_from_claims`).
- **Role values:** `reader`, `contributor`, `admin` (`settings.reader_role` / `contributor_role` / `admin_role`; env-overridable).
- **Enforcement:** `require_roles(*roles)` → `principal.roles.intersection(roles)`; empty → HTTP 403. `DELETE /api/v1/sources/{id}` requires `admin` (see [ADR-006](ARC-ADR-006-hitl-destructive-ops.md)).
- **Subject:** derived from `sub` → `oid` → `client_id`.

A middle-core admin pre-check (e.g., the ADR-006 delete confirmation) reads the **`roles`** claim and treats the user as admin **iff `"admin"` is in the set**. These are the **defaults** — a non-default issuer config (`ROLE_CLAIM` / `ADMIN_ROLE`) overrides them, so confirm backend-core's env if it isn't running defaults.

---

## Affected Layers / Repos

| Layer | Repo | Impact |
|---|---|---|
| frontend-core | nickpclarke/frontend-core | Must read session JWT and attach to `/api/copilotkit` request; issues #12, #13 |
| middle-core | nickpclarke/middle-core | Must extract inbound JWT and inject into LangGraph run config + `backend_client.py`; issues #17, #19, #22 |
| backend-core | nickpclarke/backend-core | Must accept forwarded JWT in `require_principal`; no code change expected; issue #19 |

---

## Pros and Cons of the Options

### Option 1 — Pass-through Bearer forwarding (proposed)

**Pros:**
- Zero new infrastructure: no token exchange service, no mTLS setup.
- Consistent with existing `require_principal` implementation — backend-core requires no changes.
- Auditable: JWT lifetime and claims are controlled by the original issuer; no claims augmentation risk.
- Testable: mock the JWT value in unit tests; integration tests verify RBAC responses.

**Cons:**
- middle-core receives the user's JWT — it must be treated as a secret in memory (not logged, not persisted).
- If the JWT expires mid-agent-run, backend-core returns 401 mid-tool-call — middle-core must surface this gracefully.
- Token format is tightly coupled to backend-core's validator — any change to the auth scheme requires coordinated updates across all three layers.

### Option 2 — Token exchange

**Pros:** middle-core has a stable, long-lived service token; user identity is re-attested at each hop.

**Cons:** requires a token exchange service (new infrastructure); adds latency; couples all layers to the exchange service's availability.

### Option 3 — mTLS service identity + user claim header

**Pros:** service-to-service auth is cryptographically strong.

**Cons:** requires certificate infrastructure; `X-User-ID` header is trivially forgeable without additional validation; backend-core would need new auth code.

### Option 4 — API key for service-to-service

**Pros:** simple to implement.

**Cons:** RBAC cannot be enforced per-user in backend-core — all middle-core requests would share the API key's permissions, violating the principle that RBAC is single-sourced in backend-core.

---

## Positive Consequences (if Option 1 accepted)

- RBAC remains single-sourced in backend-core — no duplication or drift.
- No new infrastructure required for the CopilotKit initiative.
- Auth behavior is fully testable at each layer boundary independently.

## Negative Consequences (if Option 1 accepted)

- middle-core holds the user JWT in memory for the duration of each tool-call chain — security review required (ARC-ADR-003 governs the browser-side boundary; a separate review of middle-core memory hygiene is recommended).
- JWT expiry mid-run must be handled gracefully — middle-core should surface a user-friendly error rather than a raw 401 from backend-core.

---

## Related Decisions

- **ARC-ADR-001:** HITL Decision Artifacts — the pattern for surfacing this decision point if the option cannot be agreed upon by the implementing agents.
- **ARC-ADR-003:** No LLM key in browser — the complementary browser-side security boundary.
- **ARC-ADR-005:** backend-core OpenAPI contract consumed by middle-core tools — the contract that governs what endpoints middle-core calls with the forwarded JWT.
- **ARC-ADR-006:** HITL for destructive ops — governs the `delete_source` tool, which uses the forwarded admin JWT.

---

## Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-25 | Scrum Master (hub decomposition) | Initial proposed ADR stub |
