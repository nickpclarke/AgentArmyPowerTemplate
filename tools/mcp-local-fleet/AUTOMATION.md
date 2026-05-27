# Cloud-agent auth automation — no more paste-the-token

Two paths, deploy independently. Use both together for the cleanest setup.

## Path A — bake env vars into the routine prompt

The cloud microVM's Claude Code reads `.mcp.json` and substitutes env vars at
process startup. If `LOCAL_FLEET_MCP_URL` + `LOCAL_FLEET_MCP_TOKEN` aren't
in the env at boot, the MCP client connects with empty bearer → 401. Pasting
into the chat is too late.

**Solution**: bake the env vars into the routine's PROMPT so the cloud
agent runs `export X=Y` before any tool call. The MCP client doesn't see
them, but every curl/HTTP call from the cloud agent does. (Sufficient for
the proven curl-based test pattern.)

### Routine creation template

When you use `/schedule` to create a routine, structure the prompt like:

```
Bootstrap (run these first):
  export LOCAL_FLEET_MCP_URL=https://mcp.untool.ai/mcp
  export LOCAL_FLEET_MCP_TOKEN=<bearer-token-value>
  export UA='Mozilla/5.0 ...'

Your task:
  <whatever you want the routine to do>
  
Use $URL / $TOKEN / $UA when calling mcp.untool.ai endpoints via curl.
```

Trust boundary: the token now lives in the routine config at Anthropic
(same trust as any other routine prompt). Acceptable for development.

## Path B — multi-token KV registry (provisioned this commit)

Each cloud-agent identity gets its OWN bearer token. The MCP server reads
all KV secrets matching `local-fleet-mcp-token-*` at startup AND the legacy
`local-fleet-mcp-key`. Auth log records WHICH identity called.

### Provision a new per-agent token

```bash
# Generate + store. The value is the bearer the agent will send.
TOK=$(node -e "console.log(require('crypto').randomBytes(36).toString('base64url'))")
az keyvault secret set --vault-name akv01-agentarmy \
  --name local-fleet-mcp-token-<agent-id> --value "$TOK"

# Restart the server so it picks up the new token
# (no live reload by design — KV-list-per-request would dominate latency)
# kill + relaunch the MCP server process.
```

The agent now authenticates with `Authorization: Bearer $TOK`. Audit log
shows `principal: token:<agent-id>` on every call.

### Revoke a per-agent token

```bash
az keyvault secret delete --vault-name akv01-agentarmy \
  --name local-fleet-mcp-token-<agent-id>
# Restart the MCP server. The token is now rejected.
```

The legacy `local-fleet-mcp-key` continues to work (as principal
`token:static-legacy`) so curl tests and existing consumers aren't broken.

### Suggested naming convention

`local-fleet-mcp-token-<consumer>-<env>-<n>` — e.g.
`local-fleet-mcp-token-claude-routine-prod-1`,
`local-fleet-mcp-token-gha-build-1`,
`local-fleet-mcp-token-nicky-phone-1`.

## Combining A + B for full automation

1. Provision a dedicated token per routine type (`local-fleet-mcp-token-claude-routine-1`).
2. Bake its value into the routine prompt (Path A).
3. The cloud agent uses its dedicated token. Audit attribution is clean.
4. To revoke that routine's access: delete the KV secret + restart MCP
   server. The token is dead; the routine fails until a new token is
   provisioned. No other consumer is affected.

## Future: edge-enforced auth via CF Access service tokens

The app-layer registry in this commit is the simpler version of CF Access
service tokens. The proper edge-enforced version would:

1. Configure `mcp.untool.ai/*` as a CF Access Self-Hosted Application
   (separate from our existing OIDC SaaS app).
2. CF Access enforces auth at the edge; unauthenticated requests never
   reach our server.
3. Cloud agents send `CF-Access-Client-Id` + `CF-Access-Client-Secret`
   headers (issued by CF Access service-token generator).
4. Our server reads `CF-Access-Authenticated-User-Email` injected by
   CF Access, replaces the bearer registry with header reading.

The migration is a server-side drop-in replacement. Schedule when you have
CF dashboard time.
