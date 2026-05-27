# Secrets management

Single doctrine across the fleet:

> **Key Vault is the source of truth. Local files are a derived view of it.**
> Rotation happens once — in `akv01-agentarmy`. Local files get re-derived
> via `scripts/secrets/sync.py`. No one hand-edits a key into a `.env`.

This doc covers the rotation flow, the onboarding flow, and what to expect at
each layer of the stack. The tooling is in `scripts/secrets/`.

## The one rule

If a secret has a Key Vault entry in `akv01-agentarmy`, **do not edit it in any
local file**. Edit it in KV, then run `python scripts/secrets/sync.py`. The
local file is regenerated; your edit would have been overwritten on the next
sync anyway.

## What lives where

| Layer | Where it reads from in production | Where it reads from locally |
|---|---|---|
| Azure Container Apps (ACA) | KV `secretref:` mounts (auto) | n/a |
| Backend-core (uvicorn / docker) | `os.environ` from `.env` | `.env` populated by sync |
| Middle-core (agent_runtime) | `os.environ` from `.env` | `.env` populated by sync |
| LLM gateway (function-tier) | `AUTH_JWT_SECRET_FILE` etc. (KV `_FILE` refs) | `.env` populated by sync |
| Local-stack platform services | docker secrets → mounted files | `templates/local-stack/.secrets/*.txt` |
| Hub tooling (Postman, GH PAT) | n/a (cloud unused) | `.env` populated by sync |

The asymmetry between cloud and local was the source of pain: cloud read from
KV automatically, but local dev required you to remember to copy the value
into a `.env`. The sync script closes that gap.

## Tooling

### `scripts/secrets/sync.py` — pull KV → local files

```bash
# Pull all entries declared in the manifest.
python scripts/secrets/sync.py

# Preview without writing anything.
python scripts/secrets/sync.py --dry-run

# Subset (after rotation, refresh only what changed).
python scripts/secrets/sync.py --only tavily-api-key,cerebras-api-key
```

Each entry in `scripts/secrets/secrets-manifest.json` declares:

```json
{
  "kv_name": "tavily-api-key",
  "description": "Tavily web-search API key used by ...",
  "consumer": "backend-core",
  "writes_to": {
    "type": "env_file",
    "path": "../backend-core/.env",
    "key": "TAVILY_API_KEY"
  }
}
```

Two `writes_to.type` modes:

- **`env_file`** — sets a `KEY=value` line in a `.env` file (creates or
  upserts; preserves other lines).
- **`secret_file`** — writes the raw value to a single file (the
  Docker-secrets / `*_FILE` convention used by ArcadeDB, JWT, etc.).

Safety rails:

- Values are **never echoed to stdout**. Only secret *names* and write
  *targets* are logged.
- Target paths are validated to live under the workspace (`AgentArmy/..`); a
  manifest typo can't clobber arbitrary system files.
- `az login` is the only prerequisite. The CLI's own diagnostic logs don't
  retain values either.

### `scripts/secrets/status.py` — freshness check (read-only)

```bash
# Human-readable table.
python scripts/secrets/status.py

# Machine-readable (for CI / heartbeat).
python scripts/secrets/status.py --json
```

Reports `current` / `stale` / `missing` / `error` per row by comparing the
KV `attributes.updated` timestamp to the local file's mtime. **Never reads a
secret value** — only metadata. Safe to run on every heartbeat tick.

Exit code: `0` if all rows are current; `1` if any are stale/missing; `2` on
configuration error.

## Rotation flow

1. Generate a new value at the upstream provider (Tavily console, Cerebras
   console, Azure Foundry, etc.).
2. **Set it in Key Vault**:
   ```bash
   az keyvault secret set --vault-name akv01-agentarmy --name <kv_name> --value <new>
   ```
   ⚠ The `--value` argument lands in your shell history. Prefer
   `--file <(echo -n "$NEW_VALUE")` or read from a temp file you `shred` afterward.
3. Confirm `properties.updated` advanced:
   ```bash
   az keyvault secret show --vault-name akv01-agentarmy --name <kv_name> \
     --query "attributes.updated" -o tsv
   ```
4. **Locally**: `python scripts/secrets/sync.py --only <kv_name>` →
   regenerates the affected `.env` line.
5. **Deployed**: ACA picks up the new value on the next container restart
   (Container Apps reads `secretref:` at start). Trigger a revision rollout
   if you need it sooner — `az containerapp update --revision-suffix rot`.
6. **Old value**: revoke at the upstream provider (delete the old API key
   from Tavily / Cerebras / etc.). The KV history retains the old version
   for emergency rollback; don't delete it from KV.

## Onboarding flow (new developer / fresh clone)

```bash
git clone <hub>
git clone <spokes>          # backend-core, middle-core, frontend-core
az login                    # required for KV access
cd AgentArmy
python scripts/secrets/sync.py
```

That's it — every `.env` and `.secrets/*.txt` declared in the manifest is
populated. No more "copy this value from Slack" / "ask Nick for the embed key."

## Adding a new secret

1. Create it in KV:
   ```bash
   az keyvault secret set --vault-name akv01-agentarmy --name new-thing --value "..."
   ```
2. Add an entry to `scripts/secrets/secrets-manifest.json`:
   ```json
   {
     "kv_name": "new-thing",
     "description": "What this is for, and which ADR governs its use.",
     "consumer": "backend-core",
     "writes_to": { "type": "env_file", "path": "../backend-core/.env", "key": "NEW_THING" }
   }
   ```
3. `python scripts/secrets/sync.py --only new-thing` to populate locally.
4. For ACA, add the corresponding `secretref:` in the spoke's Bicep / Container
   App definition pointing at the same KV name. The local→cloud parity is
   maintained by convention: KV name = the contract.

## What's coming next

Tracked separately, not in this doctrine doc:

- **Per-container `/diagnostics` endpoints** that surface *which* secrets each
  container loaded + when they were set in KV — **without ever exposing the
  value**. Lets an operator answer "did I forget a rotation in middle-core?"
  by visiting one page. See hub issue queue (`feat/diagnostics`).
- **Heartbeat integration**: `fleet-heartbeat.mjs` will call `status.py --json`
  and surface stale rows as findings.
