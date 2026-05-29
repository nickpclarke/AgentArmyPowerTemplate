# Infisical — BYO-credentials secrets store (platform tier)

The secrets **store** for the bring-your-own-keys surface
([ARC-ADR-037](../../docs/decisions/ARC-ADR-037-byo-credentials-secrets-broker.md)).
Users register their per-system keys (GitHub, Jira, Linear, Stripe, …); backend-core's
broker keeps **raw keys server-side** and hands tools scoped/short-lived references.
Platform tier ([ARC-ADR-023](../../docs/decisions/ARC-ADR-023-container-tiering-strategy.md)):
Infisical backend + Postgres + Redis.

Chosen over HashiCorp Vault (BSL license trap) and OpenBao (heavier multi-tenant ops) for
fastest adoption at the current solo/trusted stage; OpenBao is the documented upgrade path
for untrusted multi-tenancy.

## Run (local)
```sh
sh setup.sh            # rolls a gitignored .env (secrets) on first run, then docker compose up -d
python doctor.py       # GET http://localhost:8333/api/status == 200
```
UI/API at `http://localhost:8333`. First run: create the admin account in the web UI
(Infisical's self-host bootstrap). Pinned to `infisical/infisical:v0.160.7`.

## Env (generated into `.env`, never committed)
`ENCRYPTION_KEY` (hex16) · `AUTH_SECRET` (base64) · `POSTGRES_*` · `DB_CONNECTION_URI` ·
`REDIS_URL` · `SITE_URL`. See `.env.example` for the shape.

## Next (the broker — ARC-ADR-037 implementation)
backend-core gains `/api/v1/credentials/*`: a user registers a `{system}` key → written to
Infisical under a per-user path → tools request a scoped reference, resolved server-side at
call time. Tools never see the raw key (extends the abstraction-MCP proxy pattern).

## Deploy (ACA)
Backend as a container app backed by Azure Database for PostgreSQL Flexible Server + Azure
Cache for Redis; secrets from Key Vault; fronted by CF Access. Only the broker talks to it.
