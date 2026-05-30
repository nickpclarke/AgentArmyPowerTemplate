---
title: Credentials Broker as a Thin Bootstrap Container
type: design
status: draft
date: 2026-05-29
tags: [design, secrets, byo-credentials, bootstrap, dapr, container-tiering, ARC-ADR-037]
relates: [ARC-ADR-037, ARC-ADR-023, ARC-ADR-034, ARC-ADR-011]
---

# Credentials Broker as a Thin Bootstrap Container

Design note feeding an evolution of [[ARC-ADR-037]] (BYO-credentials secrets broker). Captures
(a) the prebuilt-product survey, (b) the bootstrap-container direction, (c) the honest scoping of
Dapr's role. The formal ADR decision is deferred until the Dapr scope below is chosen.

## Goal (owner's framing)

A **small, isolated, always-on localhost container** that is the credentials broker: it brings its
own onboarding **UI + web surface + security + secret-injection** "in one little moment" when dropped
into a fresh environment, then grows as **events come up / third parties are added** — i.e. a **thin
bootstrap layer** for rapid, safe human-or-agent access. Contract-mediated to backend-core so the
backend↔broker boundary rides the existing vendoring mechanism ([[ARC-ADR-034]]).

This **revises one explicit pro of [[ARC-ADR-037]]** — Option C was sold partly on *"zero new infra /
no container / no bootstrap."* A new driver (portable bootstrap primitive + fleet sequencing) now
outweighs that, so the "no container" consequence is being deliberately traded away.

## Tiering

Stateless by construction — all state lives in Azure Key Vault (`store.py` holds nothing). Per
[[ARC-ADR-023]] this is a clean **Function tier** container, like `jwt-introspect` / `hmac-verify`.

## Prebuilt survey (do we have to build it?)

Researched 2026-05-29. **Verdict: the plumbing is solved; the combination + AKV-as-store is not.**

| Layer | Prebuilt? | Best option | Catch |
|---|---|---|---|
| Store/retrieve in *our* AKV | ✅ | Dapr secrets sidecar (AKV component) | read-by-name only; no list/write |
| Egress injection ("app never sees the key") | ✅ | CyberArk Secretless Broker | secret source is Conjur, **not AKV** → 2nd service |
| BYO-key onboarding UI → writes our AKV | ❌ | *(custom everywhere)* | nobody ships this |
| All 3 in one container, AKV-backed | ❌ | — | doesn't exist as a product |

- Azure-native injectors **don't fit**: APIM Credential Manager is **OAuth-2.0-only** (can't inject a
  raw PAT/API key) and is a cloud service, not a localhost container; Azure Service Connector was
  **retired on ACA (2026-03-30)** and was deploy-time wiring only.
- **Watch-item:** Infisical **`agent-vault`** (April 2026, MIT) — single container, management UI +
  MITM HTTPS injection proxy, *purpose-built for agent credential brokering*. **Research-preview**
  quality and **AKV is not a backend** today → adopt-later, don't build on now. Strong validation that
  our direction is where the ecosystem is heading.
- The ~300 lines we already wrote (`store.py` + `console.html`) **are** the irreducibly-custom layer
  nobody sells. We are not reinventing a wheel; we built the only bespoke piece.

## Dapr's role — scoped honestly

Dapr (Distributed Application Runtime) runs as a **sidecar** exposing a localhost API for common
building blocks. Assessed against this broker:

- **Dapr *secrets* building block is a poor fit here.** It is read-by-name only; the broker needs
  list + write too, so those stay on the Azure SDK with the credential **in-process** regardless.
  Using Dapr secrets would offload `resolve()` only — *more* moving parts, not credential isolation.
- **Dapr's real fit for this vision is eventing/mesh, not secrets:** pub/sub + service-invocation
  (mTLS) — the "events come up / fleet sequencing" layer the bootstrap unit grows into.
- **Credential isolation comes from the *container*, not Dapr** — a standalone broker that is the
  sole KV-credential holder achieves the isolation goal directly.

### Prerequisites to run any Dapr locally
- Dapr CLI **not installed** (`dapr init` needed).
- Docker engine **wedged** (HTTP 500 degraded signature) — restart Docker Desktop (Troubleshoot →
  Restart) before Dapr's placement/redis containers can start. See [[reference_docker_engine_500_degraded]].

## Live fix already applied (2026-05-29)

`/api/v1/credentials/ui` wasn't pulling AKV: `DefaultAzureCredential` probed managed-identity (IMDS)
before the local `az` login, stalling ~25s → client timeout. Fixed in `app/credentials/store.py`
(`exclude_managed_identity_credential` + `exclude_workload_identity_credential` in dev). `/details`
now 200 with all 9 keys. **Same latent bug remains in `app/secrets.py:147`** (bare
`DefaultAzureCredential()` in the `akv:` resolver) — one-line consistent fix pending.

## Build options (pick scope for the formal ADR)

- **A — Standalone broker container, no Dapr (recommended).** Containerize the existing thin broker
  (UI + KV + inject) as a Function-tier image; the container is the isolation boundary; keep the SDK +
  the credential fix. Publishes its OpenAPI for backend-core to vendor. Smallest path to the goal.
- **B — A + Dapr eventing later.** Add Dapr pub/sub + service-invocation **when** "events come up" —
  the mesh layer, not secrets. Defer until there's an event to carry.
- **C — Dapr-secrets PoC for `resolve()` only.** Honest: marginal (read-only, doesn't isolate the
  credential). Only worth it if we want the resolve hot-path uniform across stores.

## Build status — Option C chosen (2026-05-29)

Owner picked **C**. Built, feature-flagged (default off; SDK path unchanged):
- `app/config.py`: `credentials_resolve_via_dapr` (off), `dapr_http_port` (env `DAPR_HTTP_PORT`),
  `dapr_secret_store` (`credstore`).
- `app/credentials/store.py`: `resolve()` branches to `_resolve_via_dapr()` when the flag is set —
  `GET http://127.0.0.1:{port}/v1.0/secrets/{store}/{name}`, optional `dapr-api-token` header, errors
  never embed the value. **Only `resolve()` is routed; list/register/delete stay on the SDK.**
- `dapr/components/credstore.yaml` (AKV secret store), `dapr/components/local-env.yaml` (envvar store
  for the dev SPN), `dapr/config.yaml`.
- `tests/test_credentials.py`: 3 mocked tests (URL shape, api-token + env-port precedence, no-leak on
  failure). **All 10 credentials tests pass** (no Docker/Dapr needed — httpx mocked).

### To actually run it (blocked on env, not code)
1. Restart Docker Desktop engine (Troubleshoot → Restart) — currently wedged (HTTP 500).
2. Install Dapr CLI + `dapr init`.
3. Export an SPN with KV "Get" on secrets: `AZURE_TENANT_ID` / `AZURE_CLIENT_ID` / `AZURE_CLIENT_SECRET`
   (avoids the same IMDS stall in Dapr's Azure auth), and `CREDENTIALS_RESOLVE_VIA_DAPR=true`.
4. `dapr run --app-id backend-core --dapr-http-port 3500 --resources-path ./dapr/components \
     --config ./dapr/config.yaml -- python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
5. A `resolve()` (e.g. an injected outbound call for `stripe-key`) now reads via the sidecar; list/UI
   still use the SDK. Verify with the audit log + a sidecar-down test (broker should 503, not hang).
