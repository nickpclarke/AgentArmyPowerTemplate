# Running the fleet locally

How to bring up the three application layers on a dev box, in the right order, with secrets sourced from Azure Key Vault (never written to disk).

## TL;DR

```powershell
# Windows / PowerShell
.\scripts\dev-up.ps1
# Then: cd ..\frontend-core; npm run dev
```

```bash
# Linux / macOS / Git-Bash
./scripts/dev-up.sh
# Then: cd ../frontend-core && npm run dev
```

The script will:
1. `docker compose up -d` the hub `local-stack` (ArcadeDB, Postgres, NATS, event-bridge, Fuseki)
2. Hydrate the current shell with secrets pulled from `akv01-agentarmy` (see [docs/env-handling.md](./env-handling.md))
3. Launch `backend-core` (uvicorn on `:8000`) and `middle-core` agent_runtime (uvicorn on `:8001`) in background processes (or new PowerShell windows on Windows)
4. Print a health-check summary

You start `frontend-core` separately in the foreground so you keep its HMR output and don't lose hot-reload context.

## Dependency order (why it matters)

```
hub local-stack (data + bus)
        ↓
backend-core (publishes openapi contract; owns ArcadeDB schema)
        ↓
middle-core agent_runtime (consumes backend-core /api/v1 + /v1)
        ↓
frontend-core (consumes both)
```

Skip a tier and the spokes silently start with broken upstream connections — failure surfaces late as cryptic 5xx in dev. `dev-up` enforces the order; manual boot is your responsibility.

## Manual boot (when you need precise control)

### 1. Hub local-stack

```bash
cd templates/local-stack
docker compose up -d
bash local-stack-doctor.sh   # one-pass health probe over 5 services
```

Default ports: ArcadeDB `2480`, Postgres `5432`, NATS `4222`, event-bridge `8080`, Fuseki `3030`.

### 2. backend-core (FastAPI on `:8000`)

```powershell
cd C:\Dev\backend-core
pip install -r requirements.txt   # one-time
uvicorn app.main:app --reload --port 8000
# health: curl http://localhost:8000/health/ready
```

**Secrets**: `TAVILY_API_KEY`, `AZURE_EMBED_API_KEY`, `ARCADEDB_PASSWORD`, etc. must be in your shell env before uvicorn starts. The `dev-up` script handles this; if booting manually, source secrets yourself from KV — see [env-handling.md](./env-handling.md#local-dev-pattern). **Do not put secret values in `.env`.**

Alternative: `docker compose up -d` from `C:\Dev\backend-core` brings up backend + local ArcadeDB + rust-api-v2 sidecar. Heavier, closer to prod.

### 3. middle-core agent_runtime (Python FastAPI on `:8001`)

```powershell
cd C:\Dev\middle-core
uvicorn agent_runtime.app:create_app --factory --port 8001
# health: curl http://localhost:8001/health
```

The middle-core .NET service is a separate process when you need it:

```powershell
dotnet run --project templates/middle-core/MiddleCore.csproj   # default :5000
```

For most local agent work you only need `agent_runtime`.

### 4. frontend-core (Next.js on `:3000`)

```powershell
cd C:\Dev\frontend-core
npm install        # one-time
npm run dev        # next dev on :3000
```

Frontend-core reads `process.env.NEXT_PUBLIC_BACKEND_CORE_URL` (default `http://localhost:8000`) at build time. If you've changed the backend-core port, set it in `.env.local` (gitignored, Next.js auto-loads).

## Doctor checks

| Layer | One-liner |
|---|---|
| Hub local-stack | `bash templates/local-stack/local-stack-doctor.sh` |
| backend-core | `curl -fsS http://localhost:8000/health/ready` |
| middle-core agent_runtime | `curl -fsS http://localhost:8001/health` |
| frontend-core | open `http://localhost:3000` in a browser |

## Stopping

```bash
# Stop the local-stack
docker compose -f templates/local-stack/docker-compose.yml down

# Stop the uvicorn processes (Linux/macOS) by PID from /tmp/backend-core.log, /tmp/middle-core.log
# On Windows: close the PowerShell windows opened by dev-up.ps1
```

## See also
- [docs/env-handling.md](./env-handling.md) — fleet-wide env / secret strategy
- [docs/setup.md](./setup.md) — first-time machine setup (Claude Code, gh, az, LSPs)
- [docs/security/secrets-rotation.md](./security/secrets-rotation.md) — rotation policy + procedures
