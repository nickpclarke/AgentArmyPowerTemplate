# ARC-ADR-013 — Authorization Model: Per-Connection RBAC + Role Taxonomy (extends ARC-ADR-002)

| Field | Value |
|---|---|
| ID | ARC-ADR-013 |
| Status | Proposed |
| Date | 2026-05-25 |
| Deciders | Architecture Review (with `security-architect` input); HITL — pending hub owner |
| Supersedes | — |
| Superseded by | — |
| Tags | authz, rbac, uda, connections, roles, governance, backend-core, security |

---

## Context and Problem Statement

ARC-ADR-002 settled *coarse* authorization: a forwarded JWT carries a **`roles`** claim
(values `reader` / `contributor` / `admin`), and backend-core's `require_roles` enforces it **once** as
the single source of truth. That answers "may this principal call this *endpoint*?" — it does **not**
answer "may this principal use *this specific UDA connection*?"

The UDA (ARC-ADR-009) is becoming a multi-connection platform: a connection registry where ArcadeDB,
BigQuery, Postgres, and object-store connections coexist. Authorization is no longer one-dimensional. A
principal who is globally a `reader` should not automatically be able to **read/test/query every
connection** — a finance BigQuery connection and a public-docs ArcadeDB connection demand different
access. backend-core **#48** needs per-connection authorization: who may **use**, **test**, **query**,
and **administer** *which* connection — and how that composes with the existing global `roles` claim.

The decision to be made is: **how do we extend ARC-ADR-002's global role model to per-connection
authorization — the role taxonomy at the connection grain, *where* the per-connection grant lives
(an allowed-roles attribute on the connection vs an ownership model vs an external policy engine), and
how it composes with the global `roles` claim — while keeping backend-core the single authoritative
RBAC gate?**

Decided late, per-connection access becomes ad-hoc checks scattered across connector code, the role
taxonomy fragments (does "query" equal "use"?), and the single-source-of-truth principle ARC-ADR-002
established erodes. Decided early, one connection authorization model — one taxonomy, one enforcement
point — governs the whole connection registry.

---

## Decision Drivers

| # | Driver |
|---|---|
| D1 | **Single authoritative gate** (inherits ARC-ADR-002 D1) — per-connection authz is enforced **once in backend-core**, never re-checked or pre-decided in middle-core/frontend-core. |
| D2 | **Composes with the global `roles` claim** — the existing `reader`/`contributor`/`admin` claim (key `roles`, ARC-ADR-002) is the principal's *identity*; the per-connection grant scopes *which connections* those abilities apply to. |
| D3 | **Clear connection-grain taxonomy** — distinct, MECE verbs: who may **use** (open), **test** (validate config/creds), **query** (read data), and **administer** (edit/rotate/delete) a connection. |
| D4 | **Least privilege by default** — a connection is **not** readable by everyone with a global `reader` claim; access is an explicit grant, defaulting to deny. |
| D5 | **Auditable & manageable** — grants are inspectable and changeable through the connection registry/governance plane, and decisions are logged (no secret/credential in the audit trail). |
| D6 | **Bounded complexity** — the model must not require standing up policy infrastructure before the platform needs it; it should be the smallest thing that satisfies D1–D4 and can grow. |

---

## Considered Options

1. **Connection-scoped `allowedRoles` attribute (recommended seed)** — each connection in the registry
   carries an `allowedRoles` (and optionally per-verb) attribute; backend-core authorizes a request by
   intersecting the principal's global `roles` (ARC-ADR-002) with the connection's allowed set, per the
   verb (use/test/query/admin). Pure extension of `require_roles` — no new infra, data lives on the
   connection record.
2. **Ownership model** — each connection has an **owner** (the creating principal) plus a small grant
   list the owner manages (owner can use/test/query/admin and grant others). Authorization is
   "owner OR explicitly granted." More intuitive for self-service connection creation; adds
   ownership/transfer/grant lifecycle to manage.
3. **External policy engine** — express connection authorization as policies in a dedicated engine
   (e.g. OPA/Rego or Cedar); backend-core calls the engine (or an embedded evaluator) at the gate.
   Most expressive and future-proof (ABAC, conditions, multi-tenancy); heaviest to operate and risks
   moving the authoritative decision *out* of backend-core unless embedded carefully (tension with D1).

---

## Decision Outcome

**To be decided.** This is an **HITL** decision — the Architecture Review (or hub owner) must choose,
because extending the RBAC model is a governance-and-security posture call (least-privilege strictness,
self-service vs central grant, build-vs-adopt a policy engine) with long-lived consequences, not a
mechanical one.

### Recommendation note (not a decision)

Lean **Option 1 (connection-scoped `allowedRoles`) as the seed**, designed so Option 2 (ownership) and
Option 3 (policy engine) remain reachable later:

