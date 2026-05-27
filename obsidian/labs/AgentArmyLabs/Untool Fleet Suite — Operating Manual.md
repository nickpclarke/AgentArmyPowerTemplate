---
tags: [operating-manual, mcp, fleet, cf-access, runbook]
created: 2026-05-27
status: live
related:
  - "[[Cloud Agents → Local Docker — Control Plane Plan]]"
  - "[[Security Model — Exposed Control Plane]]"
  - "[[Session 2026-05-27 — Dev Tunnel, Log Multiplexer, Catalog Gap]]"
---

# Untool Fleet Suite — Operating Manual

> The **untool fleet suite** is a small MCP server that lets cloud agents (claude.ai routines, `claude.yml` microVMs on `@claude` mentions, GitHub Copilot coding agents, Codex worktrees, remote API callers) **build, observe, restart, and deploy services running on the operator's local Docker fleet** — without ever exposing the Docker socket directly. As of 2026-05-27 it is live at `https://mcp.untool.ai/mcp` behind Cloudflare Access edge enforcement; bearer-token auth survives only on `127.0.0.1:8765` for local dev.

This note is the **operating manual** for that capability: who calls what, how identities are provisioned and revoked, how to attribute / audit / debug calls, and how each agent type in our fleet picks the suite up when it works on Issues and PRs.

For architecture rationale see [[Cloud Agents → Local Docker — Control Plane Plan]]; for the threat model see [[Security Model — Exposed Control Plane]]; for code, `tools/mcp-local-fleet/`.

## What you get — 8 docker primitives, universal but server-labelled

| Tool | Phase | Risk | What it does |
|---|---|---|---|
| `fleet_ps` | 1 | low | List allowlisted platform containers + state |
| `fleet_inspect` | 1 | low | Image / status / ports / env-key-names for one container (values redacted) |
| `fleet_logs` | 1 | low | `docker logs <ctr>` for one allowlisted service; substring grep + level filter |
| `fleet_up` | 2 | med | `compose up -d --no-build <svc>` |
| `fleet_down` | 2 | med | `compose stop` + `compose rm -f` (volumes preserved) |
| `fleet_restart` | 2 | med | `compose restart <svc>` |
| `fleet_build` | 3 | high | `compose build [--no-cache] <svc>` (single in-flight build per service) |
| `fleet_deploy` | 4 | high | `git fetch + checkout + compose build + restart` in one call (refuses dirty tree; strict refname validation) |

**Universal, not personal.** The 8 tool names are universal Docker primitives. The *server instance* carries a `MCP_TARGET` label (default `local-home`). Today's only running instance is `local-home` (the operator's office PC reached via `mcp.untool.ai`). Planned: `local-runner`, `dev-cloud`, `test-cloud`, `prod-edge` — each will use the same tools, with the target identifying which environment was touched. Cloud agents see the label in `serverInfo._meta.target` and per-tool `_meta.target` on `tools/list`.

**Approval discipline.** Read-only tools (`fleet_ps`/`fleet_inspect`/`fleet_logs`) are safe to auto-approve. Write tools (`fleet_up`/`down`/`restart`/`build`/`deploy`) must keep per-call approval ON in claude.ai — they execute arbitrary code in the operator's docker host. Don't whitelist them in `.claude/settings.local.json` for a cloud agent's identity.

## Two auth modes — pick by where you're calling from

### Cloud → `mcp.untool.ai` (CF Access service tokens)

Set two HTTP headers on every JSON-RPC call:

```
CF-Access-Client-Id:     <client-id-from-CF-dashboard>
CF-Access-Client-Secret: <client-secret-from-CF-dashboard>
```

CF Access enforces auth at the edge — unauthenticated requests get a 302 to the Access login and never reach our server. CF Access then injects a `Cf-Access-Jwt-Assertion` header which our server verifies in `cfaccess-edge.mjs` (defense in depth). Audit log records the principal as `cfaccess-edge:service:<common-name>` so every call is attributable to the specific cloud-agent identity.

### Local → `127.0.0.1:8765` (legacy bearer)

```
Authorization: Bearer <token-from-KV-local-fleet-mcp-token-*>
```

Bearer is refused at the public edge but accepted on loopback — handy for dev. The legacy `local-fleet-mcp-key` continues to work as principal `token:static-legacy`. Per-agent tokens live in KV `akv01-agentarmy` with prefix `local-fleet-mcp-token-` — see `tokens.mjs` for the enumeration logic.

