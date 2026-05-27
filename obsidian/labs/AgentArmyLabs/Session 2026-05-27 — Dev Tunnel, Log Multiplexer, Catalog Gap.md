---
tags: [session-report, infra, tunnel, observability]
created: 2026-05-27
related:
  - "[[Cloud Agents → Local Docker — Control Plane Plan]]"
---

# Session 2026-05-27 — Dev Tunnel, Log Multiplexer, Catalog Gap

## Headline

- 🟢 **Cloudflare Tunnel running**, frontend reachable from phone at a real HTTPS URL.
- 🟢 **Dev-log multiplexer shipped** — `tools/tail.mjs` (NDJSON, daily rotation, 3-day TTL, query/grep over time windows).
- 🟢 **Vendor-agnostic tunnel wrapper shipped** — `tools/tunnel.mjs` with cloudflared default + ngrok adapter.
- 🟡 **`/objects` page broken** — middle-core has no `/catalog` endpoint. Filed as hub issue **#252** (Enabler, agent-army-task).
- 🟢 **Five hub PRs merged**: #243, #244, #245, #248, #251 — see PR-merge section.

## What started the session

User reported the in-app agent failed mid-conversation with:

```
agent_run_error_event
code: INCOMPLETE_STREAM
message: terminated
agentId: knowledge_copilot
```

Diagnosis (without logs at the time): two most likely causes both pointed at **backend-core's shared `httpx.AsyncClient` + Tavily upstream**:
1. `_TAVILY_TIMEOUT_SECONDS = 30.0` triggers a `ReadTimeout`. Middle-core's `tools.py` only catches `BackendUnavailable`; any other exception propagates into the LangGraph node and terminates the AG-UI stream without a clean `RUN_FINISHED` event.
2. Same `httpx.AsyncClient` singleton was left wedged after call 1, so call 2 timed out fast.

Could not confirm — no app logs existed yet. **That gap is the reason for the rest of the session.**

## What we built

### `tools/tail.mjs` — dev-log multiplexer

```
node tools/tail.mjs spawn [--service front|middle|back]   # supervise + capture stdout to NDJSON
node tools/tail.mjs tail                                   # follow today's files
node tools/tail.mjs query --since 5m --level error         # last 5 min, errors only
node tools/tail.mjs query --grep tavily --service middle   # search across logs
node tools/tail.mjs clean --days 1                         # tighten retention (default 3)
```

Design notes:
- No deps, single .mjs, matches house style (`tools/status.mjs`).
- NDJSON in `tools/logs/{svc}.log.YYYY-MM-DD` so `query` is trivially scriptable.
- `classify()` extracts level from arbitrary stdout via keyword matching (`ERROR`/`FATAL`/`TRACEBACK`/`WARN`/…) so even unstructured loggers slot in.
- Every invocation purges files older than `--days` (default 3) — verbose-but-purged, per user's brief.
- Argv arrays + `shell: false` for spawned services (no shell expansion, no command-injection surface — passes semgrep clean).

### `tools/tunnel.mjs` — vendor-agnostic tunnel wrapper

```
node tools/tunnel.mjs start [--vendor cloudflared|ngrok] [--port 3000]
node tools/tunnel.mjs status     # vendor, pid, url, since
node tools/tunnel.mjs url        # just print the URL
node tools/tunnel.mjs stop       # kill agent, clear state
node tools/tunnel.mjs logs       # tail today's tunnel log
```

Design notes:
- State (`{vendor, pid, port, url, startedAt}`) persisted to `tools/.tunnel-state.json` (gitignored) so `status`/`url`/`stop` work from any new shell.
- Spawned agent is detached and lives past this Node process — `start` exits as soon as it reads the URL out of the vendor's stdout.
- Vendor adapters are tiny: `{ bin, args, parseLine(line) → {url?, ready?} }`. Adding Microsoft Dev Tunnels later is ~10 lines.
- Both ngrok and cloudflared binary locations auto-detected from their winget install paths so it works before a shell restart picks up PATH.

### `tools/logs/.gitignore` + `tools/.gitignore`

- `tools/logs/.gitignore`: `*` except `.gitignore` itself — logs never get committed.
- `tools/.gitignore`: `.tunnel-state.json` — state file never gets committed.

### `CLAUDE.md` — new "Local debugging" section

Documents both wrappers, the tunnel-policy (frontend-only; middle/back stay behind the BFF; future external API exposure is `api-gateway-engineer` + Azure APIM, not a raw tunnel), and the vendor-choice rationale (cloudflared default; ngrok-free is broken for this network).

## What we learned the hard way

### ngrok-free.dev has broken IPv6 TLS for this network

Phone got `ERR_SSL_PROTOCOL_ERROR` on every attempt to `https://groggily-boat-barrel.ngrok-free.dev`. Reproduced from the laptop:

- `openssl s_client -6` → `packet length too long` after reading 5 bytes (truncated handshake)
- `openssl s_client -4` → unstable; sometimes "Verify return code: 0 (ok)" without a real cert chain
- Windows curl → `schannel SEC_E_INVALID_TOKEN`

Restarting ngrok kept the same hostname (account-deterministic). `--region eu` was deprecated in 3.39.5 — auto-region selection took us back to the same broken edge. **The ngrok-free edge node for our account is just broken for our network path.**

Switched to Cloudflare Tunnel ephemeral mode (`cloudflared tunnel --url ...`) — clean Google Trust Services cert on both IPv4 and IPv6, end-to-end Python fetch returns 200. Phone confirmed working.