- **Extend, don't replace, ARC-ADR-002** (D2): keep the global `roles` claim (key `roles`, values
  `reader`/`contributor`/`admin`) as the principal's identity; add the per-connection `allowedRoles`
  grant as the *scope*. Authorization = `principal.roles ∩ connection.allowedRoles[verb]` — a direct,
  testable extension of `require_roles`, enforced in backend-core (D1).
- **Pin a MECE verb taxonomy** (D3): **use** (open the connection) ⊃-free of **test** (validate
  config/creds) ⊃-free of **query** (read data via the connection) ⊃-free of **admin** (edit/rotate-
  secret/delete) — mapping `admin` to the destructive verbs that already require `admin` + HITL
  (ARC-ADR-006). Define these once so connector code never invents its own.
- **Default deny** (D4): a connection grants no access implicitly; a global `reader` sees only
  connections whose `allowedRoles[query]` includes `reader`. This is the least-privilege correction to
  "global reader ⇒ reads everything."
- **Keep it inside backend-core** (D1/D6): the intersection check lives at the gate, beside
  `require_roles` — no external engine yet. This is also the principal dimension ARC-ADR-012's cache key
  must encode (D2 there) so cached reads never cross authz boundaries.
- **Leave the door open**: model `allowedRoles` as connection data so an **ownership** layer (Option 2)
  can later set/transfer it, and a **policy engine** (Option 3) can later evaluate it — adopt those only
  when self-service or ABAC/multi-tenancy (a Horizon backlog item) actually demands them.

A spike (`security-architect`) validating the `roles ∩ allowedRoles[verb]` model against the existing
`require_roles` path, and confirming the verb taxonomy covers #48's use/test/query/admin scenarios,
would settle Option 1 vs the heavier ownership/policy options.

---

## Affected Layers / Repos

| Layer | Repo | Impact |
|---|---|---|
| backend-core | nickpclarke/backend-core | Per-connection authz #48 — connection registry `allowedRoles`, the `roles ∩ allowedRoles[verb]` gate beside `require_roles`, verb taxonomy, default-deny, audit log |
| middle-core | nickpclarke/middle-core | Agent tools that open/query connections inherit the forwarded JWT's grants; **no** authz re-check (ARC-ADR-002 D1) — may read claims for UX only |
| frontend-core | nickpclarke/frontend-core | Connection-management UI surfaces only connections the principal may see; no enforcement (thin proxy) |
| (infra) | hub templates | Governance-plane / connection-registry conventions; audit-log format (no credentials in the trail) |

---

## Pros and Cons of the Options

### Option 1 — Connection-scoped `allowedRoles` attribute (recommended)

**Pros:**
- Pure extension of ARC-ADR-002's `require_roles` — minimal new code, keeps the single authoritative gate (D1).
- No new infrastructure; the grant is connection data, easy to inspect and test.
- Composes cleanly with the global `roles` claim; supplies the principal dimension ARC-ADR-012's cache needs.

**Cons:**
- Coarser than ABAC — no per-row or conditional access (acceptable at this stage).
- Without an ownership/grant UI, editing `allowedRoles` is an admin operation; self-service comes later.

### Option 2 — Ownership model

**Pros:**
- Intuitive for self-service connection creation; owner manages their own grant list.

**Cons:**
- Adds ownership lifecycle (transfer, orphaned connections, owner-leaves) to design and govern.
- Still needs a verb taxonomy underneath; ownership alone doesn't define use/test/query/admin.

### Option 3 — External policy engine

**Pros:**
- Most expressive (ABAC, conditions, multi-tenancy); future-proof for governance growth.

**Cons:**
- Heaviest ops surface; risks moving the authoritative decision out of backend-core unless embedded (tension with D1).
- Premature for the current connection grain (D6) — over-engineering before the need is proven.

---

## Related Decisions

- **ARC-ADR-002:** JWT-forwarding auth contract — this ADR **extends** its global `roles` model (claim key `roles`, values `reader`/`contributor`/`admin`) to the per-connection grain; the single-authoritative-gate principle (D1) is inherited unchanged.
- **ARC-ADR-005:** backend-core OpenAPI contract — the connection endpoints (#48) whose access this model gates.
- **ARC-ADR-006:** HITL for destructive ops — connection `admin` verbs (delete/rotate) map to the existing `admin`-required + HITL destructive path.
- **ARC-ADR-009:** Canonical data model — `Connection` is a modeled object; `allowedRoles` is a governance attribute on it.
- **ARC-ADR-011** (proposed): Runtime secret-resolution — *which secret* a connection resolves (ADR-011) is orthogonal to *who may use* the connection (this ADR); together they bound a connection's trust.
- **ARC-ADR-012** (proposed): Read-query caching — the per-connection principal/role dimension defined here is what the cache key must encode to prevent auth-varying leakage.
- **Horizon — Multi-tenancy / data-isolation boundary** (ADR-BACKLOG) — if tenant-level isolation lands, it likely promotes this model toward Option 3 (policy engine).

---

## Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-25 | architect-reviewer (forward ADR backlog) | Initial proposed stub — options open, HITL decision pending |
