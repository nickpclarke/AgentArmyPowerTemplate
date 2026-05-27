# local-fleet MCP server

Tiny MCP server that lets cloud agents (Claude.ai routines, GitHub Actions,
remote API callers) observe and — phase by phase — drive the local Docker
fleet without ever exposing the Docker socket directly.

**Why this exists:** [`Cloud Agents → Local Docker — Control Plane Plan`](../../obsidian/labs/AgentArmyLabs/Cloud%20Agents%20%E2%86%92%20Local%20Docker%20%E2%80%94%20Control%20Plane%20Plan.md)

## Run it

```bash
# Prereq: `az login` so the server can read/write Key Vault on your behalf.
node tools/mcp-local-fleet/server.mjs
```

**First run** generates a 48-char token, stores it in Azure Key Vault
(`akv01-agentarmy` secret `local-fleet-mcp-key`), and **prints the token to
the console once** so you can paste it into cloud-agent configs. Subsequent
runs read it silently — token never appears in any log line.

## Expose it publicly (for cloud agents)

If you have the stable named tunnel set up (untool.ai pattern):
```bash
# In a separate terminal, start the cloudflared connector once. The Cloudflare
# zone routes `mcp.untool.ai` at this tunnel and the connector forwards to
# http://localhost:8765. Token lives in KV (`cloudflare-tunnel-untool-ai`).
TUNNEL_TOKEN=$(az keyvault secret show --vault-name akv01-agentarmy \
  --name cloudflare-tunnel-untool-ai --query value -o tsv) \
  cloudflared tunnel run
# → public URL: https://mcp.untool.ai/mcp
```

Otherwise the quick-tunnel fallback:
```bash
node tools/tunnel.mjs start --name mcp   # ephemeral *.trycloudflare.com URL
node tools/tunnel.mjs url   --name mcp
```

Give the URL + bearer token to your cloud agent. The server binds to
`127.0.0.1` only — never accidentally reachable without an explicit tunnel.

## Consume it from a cloud agent

Each cloud agent (Claude.ai routine, GitHub Actions runner, microVM Claude
Code instance) configures one `mcpServers` entry. Identical shape to this
repo's `.mcp.json`:

```jsonc
"local-fleet": {
  "type": "http",
  "url": "https://mcp.untool.ai/mcp",
  "headers": { "Authorization": "Bearer ${LOCAL_FLEET_MCP_TOKEN}" }
}
```

The microVM/runner's bootstrap sets `LOCAL_FLEET_MCP_TOKEN` from its own
secret store (GitHub Actions secret, Anthropic-routine secret, etc.). Token
is what we generated/stored in `akv01-agentarmy/local-fleet-mcp-key`.

For local Claude Code on the laptop hosting this MCP server, the `.mcp.json`
default URL (`http://127.0.0.1:8765/mcp`) is used; the token is sourced from
`.claude/settings.local.json` (gitignored).

No Anthropic "Connections" catalog registration is needed — that catalog is
for OAuth-authenticated *public* MCP servers shown in the Claude.ai UI
dropdown. Private/custom servers go in via direct `mcpServers` config.

## Call it manually

```bash
TOKEN=$(az keyvault secret show --vault-name akv01-agentarmy \
  --name local-fleet-mcp-key --query value -o tsv)

# health (no auth)
curl http://127.0.0.1:8765/healthz

# list available tools
curl -X POST http://127.0.0.1:8765/mcp \
  -H 'content-type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# tail platform service logs
curl -X POST http://127.0.0.1:8765/mcp \
  -H 'content-type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call",
       "params":{"name":"fleet.logs",
                 "arguments":{"service":"arcadedb","since":"5m","limit":50}}}'
```

## Target labels (deployment environments)

Tools are universal docker primitives — they speak `docker compose`, which is
the same surface whether docker runs on the operator's office PC, a runner
box on the LAN, or an Azure VM. The **server instance** carries the "where
this is deployed" label so cloud agents can route to the right server.

```
MCP_TARGET=local-home   node tools/mcp-local-fleet/server.mjs   # default
MCP_TARGET=dev-cloud    node tools/mcp-local-fleet/server.mjs   # same code, different label
MCP_TARGET=local-runner node tools/mcp-local-fleet/server.mjs
```

The active target is advertised in:
- `serverInfo._meta.target` on the `initialize` response
- Every tool's `_meta.target` on `tools/list`

