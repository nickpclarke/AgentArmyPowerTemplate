# Env-var & secret handling across the fleet

The fleet has three application layers (backend-core, middle-core, frontend-core) with three different runtime stacks (Python/FastAPI, .NET + Python, Next.js). Without a shared discipline they drift toward inconsistent secret-loading patterns and the worst-case failure mode is silent — code reads `os.environ.get(KEY)`, the var is missing, the feature degrades quietly.

This doc is the **shared discipline**. New code in any spoke should follow it; existing drift is tracked as gap issues per spoke.

## The two-axis split

Every variable belongs to one cell of this 2x2:

| | **Secret** (rotatable credential, leak = blast radius) | **Config** (non-secret runtime setting) |
|---|---|---|
| **Local dev** | KV → process env (via launcher); **never on disk** | `.env` (gitignored, in repo as `.env.example`) |
| **Production** | KV → container `secretRef` binding | env block in IaC (Bicep/Terraform) |

The two diagonals (Secret-Local, Config-Production) are where teams reach for shortcuts and where leaks happen. Both diagonals are answered the same way: **lift the value from a vault or IaC source, never put a literal secret in a tracked or even local file.**

## Where the source of truth lives

| Category | Source of truth | Read path (dev) | Read path (prod) |
|---|---|---|---|
| Secrets (any credential) | Azure Key Vault `akv01-agentarmy` | dev-up script: `az keyvault secret show … --query value -o tsv` → `[Environment]::SetEnvironmentVariable(…, …, "Process")` | ACA `secretRef` binding → env var |
| Non-secret config | `.env.example` (the spec) + `.env` (your overrides, gitignored) | pydantic-settings `SettingsConfigDict(env_file=".env")` (Python), Next.js native (`.env.local`), `appsettings.Development.json` (.NET) | IaC-templated env block |
| Tunables in code | typed `Settings` class | pydantic-settings field defaults | same defaults; overrides in IaC env block |

## Local-dev pattern

Boot a session via `scripts/dev-up.ps1` (Windows) or `scripts/dev-up.sh` (Linux/macOS). The script pulls each secret from KV at start, exports it to the current shell, then launches the spokes — so they inherit a fully-hydrated env without any secret touching disk. See [running-locally.md](./running-locally.md).

### Prerequisite: KV access per dev

The pull-from-KV pattern only works if the developer running `dev-up` has `get`+`list` on Secrets in `akv01-agentarmy`. Today the fleet is single-developer; KV grants `nicholas@livecreative.com` full perms. For multi-developer onboarding:

```bash
# Grant a dev get+list on Secrets via access policy (KV is in policy mode, not RBAC)
az keyvault set-policy --name akv01-agentarmy \
  --upn new.dev@example.com \
  --secret-permissions get list
```

`dev-up` calls `az account show` and `az keyvault secret list` up front; if either fails it triggers `az login` and exits with a clear error before any spoke boots — so a permissions gap surfaces immediately, not as N silent skipped secrets.

If you bootstrap manually, this PowerShell line does the same for one secret (key never echoed):

```powershell
$env:TAVILY_API_KEY = az keyvault secret show --vault-name akv01-agentarmy --name tavily-api --query value -o tsv
```

Bash equivalent:

```bash
export TAVILY_API_KEY=$(az keyvault secret show --vault-name akv01-agentarmy --name tavily-api --query value -o tsv)
```

After this, `uvicorn`, `next dev`, or `dotnet run` started in the same shell will see the value via `os.environ`/`process.env`/`Environment.GetEnvironmentVariable`.

### What `.env` is for (and not for)

- ✅ **Non-secret runtime config** that varies by environment: `APP_ENV=local`, `ARCADEDB_URL=http://localhost:2480`, `LLM_GATEWAY_RATE_PER_MIN=60`
- ✅ **Pointers** to where secrets live: `AZURE_KEYVAULT_URL=https://akv01-agentarmy.vault.azure.net/`
- ❌ **Actual secret values**: `TAVILY_API_KEY=tvly-…`, `ARCADEDB_PASSWORD=…`, OIDC client secrets, API keys of any kind

