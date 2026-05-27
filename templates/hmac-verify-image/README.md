# hmac-verify-image

Reusable HMAC-signature verification sidecar — function-tier image that sits in front of any spoke accepting signed webhooks (GitHub `X-Hub-Signature-256`, Stripe `Stripe-Signature`, Postmark `X-Postmark-Signature`, custom). Verifies the signature constant-time using `hmac.compare_digest`, applies replay protection by delivery-id, then proxies the verified request to the upstream spoke.

Closes hub issue #282. Lifts the constant-time verifier already living inside [`templates/event-bridge-image/scripts/webhook_receiver.py`](../event-bridge-image/scripts/webhook_receiver.py) into its own image so any signed-webhook source can reuse it without copy-paste.

## Quick start

```bash
cd templates/hmac-verify-image
./setup.sh
```

This builds the image, brings up the sidecar **plus a tiny stdlib echo upstream** (so the doctor can prove the verified request actually got proxied), waits for `/livez` on both, and runs the doctor.

Expected output: **5 pass, 0 fail**.

```bash
./setup.sh --down   # tear down
```

## Verify endpoint

```bash
# Compute the GitHub-style signature for a payload + secret.
BODY='{"action":"opened","number":1}'
SECRET=doctor-secret
SIG="sha256=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')"

curl -sS http://localhost:8083/verify \
  -H 'Content-Type: application/json' \
  -H "X-Hub-Signature-256: ${SIG}" \
  -H 'X-GitHub-Delivery: abc-123' \
  -X POST -d "$BODY"
```

Response when verified + proxied: whatever the upstream returned. When verified in **verify-only mode** (no `UPSTREAM_URL` set): `{"ok": true, "verified": true, "delivery_id": "abc-123"}`.

| Failure | HTTP | Body shape |
|---|:---:|---|
| Missing signature header | 401 | RFC 7807 Problem Details |
| Wrong signature | 401 | RFC 7807 Problem Details |
| Replay of same delivery-id within TTL | 409 | RFC 7807 Problem Details |
| Upstream unreachable / 5xx | 502 | RFC 7807 Problem Details |
| `HMAC_SECRET` not configured | 500 | RFC 7807 Problem Details — fail closed |

## Health surface

| Endpoint | Auth-free? | Returns | Use case |
|---|:---:|---|---|
| `/livez` | ✅ | 200 always (no dependency checks) | LB liveness probe |
| `/readyz` | ✅ | 200 when secret loaded + upstream reachable; 503 + Problem Details otherwise | LB readiness gate |
| `/healthz` | ✅ | 200 with version + provider config + per-dependency status | Heartbeat + dashboards |

## Configuration

| Env var | Default | Meaning |
|---|---|---|
| `PROVIDER` | `github` | Provider preset. One of: `github`, `stripe`, `postmark`, `custom` |
| `HMAC_SECRET` | (none) | Shared secret. **Required.** Fails closed if unset. |
| `HMAC_SECRET_FILE` | `/run/secrets/hmac_secret` | File path to the secret (preferred — mount via Docker secret / K8s Secret) |
| `UPSTREAM_URL` | (none) | Where to forward verified requests. If unset, runs in **verify-only mode** (returns 200 without proxying) |
| `SIGNATURE_HEADER` | provider-dependent | Override the header name carrying the signature |
| `SIGNATURE_PREFIX` | provider-dependent | Override the algo tag prefix (e.g. `sha256=` for GitHub) |
| `DELIVERY_HEADER` | provider-dependent | Override the header name carrying the delivery id (replay key) |
| `REPLAY_TTL_SECONDS` | `300` | Replay window. Same delivery-id within this window returns 409 |
| `HMAC_PORT` | `8083` | Listen port |

### Provider presets

| Provider | Signature header | Prefix | Algo | Delivery header |
|---|---|---|---|---|
| `github` | `X-Hub-Signature-256` | `sha256=` | sha256 | `X-GitHub-Delivery` |
| `stripe` | `Stripe-Signature` | (none) | sha256 | `Stripe-Signature` |
| `postmark` | `X-Postmark-Signature` | (none) | sha256 | `X-Postmark-Message-Id` |
| `custom` | `X-Signature` | (none) | sha256 | `X-Delivery-Id` |

Override any field via the `SIGNATURE_HEADER` / `SIGNATURE_PREFIX` / `DELIVERY_HEADER` envs.

## Secret-resolution roadmap

| Stage | How the secret arrives | Status |
|---|---|---|
| Local dev / doctor | `HMAC_SECRET` env var | ✅ Shipped |
| Compose / K8s mount | `HMAC_SECRET_FILE` (Docker secret / K8s Secret) | ✅ Shipped |
| Azure Container Apps | KV-referenced env var (ACA secret backed by Key Vault) | 🔜 follow-up (deployment-engineer) |
| Direct KV unwrap on boot | `cryptography` is pre-installed for the SDK call | 🔜 follow-up |

The `cryptography` dependency is baked into the image now so the KV-unwrap follow-up doesn't need a rebuild — it's a code change only.

## Why function-tier (per [ARC-ADR-023](../../docs/decisions/ARC-ADR-023-container-tiering-strategy.md))

- **Independent rollout** — security primitives ship without rebuilding their host spoke. A CVE in the verifier shouldn't force a backend redeploy.
- **Composable** — drop it in front of any new spoke that takes signed input, no spoke code changes. The proxy hop is transparent.
- **Auditable in isolation** — the doctor proves the constant-time + replay invariants without depending on the host spoke being up.

## Contract anchor

No new contract — this image realizes the verification half of [`contracts/webhook-receiver.openapi.yaml`](../../contracts/webhook-receiver.openapi.yaml) for any signed-webhook source. The webhook-receiver spec is the GitHub-specific consumer; this image generalizes the verification primitive.
