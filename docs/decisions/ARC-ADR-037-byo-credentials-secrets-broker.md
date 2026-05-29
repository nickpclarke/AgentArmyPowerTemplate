# ARC-ADR-037 — BYO-Credentials: a Secrets Broker for Abstracted Systems

| Field | Value |
|---|---|
| ID | ARC-ADR-037 |
| Status | Accepted |
| Date | 2026-05-29 |
| Deciders | Hub owner (Nicky Clarke) — accepted 2026-05-29 via HITL selector (chose Option A, Infisical CE) → **revised same day to Option C (Azure Key Vault) on self-host friction** |
| Supersedes | — (enables [ARC-ADR-036](ARC-ADR-036-abstraction-validation-distribution-service.md) at multi-system / multi-user scale) |
| Tags | secrets, credentials, byo-keys, secrets-broker, anti-corruption-layer, security, multi-tenant, openbao, infisical, azure-key-vault |

---

## Context and Problem Statement

Abstracting a real third-party system (GitHub, Jira, Linear, Stripe, …) **implies the user wants it abstracted and has granted the appropriate access**. Our MCP tools — generated against the canonical APIs ([ARC-ADR-036](ARC-ADR-036-abstraction-validation-distribution-service.md)) and proxied through backend-core — can only call those real producers with that system's credentials. So the platform needs a **place for users to register their keys/secrets per abstracted system**, under a firm principle: **raw keys stay server-side** — a broker issues scoped, short-lived credentials and the tools never hold the raw third-party key.

Today this is ad-hoc and operator-only: secrets live in Azure Key Vault `akv01-agentarmy`, resolved at runtime by `akv:` reference (e.g. `akv:GithubPAT`). That works for a single operator but offers no per-user / per-system onboarding, scoping, rotation, or audit as a first-class surface.

**Threat-model note (current vs. horizon):** the fleet today is **single-operator and trusted** (private, no untrusted collaborators). Hard multi-tenant isolation between *untrusted* users is a **design horizon, not today's threat** — which argues for adopting fast now with a documented upgrade path, rather than paying heavy multi-tenant ops cost prematurely.

## Decision Drivers

- **Keys stay server-side** — the broker issues scoped/short-lived credentials; tools proxy and never hold raw keys (extends the pattern the abstraction MCP already uses).
- **Fast to adopt** — the capability/tool cadence is aggressive ([[serve-capabilities-via-mcp]]); the credential surface must not be a multi-day yak-shave.
- **Open-source / self-hostable** preferred; must fit the Docker fleet + Azure (ACA, Entra, Key Vault).
- **Onboarding UX** — a real surface where a user registers a key for a system.
- **Don't hand-roll security** — prefer a battle-tested secrets platform over custom token/rotation/audit code (secure-by-default).
- **Multi-tenant isolation** — a driver, but weighted for the *horizon*, not the solo/trusted present.

## Considered Options

### Option A — Infisical Community Edition (MIT)  ← recommended
Self-hosted secrets platform: single Docker stack (Postgres + Redis + app), first-class Python SDK (`infisicalsdk` 1.x), REST API ideal for a thin registration endpoint, Org→Project→Environment→Path hierarchy that maps to per-user/per-system scoping, RBAC + audit in CE, Azure auth method.
- **Pros:** fastest to a working broker (an afternoon); MIT core; clean fit with the fleet's Docker/ACA pattern; the onboarding surface is a thin wrapper over its API so users never touch the vault; active project (weekly releases).
- **Cons:** tenant isolation is **RBAC/path-based, not cryptographic-namespace**; dynamic-secret engines are fewer than Vault/OpenBao (third-party API-key rotation is partly hand-coded); SSO (SAML/SCIM) is Enterprise-tier.

