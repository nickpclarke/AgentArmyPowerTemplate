# Fleet environments

Where each application layer lives in `local`, `dev` (Azure), and `prod`. This page is the **canonical URL registry** — every spoke gets a local copy via the daily helper-sync at `.agent/environments.json` so sandboxed agents (microVMs with no hub board access) can resolve other layers at runtime.

> Edit only on the hub. The fleet-sync routine propagates this to every spoke; spokes overwrite their local copies on each pull. Machine-readable twin: [`.agent/environments.json`](https://github.com/nickpclarke/AgentArmy/blob/main/.agent/environments.json).

## `local` — your dev box

Native ports per [running-locally.md](./running-locally.md). Use `scripts/dev-up.{ps1,sh}` to boot in order.

| Layer | URL | Default port |
|---|---|---|
| frontend-core | `http://localhost:3000` | 3000 |
| backend-core | `http://localhost:8000` | 8000 |
| middle-core agent_runtime | `http://localhost:8001` | 8001 |
| middle-core .NET | `http://localhost:5000` | 5000 |
| ArcadeDB | `http://localhost:2480` | 2480 |
| Postgres | `postgres://localhost:5432` | 5432 |
| NATS | `nats://localhost:4222` | 4222 |
| Fuseki | `http://localhost:3030` | 3030 |
| event-bridge | `http://localhost:8080` | 8080 |

## `dev` — Azure Container Apps (`cae-arcade-platform`, `rg-arcade-platform`, eastus)

All apps live in **one managed environment**. Internal-ingress apps are only reachable from inside this env, which is why `middle-core` MUST deploy here to call `backend-core`.

| App | URL | External? | Tier (ADR-023) | Status |
|---|---|---|---|---|
| **frontend-core** | https://frontend-core.kindcoast-b0a6ea84.eastus.azurecontainerapps.io | ✅ public | application | live |
| **backend-core** | http://backend-core.internal.kindcoast-b0a6ea84.eastus.azurecontainerapps.io | 🔒 internal | application | live |
| **arcadedb** | http://arcadedb.internal.kindcoast-b0a6ea84.eastus.azurecontainerapps.io | 🔒 internal | platform | live |
| **middle-core** | _(not deployed yet)_ | 🔒 internal (planned) | application | **planned** |

### backend-core (the most-called URL)

- **Ingress:** `external: false`, `allowInsecure: true`, `transport: Http`
- **Auth:** all non-health `/api/v1/*` routes require a **JWT bearer**. Dev allows HS256 with `AUTH_JWT_SECRET`; prod uses OIDC/JWKS (`AUTH_JWKS_URL` + `AUTH_ISSUER` + `AUTH_AUDIENCE`).
- **LLM gateway:** `/v1/chat/completions` (OpenAI-shaped, multi-provider), `/v1/embeddings`, `/v1/models`, plus `/v1/tools/{search,extract}` (flag-gated; Tavily-backed). The `LLM_GATEWAY_WEB_SEARCH_ENABLED=true` flag is set on dev; `TAVILY_API_KEY` resolves from `secretref:tavily-api` (KV-sourced).
- **Calling it from middle-core (dev):**
  ```bash
  curl -fsS http://backend-core.internal.kindcoast-b0a6ea84.eastus.azurecontainerapps.io/health/ready
  curl -fsS -H "Authorization: Bearer $JWT" \
    http://backend-core.internal.kindcoast-b0a6ea84.eastus.azurecontainerapps.io/api/v1/stats
  ```

### Shared platform deps

- **Key Vault:** `akv01-agentarmy` (access-policy mode, not RBAC). The dev-up scripts hydrate secrets from here at session start. See [env-handling.md](./env-handling.md).
- **Container Registry:** `arcadeplatformacr.azurecr.io`. Single ACR convergence is tracked at [hub#218](https://github.com/nickpclarke/AgentArmy/issues/218).

## `prod` — not provisioned yet

Tracked by [hub#219](https://github.com/nickpclarke/AgentArmy/issues/219) (`rg-aa-env-tier` naming) and [hub#220](https://github.com/nickpclarke/AgentArmy/issues/220) (Azure Front Door + WAF). Will follow the same shape: a single external front-door over a fleet of internal-ingress spokes in a hardened ACA env.

## How spokes should consume this

Two equivalent reads:

```python
# Python — parse the machine twin
import json, pathlib
envs = json.loads(pathlib.Path(".agent/environments.json").read_text())
backend_url = envs["environments"]["dev"]["apps"]["backend_core"]["url"]
```

```typescript
// Node / Next.js
import envs from "../../.agent/environments.json";
const backendUrl = envs.environments.dev.apps.backend_core.url;
```

**Don't hardcode URLs** in spoke code — read from `environments.json` so a single hub update propagates to every spoke on next sync.

## Related
- [running-locally.md](./running-locally.md) — boot the fleet locally
- [env-handling.md](./env-handling.md) — secrets + non-secret config strategy
- [contracts.md](./contracts.md) — inter-layer contract registry