## Provisioning a new cloud consumer (3 minutes)

You're standing up a new agent type — a new claude.ai routine, a new GHA workflow, a new Codex worktree, etc. Each consumer deserves its own service-token identity so the audit log is attributable and a leaked token can be revoked without affecting others.

```bash
# 1. CF Dashboard: Zero Trust → Access → Service Auth → Create service token
#    Name:  mcp-untool-<consumer>            e.g. mcp-untool-gha-fleet-build
#    TTL:   1 year
#    Copy Client ID + Client Secret (Secret is shown ONCE).

# 2. Store the pair in Key Vault under matching names
az keyvault secret set --vault-name akv01-agentarmy \
  --name cf-access-svc-<consumer>-id     --value "<client-id>"
az keyvault secret set --vault-name akv01-agentarmy \
  --name cf-access-svc-<consumer>-secret --value "<client-secret>"

# 3. Attach the service token to the "Local Fleet MCP" Access Application
#    Policy: decision=non_identity, include=service-token mcp-untool-<consumer>.

# 4. Wire the consumer's bootstrap to read both KV secrets and export them
#    as CF_ACCESS_CLIENT_ID + CF_ACCESS_CLIENT_SECRET env vars before
#    `claude` (or the equivalent agent runtime) starts. See per-agent-type
#    recipes below.
```

**Revoke** by deleting the CF Access service token in the dashboard (immediate; no server restart needed) — the audit log will show the rejected attempt, and the consumer falls dark until a new token is provisioned.

## Per-agent-type bootstrap recipes

### `claude.yml` (GitHub Actions @claude responder)

Add three repo-level secrets via `gh secret set` (do this once per repo: hub + 3 spokes):

```bash
gh secret set LOCAL_FLEET_MCP_URL    --body "https://mcp.untool.ai/mcp"
gh secret set CF_ACCESS_CLIENT_ID    --body "<client-id-for-this-repo>"
gh secret set CF_ACCESS_CLIENT_SECRET --body "<client-secret-for-this-repo>"
```

Each repo gets its own service token (`mcp-untool-claude-yml-<repo>`) so the audit log shows which repo's @claude mention triggered a fleet call. Then patch `.github/workflows/claude.yml` to expose them as env vars to the microVM — the job-level `env:` block is inherited by the `claude-code-action` step, which passes them through to the spawned `claude` process. See `.github/workflows/claude.yml` for the canonical wiring.

### Copilot coding agent

Copilot's microVM is spawned by GitHub-side infrastructure when an issue gets assigned, not by our workflow. To inject env vars, configure a **Copilot environment** in repo settings (Settings → Copilot → Coding agent → Environment) with the three secrets above. Copilot then reads them at task start. Note: Copilot tasks are small and mechanical by design (`copilot-task` label) — fleet write operations should usually escalate to `agent-army-task` instead.

### claude.ai routines (cloud scheduled agents)

Routines run in Anthropic's cloud and have no access to KV. Two options:

- **Path A (today):** bake `CF_ACCESS_CLIENT_ID` + `CF_ACCESS_CLIENT_SECRET` into the routine's prompt as `export` lines. Trust boundary: the values live in the routine config at Anthropic — acceptable for development. See `tools/mcp-local-fleet/AUTOMATION.md` Path A.
- **Path B (eventually):** Anthropic exposes per-routine env-var injection from a connected secret store. Until then, Path A is the only workable option.

### Codex worktrees (`.codex/worktrees/`)

Codex runs on the operator's machine, so it can read KV directly. Codex bootstrap should `az keyvault secret show` the two values and `export` them before invoking `claude`. Alternative: use loopback bearer auth (`http://127.0.0.1:8765/mcp`) since Codex is local — no CF Access round-trip needed.

### Local Claude Code (operator's interactive sessions)

`.claude/settings.local.json` has the env block with `LOCAL_FLEET_MCP_TOKEN` already wired (gitignored). `.mcp.json` defaults `LOCAL_FLEET_MCP_URL` to `127.0.0.1:8765` if unset, so local sessions hit loopback and use the bearer — no CF Access involved. CF Access env vars are unset → MCP client passes empty headers → server ignores them.

## Picking up Issues + PRs with the fleet suite

How does a cloud agent picking up an issue *know* it should use the fleet suite? Two patterns work in practice — apply both.

### Pattern 1: Label-driven