Saved as memory `reference_tunnel_vendor.md` so future sessions don't burn the same hour.

### Cloudflare API token in KV was the wrong shape

User added `cloudflare` to Key Vault. The value (52 chars, `cfk_…`) was rejected by CF API with code 1000 "Invalid API Token". CF's canonical API tokens are 40 hex chars with no prefix; `cfk_` is something else (maybe a Workers/Stream key, maybe a truncated copy).

User opted to **delete it** rather than chase — for tunnel-only use we don't need an API token at all (the `cloudflared tunnel login` browser flow is sufficient when we want a stable subdomain on a CF zone).

KV secret soft-deleted; `ngrok` authtoken kept in case we ever pay for ngrok later (paid uses a different edge pool than free).

### The contract-first rule has a real cost when violated

`/objects` page (`BusinessObjectCatalog.tsx`) shipped against `/middle-core/catalog` — but **no producer was ever written**. Page fails to load. This is the canonical "contract-first & mock-first" violation. Filed as hub issue #252.

## Hub PRs merged

| # | Title | Type |
|---|---|---|
| #243 | chore(agents): compress descriptions to cut startup token bloat | chore |
| #244 | docs(claude-md): document agent-regen requirement in Gotchas | docs |
| #245 | docs(contracts): register Tavily upstream + document external-API vendoring pattern | docs |
| #248 | feat(secrets): KV-as-source-of-truth tooling + doctrine | feat |
| #251 | fix(commands): /ea-adr routes ADR work to the right sub-agent (explicit dispatch) | fix |

All five had green CI + mergeable status at time of merge.

## Control-plane Phase 1 — also shipped this session

After the wrap, user asked to "do that control-plane full on first" — so we built it. Same branch / PR #253 picks this up too.

`tools/mcp-local-fleet/` — minimal MCP server (HTTP + JSON-RPC 2.0, no deps, ~600 lines across 4 files):
- `server.mjs` — HTTP listener, bearer auth (constant-time compare), 256 KB body cap, JSON-RPC dispatcher
- `tools.mjs` — 10 tools registered: **4 Phase-1 fully working** (`fleet.tunnel_url`, `fleet.ps`, `fleet.inspect`, `fleet.logs`) + **6 Phase-2/3/4 stubs** (`fleet.{up,down,restart,build,deploy,test}`) that return `{not_implemented, phase, args, note}` so cloud agents see the full surface today
- `config.mjs` — token bootstrap from KV `local-fleet-mcp-key`; auto-generates 48-char token on first run via `cmd.exe /c az keyvault secret set` (Node 18+ blocks raw `.cmd` execution, CVE-2024-27980 — `cmd.exe /c` is the safe workaround)
- `audit.mjs` — append-only NDJSON audit log to `tools/logs/mcp-audit.log.YYYY-MM-DD`, redacts secret-shaped keys (`authorization|bearer|token|secret|password|api[_-]?key`)

`tools/tunnel.mjs` refactored to multi-tunnel: state now keyed by name, supports `start --name mcp` for the second tunnel exposing the MCP server. Legacy single-tunnel state auto-migrates as `frontend`.

`tools/tail.mjs` gained docker-logs ingestion: platform containers (arcadedb, postgres, nats, event-bridge) are now registered services that attach via `docker logs --follow <container>` instead of subprocess spawn. Same NDJSON pipeline, same `query` semantics. **This is the "container console fallback" you asked for** — if everything else is broken, `docker logs <ctr>` still works at the OS level; if not, `tail.mjs query` works at the NDJSON level; if the MCP server is up, cloud agents call `fleet.logs`. Three independent log paths, same data.

End-to-end smoke test passed: server starts, token created + stored in KV + printed once, `/healthz` 200, no-auth 401, `initialize` returns MCP capabilities, `tools/list` shows all 10 with phase+risk metadata, `fleet.ps` shows 4 platform containers healthy + 3 spokes, `fleet.logs arcadedb` routes through docker correctly, `fleet.restart` returns `not_implemented:true`, audit log records every call with redacted args + audit-id + duration.

**Hard rules baked into the code:**
- 127.0.0.1 only; tunnel exposure is an explicit second step
- Constant-time bearer compare
- Substring matching for grep/level (not regex — kills ReDoS surface, Semgrep CWE-1333)
- Allowlisted service names only; no shell-exec tool ever
- Body cap 256 KB; everything else is a bug or abuse
- Every call audited

## What's queued for the next session

1. **Stable tunnel URLs** (frontend + mcp) — add a Cloudflare-managed domain so the URLs don't change on restart. Without this, every dev box restart breaks the cloud-agent configs.
2. **Phase 2 implementation** (lifecycle: `fleet.{up,down,restart}`) — wraps `docker compose` for the platform allowlist. ~½ day.
3. **Phase 3 implementation** (`fleet.build`) — first capability that runs arbitrary code (your own Dockerfile). Needs idempotency keys + single-in-flight concurrency. ~1 day.
4. **Phase 4 implementation** (`fleet.deploy`, `fleet.test`) — git-pull + redeploy + test runners with streamed output. ~1-2 days.
5. **Catalog endpoint** — hub issue #252.
6. **Original `INCOMPLETE_STREAM`** — next repro now has both `tools/tail.mjs query` AND `fleet.logs` paths to grep.
