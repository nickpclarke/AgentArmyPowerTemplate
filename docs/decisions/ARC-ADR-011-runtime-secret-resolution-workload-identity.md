# ARC-ADR-011 — Runtime Secret-Resolution & Workload Identity: `env:` / `akv:` / OIDC Resolver Scheme + Precedence

| Field | Value |
|---|---|
| ID | ARC-ADR-011 |
| Status | Accepted |
| Date | 2026-05-25 |
| Deciders | Architecture Review; accepted by hub owner 2026-05-25 |
| Supersedes | — |
| Superseded by | — |
| Tags | secrets, identity, workload-identity, key-vault, oidc, wif, managed-identity, security, deployment |

---

## Context and Problem Statement

The platform already *lives* a layered secret-resolution pattern; it has never been written down as a
contract. Three distinct credential planes are in play, each with a different trust model:

1. **Local / CI / sandbox** — secrets arrive as **`env:`** values. ArcadeDB passwords are bridged from
   Azure Key Vault into GitHub Actions secrets (and into a runtime channel — `ARCADEDB_PASSWORD` /
   `ARCADEDB_PASSWORD_FILE`, see [arcadedb-secret-hardening.md](../arcadedb-secret-hardening.md)).
   Sandboxed spokes have no path back to the hub, so the secret is *injected*, not *fetched*.
2. **Production runtime** — services resolve secrets via an **`akv:`** scheme (a Key Vault reference,
   e.g. `akv:akv01-agentarmy/arcadedb-password`) backed by an Azure **managed identity** — the service
   reads the secret at runtime with its own identity, no static credential on disk. backend-core's
   resolver (`app/secrets.py`) already understands the `file:` / `env:` / `akv:` URI schemes.
3. **Deploy time** — workflows authenticate to the cloud via **OIDC / federated identity (WIF)** — no
   long-lived service-account key in the repo (the GCP Cloud Run pipeline already does keyless WIF;
   the Azure side uses federated credentials on an app registration).

The decision to be made is: **what is the canonical secret-resolver scheme and resolution precedence
across every spoke and cloud — the URI schemes (`file:` / `env:` / `akv:` and any addition), the
order they are tried, and how strictly the `env:`-for-CI / `akv:`-managed-identity-for-prod / OIDC-WIF-
for-deploy split is mandated versus left to each spoke?**

Decided late, each spoke invents its own resolver and precedence; a prod service silently falls back to
an `env:` value a developer left set; a connection credential leaks because one spoke logged the
resolved value; and "no static creds" erodes into per-repo PATs. Decided early, every layer shares one
resolver contract, one precedence, and one rule that prod identity is always federated/managed.

---

## Decision Drivers

| # | Driver |
|---|---|
| D1 | One resolver scheme — the same `file:` / `env:` / `akv:` URI vocabulary (`app/secrets.py`) understood identically in every spoke, so a connection or service config is portable across local/CI/prod. |
| D2 | A **deterministic precedence** — when more than one scheme could supply a value, the order is fixed and documented (e.g. explicit `akv:` ref > `*_FILE` > `env:`), never accidental. |
| D3 | **No static long-lived credentials in prod or deploy** — prod runtime uses managed identity (`akv:`), deploy uses OIDC/WIF; static keys exist only as the local/CI convenience path. |
| D4 | Must fit the secret-bridging already done in practice (Key Vault → GitHub secrets → runtime channel) and the hardening rules (`*_FILE` wins over `*`; never log the value; rotate on exposure). |
| D5 | Cross-cloud reality — Azure (Key Vault + managed identity + federated app reg) and GCP (Secret Manager + WIF) must both satisfy the same *abstract* scheme without forcing one cloud's primitive on the other. |
| D6 | The resolved secret must **never** enter telemetry, logs, or PR comments — interlocks with ARC-ADR-010's redaction rule (D6) and ADR-002's "never log the JWT". |

---

## Considered Options

1. **Single shared resolver library + strict prod-identity mandate (recommended seed)** — promote
   `app/secrets.py`'s `file:`/`env:`/`akv:` resolver into a shared, per-language contract every spoke
   adopts, with a fixed precedence and a **hard rule**: prod must resolve via `akv:` + managed identity
   and deploy via OIDC/WIF; `env:`/static keys are permitted **only** in local/CI/sandbox. The hub owns
   the spec; spokes implement it in their language.
2. **Shared scheme, advisory identity posture** — standardize the URI schemes and precedence, but treat
   the "managed identity in prod / OIDC at deploy" rule as a strong recommendation each spoke may relax
   (e.g. a spoke on a cloud without easy managed identity may use a scoped static key in prod).
3. **Per-spoke resolver, hub publishes principles only** — no shared resolver code; the hub documents
   the `env:`/`akv:`/OIDC *intent* and the hardening rules, and each spoke builds its own resolver to
   fit its stack and cloud.

---

## Decision Outcome