Add `needs-fleet-access` (and create the label if it doesn't exist) to issues that require live container inspection. When `claude.yml` fires and the agent reads the issue body, it sees the label and knows to bias toward `fleet_logs` / `fleet_inspect` / `fleet_restart` rather than asking the operator to run commands locally.

Issues that warrant the label:
- "Service X is returning 500s in production — diagnose"
- "Verify migration <N> completed cleanly on `agentarmy-arcadedb`"
- "Bounce backend-core after merging #123"
- "What images are running and at what tags?"

### Pattern 2: CLAUDE.md routing-table row

The hub `CLAUDE.md` now has this row in the Claude Code army routing table:

> | Inspect/manage operator's local docker fleet (logs, restart, build, deploy) | **untool fleet suite** — `mcp__local-fleet__fleet_*` tools |

So any Claude Code agent (local or microVM) reading CLAUDE.md on session start sees the routing. The spoke helper-pack sync (already in place) propagates this routing into spoke CLAUDE.md files too.

## Common operational tasks

### "Debug a misbehaving container"

```
fleet_ps                                                    # find the container
fleet_inspect { name: "agentarmy-arcadedb" }                # ports, env keys, status
fleet_logs    { name: "arcadedb", lines: 200, level: "error" }
fleet_logs    { name: "arcadedb", lines: 100, grep: "OOM" }
```

`fleet_logs` accepts service names from `ALLOWED_SERVICES` in `config.mjs` — not container IDs. Substring grep, not regex (ReDoS-safe).

### "Re-deploy backend-core after merging #123"

```
fleet_deploy { service: "backend-core", ref: "main" }
```

`fleet_deploy` will: `git fetch` → checkout `main` → `compose build backend-core` → `compose restart backend-core`. Refuses if the hub working tree is dirty (won't trample uncommitted operator work). Strict refname validation rejects `--upload-pack=cmd` and similar argv-smuggling attempts.

### "Reach the platform tier's logs the same way as a spoke's"

```
node tools/tail.mjs spawn --service arcadedb
# now `tail.mjs query --service arcadedb` works
```

Or use the MCP equivalent: `fleet_logs { name: "arcadedb" }`. Both paths read `docker logs --follow agentarmy-arcadedb` and write the same daily-rotated NDJSON to `tools/logs/`. The "container console" via `fleet_logs` is the OS-level fallback when everything else breaks.

## Audit log lookups

Every call appends a hash-chained NDJSON line to `tools/logs/mcp-audit.log.YYYY-MM-DD`. Each entry: `{ts, audit_id, principal, tool, args (redacted), duration_ms, remote_ip, prev_hash, hash}`.

```bash
# Last 50 audit entries
node tools/tail.mjs query --service mcp-audit --lines 50

# Calls from a specific cloud-agent identity
node tools/tail.mjs query --service mcp-audit --grep "cfaccess-edge:service:mcp-untool-gha-fleet-build"

# Chain integrity check (run weekly or after any incident)
node tools/mcp-local-fleet/verify-audit.mjs
```

If the verifier flags a broken chain, treat it as **tamper evidence**: capture the file, snapshot the host, and rotate every service token before resuming. The chain breaks if a single byte of any prior entry changes.

## Hard rules — enforced in code

- Bound to `127.0.0.1` only; public exposure requires the explicit `tunnel.mjs --name mcp` step.
- Constant-time bearer comparison; no token or JWT in any log line ever.
- `--grep` / `--level` are substring matches (not regex) — kills the ReDoS surface.
- **Allowlisted service names** only — cloud agents can't ask us to spawn arbitrary containers.
- **No shell-exec tool** — capability gaps become hub issues, not escape hatches.
- `fleet_deploy` strict refname validation rejects leading `-`, `..`, `//`, `--upload-pack=`, etc.
- Every call audited with redacted args + remote IP.

## What this is NOT for

- **Not a general control plane for ACA/Container Apps** — that's the cloud-side IaC pipeline (`templates/gcp-cloud-run/`, `templates/aca/`). The untool fleet suite targets the operator's *local* docker host. When `dev-cloud` / `test-cloud` instances land they will use the same suite shape against a cloud docker target — same tools, different `MCP_TARGET` label.
- **Not for external monetised APIs** — that's `api-gateway-engineer` (Azure APIM) territory when it arrives. The tunnel exposes frontend-only to the public web; the MCP is the *only* other thing on the public surface, and it's gated by CF Access.
- **Not a way to bypass the trust boundary on the Docker socket** — if you find yourself wanting `fleet_exec`, file a hub issue for a *named* primitive instead. Capability gaps become hub issues, not escape hatches.