The line between secret and config is "could a leak of this value harm me?" If yes, KV.

## Per-layer implementation pattern

### Python (backend-core, middle-core agent_runtime)

```python
# config.py — pydantic-settings reads .env for NON-SECRET fields
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE), env_file_encoding="utf-8", extra="ignore"
    )
    app_env: str = "local"
    arcadedb_url: str = "http://localhost:2480"
    # secret fields are declared but always default to "" — value comes from process env
    tavily_api_key: str = ""
    arcadedb_password: str = ""
```

For LLM-gateway-style indirection, define a `secret_ref` scheme (`env:` / `file:` / `akv:`) that resolves at call time. See `app/secrets.py` in backend-core for the reference implementation.

> ⚠️ **Known gap (2026-05-26):** backend-core's pydantic-settings populates the `Settings` instance only — not `os.environ`. Code that does `os.environ.get("TAVILY_API_KEY")` (e.g. the `env:` scheme in `app/secrets.py`) misses `.env`-loaded values. Fix: small `main.py` preamble that copies `Settings` fields into `os.environ`. Tracked at backend-core (see below).

### Next.js (frontend-core)

Next.js loads `.env.local` natively. Use `NEXT_PUBLIC_*` prefix for values that need to reach the browser (only the safe ones — never a server secret). Server-only secrets stay un-prefixed and are only readable in Route Handlers / Server Components.

```env
# .env.local  (gitignored)
NEXT_PUBLIC_BACKEND_CORE_URL=http://localhost:8000   # safe to ship to browser
NEXTAUTH_SECRET=…                                     # server-only, NEVER NEXT_PUBLIC_
```

For production secrets, set them as ACA env vars (or Vercel project env vars if/when that's adopted) — never in `.env.production` checked into the repo.

### .NET (middle-core MiddleCore)

`appsettings.Development.json` for non-secret config + `appsettings.Production.json` for prod overrides. Secrets via env vars (`Environment.GetEnvironmentVariable`) bound from `secretRef` in ACA.

```csharp
var apiKey = Environment.GetEnvironmentVariable("TAVILY_API_KEY")
    ?? throw new InvalidOperationException("TAVILY_API_KEY missing — set via dev-up or ACA secretRef");
```

## Production pattern (ACA secretRef → env)

```bicep
// Hub Bicep — the recommended pattern for every spoke ACA app
secrets: [
  { name: 'tavily-api', keyVaultUrl: '${kv.properties.vaultUri}secrets/tavily-api', identity: 'system' }
]
template: {
  containers: [{
    env: [
      { name: 'TAVILY_API_KEY', secretRef: 'tavily-api' }
      { name: 'LLM_GATEWAY_WEB_SEARCH_ENABLED', value: 'true' }
    ]
  }]
}
```

Until every spoke has the managed-identity wiring done (tracked as hub [#216](https://github.com/nickpclarke/AgentArmy/issues/216)), use the ACA built-in secret store via `az containerapp secret set` — same encryption-at-rest properties, no identity dependency.

## Pre-commit safety net (rolling out)

Each spoke should add a `gitleaks` or `detect-secrets` pre-commit hook so accidental secret commits get caught locally before they reach git history. Tracked per spoke; once all four repos have it, this section moves to "in place."

## Adding a new env var: checklist

1. **Is it a secret?** If yes → add to KV, document in [secrets-rotation.md](./security/secrets-rotation.md), update `dev-up.{ps1,sh}` `SECRETS` map.
2. **Is it config?** If yes → add an `EXAMPLE_VAR=` slot in `.env.example` with a comment, declare a `Settings` field with a safe default.
3. **Does prod need it?** If yes → add to the relevant Bicep / Terraform IaC, NOT to a checked-in `.env.production`.
4. **Does the browser need it?** Only if yes, use `NEXT_PUBLIC_*` prefix in frontend-core — and only if the value is safe to ship publicly.

## Related
- [running-locally.md](./running-locally.md) — boot the fleet
- [security/secrets-rotation.md](./security/secrets-rotation.md) — rotation policy
- [setup.md](./setup.md) — first-time machine setup
