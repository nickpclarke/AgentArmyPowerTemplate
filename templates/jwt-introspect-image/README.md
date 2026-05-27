# jwt-introspect-image

JWT introspection sidecar — function-tier image that verifies forwarded user JWTs per [ARC-ADR-002](../../docs/decisions/ARC-ADR-002-jwt-forwarding-auth-contract.md). Exposes `POST /introspect` so every spoke calls one local endpoint instead of re-implementing RS256 + JWKS-rotation logic.

Closes hub issue #284. Realizes the verify-side of ADR-002.

## Quick start

```bash
cd templates/jwt-introspect-image
./setup.sh
```

This builds the image, brings up the sidecar (CPU, ~50 MB), waits for `/livez`, and runs the doctor. The doctor mints its own RSA keypair + JWKS + JWTs (no external IdP needed) and proves all 5 checks end-to-end.

Expected output: **5 pass, 0 fail**.

```bash
./setup.sh --down
```

## /introspect endpoint

POST a bearer token, get back verified claims (or 401).

```bash
curl -sS http://localhost:8084/introspect \
  -H 'Content-Type: application/json' \
  -d '{"token":"eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Im..."}'
```

Response shapes:

```json
{ "active": true,  "claims": { "sub": "user-1", "iss": "...", "aud": "...", "exp": 1748370000 } }
{ "active": false, "error":  "token expired: Signature has expired" }
```

Response codes:

| HTTP | Meaning |
|---|---|
| `200` | Token verified — `claims` carries the decoded payload |
| `401` | Token rejected (bad sig / expired / wrong iss / wrong aud / unknown kid / unconfigured JWKS) |
| `503` | Sidecar isn't ready (`/readyz` only — `/introspect` always answers 200 or 401) |

## Health surface

| Endpoint | Auth-free? | Returns | Use case |
|---|:---:|---|---|
| `/livez` | ✅ | 200 always (no dependency checks) | LB liveness probe |
| `/readyz` | ✅ | 200 when `JWKS_URL` is reachable + JWKS-shaped; 503 + Problem Details otherwise | LB readiness gate |
| `/healthz` | ✅ | 200 with version + issuer + audience + leeway + algs + JWKS status | Heartbeat + dashboards |

The JWKS fetch is lazy — the sidecar boots in seconds and serves `/livez` even before the first JWKS fetch. `/readyz` probes JWKS reachability on each call so it goes 503 → 200 as soon as the issuer comes online.

## Configuration

| Env var | Default | Meaning |
|---|---|---|
| `JWKS_URL` | _(unset → 401s every request)_ | HTTPS URL of the issuer's JWKS document |
| `JWKS_TTL_SECONDS` | `300` | JWKS cache TTL. Refresh is dogpile-safe (lock-guarded) |
| `JWT_ISSUER` | _(unset → iss check skipped + warned)_ | Expected `iss` claim |
| `JWT_AUDIENCE` | _(unset → aud check skipped + warned)_ | Expected `aud` claim |
| `JWT_LEEWAY_SECONDS` | `0` | Clock-skew tolerance for exp/nbf |
| `JWT_ALGORITHMS` | `RS256,ES256` | Allowed algs. **HS* and `none` are hard-refused at startup** (CWE-347) |
| `INTROSPECT_PORT` | `8084` | Listen port |

## Why function-tier (per [ARC-ADR-023](../../docs/decisions/ARC-ADR-023-container-tiering-strategy.md))

- **Cross-cutting** — auth verification belongs in a sidecar, not duplicated across every spoke.
- **Small static surface** — a single `/introspect` endpoint; <100 MB image.
- **Independent rollout** — JWKS issuer changes, leeway tuning, or revocation-cache updates ship without touching any spoke.

## Doctor — what it proves

The doctor mints its own keypair so the image proves end-to-end without depending on an external IdP. See `scripts/jwt-doctor.sh`.

| # | Check | How |
|---|---|---|
| 1 | readiness | `/healthz` returns 200 with `jwks_reachable=true` within 15s |
| 2 | valid-token-returns-claims | Fresh RS256 JWT → 200 + `active:true` + expected `sub` |
| 3 | tampered-rejected | Last-byte-mutated signature → 401 + `active:false` |
| 4 | expired-rejected | 60s-stale JWT (leeway=0) → 401 + error mentions "expired" |
| 5 | leeway-honored | Restart with `JWT_LEEWAY_SECONDS=60`; 30s-stale JWT → 200 |

## Roadmap

- **Revocation list integration** (next) — local TTL'd cache of revoked `jti`s pulled from the issuer's revocation endpoint, with negative-result caching so verify stays sub-ms.
- **CRL / OCSP for x5c-presented keys** — only matters once we mint short-lived JWTs from an internal CA.
- **mTLS-bound tokens** ([RFC 8705](https://www.rfc-editor.org/rfc/rfc8705)) — bind the JWT to the client cert so a stolen token from one spoke can't be replayed from another.
- **JWT-DPoP** ([RFC 9449](https://www.rfc-editor.org/rfc/rfc9449)) — proof-of-possession for browser-originated tokens once frontend uses public clients.

## Contract anchor

Realizes the verify-side of [ARC-ADR-002](../../docs/decisions/ARC-ADR-002-jwt-forwarding-auth-contract.md). No new external contract — the OAuth/OIDC issuer's JWKS is the only upstream. Registered in [`docs/contracts.md`](../../docs/contracts.md).