**Accepted 2026-05-25 — Option 1: a single shared secret-resolver library + strict production-identity mandate — managed identity in prod, OIDC/WIF at deploy, static keys only in local/CI.** The HITL framing that produced this choice: This is an **HITL** decision — the Architecture Review (or hub owner) must choose,
because how strictly identity is standardized across spokes and clouds is a security-posture and
fleet-governance call with real cost/portability trade-offs, not a mechanical one.

### Recommendation note (not a decision)

Lean **Option 1** as the destination, reached pragmatically:

- **Ratify the existing scheme** (D1): `file:` (mounted secret, `*_FILE` shape) → `akv:` (Key Vault ref
  via managed identity) → `env:` (literal/injected) — the vocabulary `app/secrets.py` already speaks.
- **Pin one precedence** (D2): explicit `akv:`/`file:` reference wins over a bare `env:` literal, so a
  prod service can't silently pick up a stray developer `env:` value — fold this into the resolver, not
  per-call discipline. Mirror the hardening rule "`*_FILE` wins over `*`".
- **Make prod identity non-negotiable** (D3/D5): prod = `akv:` + managed identity (Azure) /
  Secret Manager + WIF (GCP); deploy = OIDC/WIF, never a committed key. Keep static `env:` keys scoped
  to local/CI/sandbox — exactly the bridging done today (Key Vault → GitHub secrets → runtime channel).
- **Abstract over cloud** (D5): the `akv:` scheme is the *interface*; a GCP spoke binds it to Secret
  Manager. Don't force Key Vault primitives into a GCP spoke — standardize the resolver contract, not
  the backing store.
- **Hard redaction rule (D6):** resolved values never enter logs/telemetry/PR comments — shared with
  ARC-ADR-010's redaction checklist and ADR-002's JWT-never-logged invariant.

Avoid **Option 3** (pure principles): it guarantees N divergent resolvers and N chances to leak. A
spike (`security-architect` + `azure-infra-engineer`) confirming the shared resolver + WIF/managed-
identity path on both Azure and one GCP spoke would settle Option 1 vs the advisory Option 2.

---

## Affected Layers / Repos

| Layer | Repo | Impact |
|---|---|---|
| backend-core | nickpclarke/backend-core | `app/secrets.py` resolver (`file:`/`env:`/`akv:`) is the seed; UDA connection credentials resolve through it; prod = managed identity |
| middle-core | nickpclarke/middle-core | LLM/connection-string secrets (e.g. ARC-ADR-008 memory store) resolve via the shared scheme; deploy via OIDC/WIF |
| frontend-core | nickpclarke/frontend-core | Server-side secrets (no browser secret per ARC-ADR-003) resolve via the scheme on its runtime |
| (infra) | hub templates | Key Vault / Secret Manager wiring; WIF + federated-credential bootstrap; GitHub-secret bridging convention; ACA secret-backed env vars |

---

## Pros and Cons of the Options

### Option 1 — Shared resolver + strict prod-identity mandate (recommended)

**Pros:**
- One resolver, one precedence, one identity posture — a config is portable local → CI → prod across spokes.
- "No static creds in prod/deploy" becomes enforceable, not aspirational; matches the WIF/managed-identity work already shipping.
- Single redaction chokepoint in the resolver (D6).

**Cons:**
- Per-language resolver implementations must be kept in lockstep (a shared spec to maintain).
- A spoke on a cloud with weak managed-identity support is forced to invest to comply.

### Option 2 — Shared scheme, advisory identity posture

**Pros:**
- Same portable URI vocabulary; lower compliance burden for awkward clouds.

**Cons:**
- "Advisory" prod-identity drifts toward static keys under deadline pressure — the exact risk D3 exists to kill.
- Inconsistent prod posture across spokes complicates security review.

### Option 3 — Per-spoke resolver, principles only

**Pros:** Each spoke fits its own stack/cloud with zero shared code to maintain.

**Cons:** N resolvers, N precedences, N redaction implementations — the divergence and leak surface this ADR exists to prevent; retrofitting a shared contract later is costlier.

---

## Related Decisions

- **ARC-ADR-002:** JWT-forwarding — same "never log the secret" discipline; the JWT is an in-memory secret, this ADR governs the *at-rest/at-config* secrets around it.
- **ARC-ADR-005:** backend-core OpenAPI contract — UDA endpoints whose connection credentials resolve via this scheme.
- **ARC-ADR-009:** Canonical data model — UDA `Connection` objects carry credential refs expressed in this resolver's `akv:`/`env:` vocabulary.
- **ARC-ADR-010:** Observability standard — its redaction rule (D6) references this secret model; collector/exporter endpoints resolve via this scheme.
- **ARC-ADR-013** (proposed): Per-connection RBAC — *who* may use a connection (authz) sits atop *which secret* the connection resolves (this ADR).
- **ARC-ADR-015** (backlog): Deployment & release-promotion — where managed identities/WIF federations are provisioned per environment.
- **arcadedb-secret-hardening.md** — the concrete hardening rules (`*_FILE` wins, never log, rotate on exposure) this resolver enforces.

---

## Revision History

| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 | 2026-05-25 | architect-reviewer (forward ADR backlog) | Initial proposed stub — options open, HITL decision pending |