### Option B — OpenBao v2.5.4+ (MPL 2.0, Linux Foundation)
The truly-OSS fork of Vault. Hard multi-tenant **namespaces**, 50+ dynamic-secret engines, leased credentials with automatic TTL/revocation, mature audit, JWT/OIDC auth (exchange an Entra token for a scoped OpenBao token), Azure Key Vault as backing KMS.
- **Pros:** the "do it right" multi-tenant answer; cryptographic namespace isolation; dynamic secrets + leasing out of the box; no brokering logic to write; clean license (no Vault BSL trap).
- **Cons:** **operational weight** — HA Raft clustering, an unseal ceremony, namespace administration (~1–2 days setup + runbooks); `hvac` is Vault-branded (works, but won't track OpenBao-specific features); must run ≥2.5.4 to avoid the May-2026 cross-namespace CVEs.

### Option C — Azure Key Vault + a thin custom broker
Keep secrets in Key Vault (one vault per tenant, or `{userId}/{system}/` naming) and build a FastAPI broker that authenticates users, stores keys, and issues scoped short-lived tokens.
- **Pros:** zero new infra; native to the existing Azure/Entra footprint; fully managed store.
- **Cons:** you **own all the security-sensitive code** — token issuance, revocation, rotation, audit, onboarding UI. Research finding: this accumulates to roughly the same scope as deploying Infisical, but **without the community battle-testing** — i.e. the riskiest path per secure-by-default. No dynamic secrets (you implement leasing).

### Ruled out
- **HashiCorp Vault** — BSL 1.1 since 2023 (IBM-owned); the "no competing product" clause is a legal trap if credential-brokering ever becomes a sold feature. OpenBao removes this.
- **Doppler** — SaaS-only, no self-host, not a multi-tenant BYO-keys broker.
- **SOPS+age, Bitwarden/Vaultwarden** — static-secret stores, no runtime lease/scoped-credential issuance.
- **Teleport/Pomerium** — infra-access certs / identity proxy, not third-party key brokering.

## Decision Outcome

**Chosen: Option C — Azure Key Vault + a thin broker** (revised 2026-05-29). Option A (Infisical CE) was selected first via the HITL selector, but its self-host reality — a Postgres+Redis+app container plus an admin/project/machine-identity/client-secret bootstrap, compounded by a flaky local Docker engine — was real operational friction. We switched to **Azure Key Vault**: the broker API and the "raw keys stay server-side, inject server-side" contract are **identical** (only the storage backend changed), and it reuses the box's existing `DefaultAzureCredential` + `AZURE_KEYVAULT_URL` (the `akv:` resolver machinery) — **no container, no new dependency, no extra credentials**. Per-user keys are name-prefixed secrets (`cred-{user}-{system}`) in `akv01-agentarmy`.

Option C's original caveat ("you build all the broker code") proved minor here because the broker was already built backend-agnostic; only `store.py` swapped. **Tradeoffs accepted for the solo/trusted stage** ([[threat-model-no-forks]]): flat namespace + one shared vault (co-mingled with operator secrets), no per-user RBAC boundary. **Documented upgrade path** (unchanged): a dedicated per-tenant vault, then **OpenBao (Option B)** for cryptographic namespace isolation when *untrusted* multi-tenancy arrives. This honors velocity + "don't over-engineer for the horizon" + "don't hand-roll security."

## Consequences

- **Positive:** a real BYO-keys surface; tools receive scoped, short-lived credentials and never hold raw third-party keys; rotation + audit become first-class; the abstraction tools can finally call *real* producers per-user, not just mocks.
- **Negative / cost:** a new platform-tier service to run (Infisical: Postgres + Redis + app); isolation is RBAC/path-based until/unless we move to OpenBao; a backend-core broker layer to build (thin) + an onboarding endpoint.

## Implementation sketch (as built)

1. **No store to deploy** — reuse Azure Key Vault (`akv01-agentarmy`) via `DefaultAzureCredential` + `AZURE_KEYVAULT_URL`, the same machinery as `app/secrets.py`'s `akv:` resolver.
2. backend-core `/api/v1/credentials/*` (`app/credentials/`): a user registers a `{system}` key (auth via `require_roles`); it is stored as the KV secret `cred-{user}-{system}`; the raw key never returns to the client. `GET` lists registered system names (never values); `DELETE` removes.
3. `store.resolve(user, system)` is **server-side only** — backend-core injects the secret into the outbound call (option A). There is **no endpoint that returns a raw secret**.
4. Audit every register/delete (`audit.emit`); rotation = a new KV secret version. **Live-verified** end-to-end against `akv01-agentarmy` (put/list/resolve/delete).
5. The store is **backend-agnostic** — swapping to a dedicated vault or OpenBao later changes only `store.py`. Dev input surface (a small console UI / `/_dev` helper) is a follow-up as we iterate.