So a cloud agent that wants to act on "the operator's home PC" sees `target=local-home`
and knows it's talking to the right instance; a "dev-cloud" agent ignores
local-home and only calls servers it's been routed to for dev-cloud work.

**Today's taxonomy** (live + planned):

| Target | What |
|---|---|
| `local-home` ✅ | Operator's own dev box (a PC in their office). Reached via cloudflared tunnel at mcp.untool.ai. Today's only instance. |
| `local-runner` | A self-hosted runner on the operator's LAN — beefier machine for builds. |
| `dev-cloud` | Azure / GCP / ACA VM speaking docker — dev environment. |
| `test-cloud` | Same shape, the test environment. |
| `prod-edge` | Edge nodes, very narrow tool surface (build/deploy only — never restart/down). |

If a specific tool should NOT be exposed against certain targets (e.g.
`fleet.build` is dangerous on prod-edge), declare `availableOn: ["local-home", "dev-cloud"]`
in its registry entry and the server will hide it for other instances.

## Files

| File | Purpose |
|---|---|
| `server.mjs` | HTTP+JSON-RPC 2.0 endpoint, bearer auth, body cap, dispatcher |
| `tools.mjs` | Universal tool definitions (docker primitives — no per-instance config) |
| `registry.mjs` | Per-instance filter: hides tools whose `availableOn` doesn't include `MCP_TARGET` |
| `config.mjs` | Port, host, KV vault, instance target (`MCP_TARGET`), bearer-token bootstrap |
| `audit.mjs` | Append-only NDJSON audit log; redacts secret-shaped keys |

## Tools (current — scoped to Docker / CI-CD only)

| Tool | Phase | Risk | What |
|---|---|---|---|
| `fleet.ps`      | 1 | low  | List allowlisted platform containers + state |
| `fleet.inspect` | 1 | low  | Image / status / ports / env KEY names for one container (values redacted) |
| `fleet.logs`    | 1 | low  | Tail `docker logs <container>` for one allowlisted service. Refuses non-docker spoke names. |
| `fleet.up`      | 2 | med  | `docker compose -f templates/local-stack/docker-compose.yml up -d --no-build <svc>` |
| `fleet.down`    | 2 | med  | `compose stop <svc>` + `compose rm -f <svc>` (volumes preserved — platform tier is stateful) |
| `fleet.restart` | 2 | med  | `compose restart <svc>` |
| `fleet.build`   | 3 | high | `compose build [--no-cache] <svc>`. Single in-flight build per service (mutex). |

**Removed** (originally Phase 1/4, descoped to match the operator's "docker only" decision):
- `fleet.tunnel_url` — not docker-related; tunnel state is queried via `tools/tunnel.mjs status`
- `fleet.deploy` — git-pull-and-redeploy is out of MVP scope
- `fleet.test` — test runners can be invoked by the cloud-agent's own CI; not a docker concern

This roster is the minimum viable set for cloud action runners building images
and managing the local Docker compose stack.

## Hard rules (enforced in code)

1. **No Docker socket exposure, ever.** All Docker interactions go through
   `execFile("docker", [...whitelisted args...])`. The MCP server is the only
   code that talks to docker.
2. **Allowlisted service names only.** See `ALLOWED_SERVICES` in `config.mjs`.
   Adding a new service is a code change here.
3. **No shell-exec tool.** Capability gaps become hub issues, not escape
   hatches.
4. **Constant-time bearer comparison.** Length pre-check to avoid leaks via
   throw; `timingSafeEqual` on equal-length buffers.
5. **No regex on caller-supplied input.** `--grep`/`--level` are substring
   matches — kills the ReDoS surface (Semgrep CWE-1333).
6. **Bound to `127.0.0.1`.** Public exposure is an explicit second step.
7. **Body cap 256 KB.** JSON-RPC requests are tiny; anything larger is a bug
   or abuse.
8. **Audit log is append-only and required.** A mutating tool that bypasses
   `logCall()` is a bug.

## Logs & retention

- Audit log: `tools/logs/mcp-audit.log.YYYY-MM-DD` (NDJSON)
- Tunnel log: `tools/logs/tunnel.log.YYYY-MM-DD` (per-line vendor stdout)
- Spoke logs (if started via tail.mjs): `tools/logs/<service>.log.YYYY-MM-DD`

All purged together by `node tools/tail.mjs clean --days N` (default 3 days).
