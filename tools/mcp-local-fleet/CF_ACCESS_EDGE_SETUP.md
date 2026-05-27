# Cloudflare Access edge enforcement — operator setup guide

Goal: every request to `mcp.untool.ai/*` passes through CF Access enforcement
at Cloudflare's edge BEFORE reaching the MCP server. Unauthenticated traffic
is rejected at the edge (cheaper, never hits your machine).

The server-side support is already shipped — once you finish the dashboard
side and set one env var, the edge JWT path activates and replaces the
"paste a bearer per session" friction permanently.

## What you'll create

1. **One CF Access Self-Hosted Application** scoped to `mcp.untool.ai`
2. **One Access Policy** that allows your email (for browser/MCP-OIDC use)
   AND service tokens (for cloud agents)
3. **One or more Service Tokens** — pre-shared `(client_id, client_secret)`
   pairs for each cloud-agent identity

Time: ~20-30 minutes including waiting for DNS to propagate edge changes.

## Step-by-step

### 1. Open CF Zero Trust → Access → Applications

https://one.dash.cloudflare.com → Access → Applications → **Add an application**

### 2. Pick application type: **Self-hosted**

(Not SaaS — that's what we used for the claude.ai OIDC connector last night.
This is a different beast: we're protecting OUR OWN hostname.)

### 3. Application configuration

- **Application name**: `Local Fleet MCP API`
- **Session duration**: 24 hours (or whatever fits your auth UX)
- **Application domain**:
  - Type: Public hostname
  - Subdomain: `mcp`
  - Domain: `untool.ai`
  - Path: leave blank (protect the whole hostname) OR set `mcp` to protect
    only `/mcp*` and leave `/healthz` unprotected
- **Identity providers**: enable
  - The OTP/email IdP (or whichever you used last night)
  - **Service Auth** ← required for cloud agents

### 4. Note the AUD tag

After saving, the application shows an **Application Audience (AUD) Tag** —
a long hex string. Copy this. You'll set it as the `CF_ACCESS_EDGE_APP_AUD`
env var for the MCP server.

Looks like: `8c7e9f1a4b2d3c5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e`

### 5. Create Access Policy

Under the new application → Add a policy:

- **Policy name**: `Allow authorized identities`
- **Action**: Allow
- **Configure rules**:
  - Include: **Emails** → `nick@livecreative.com` (and any others you want)
  - Include: **Service Token** → start with "Any access service token"
    (you'll create the tokens next; once they exist you can scope this
    rule to specific tokens)

Save.

### 6. Generate Service Tokens for cloud agents

Access → **Service Auth** → Create Service Token

- Name each token after its consumer:
  `mcp-untool-claude-routine-1`, `mcp-untool-gha-build-1`, etc.
- Click Generate. CF shows the credentials **ONCE**:
  - `CF-Access-Client-Id: <id>.<account>.access`
  - `CF-Access-Client-Secret: <secret>`
- Copy both. Store in your Key Vault under appropriately-named secrets:
  ```bash
  az keyvault secret set --vault-name akv01-agentarmy \
    --name cf-access-svc-mcp-untool-claude-routine-1-id \
    --value '<id>.<account>.access'
  az keyvault secret set --vault-name akv01-agentarmy \
    --name cf-access-svc-mcp-untool-claude-routine-1-secret \
    --value '<secret>'
  ```

Repeat for each cloud-agent identity. Each gets its own token.

### 7. Configure the MCP server with the AUD tag

The server reads `CF_ACCESS_EDGE_APP_AUD` from env. Pick one option:

**Option A — local-dev (.claude/settings.local.json env block, gitignored):**
```jsonc
{
  "env": {
    "CF_ACCESS_EDGE_APP_AUD": "<your AUD tag>"
  }
}
```

**Option B — server-startup wrapper script:**
```powershell
$env:CF_ACCESS_EDGE_APP_AUD = "<your AUD tag>"
node tools/mcp-local-fleet/server.mjs
```

**Option C — hardcode in config.mjs** (if you're confident this AUD won't change):
edit `CF_ACCESS_EDGE_APP_AUD` default in `tools/mcp-local-fleet/config.mjs`.

### 8. Restart the MCP server

```bash
# kill existing
netstat -ano | grep ':8765 ' | awk '{print $NF}' | head -1 | xargs taskkill //F //PID
# relaunch
node tools/mcp-local-fleet/server.mjs &
```

Boot banner now shows the edge path is configured.

### 9. Test the edge enforcement

**Without auth — should 401 at the CF edge** (request never reaches our server):
```bash
curl -i https://mcp.untool.ai/mcp
# expect: HTTP/2 302 redirect to CF Access login page
```

**With service token — should reach our server and audit as cfaccess-edge:service:<name>**:
```bash
SVC_ID=$(az keyvault secret show --vault-name akv01-agentarmy \
  --name cf-access-svc-mcp-untool-claude-routine-1-id --query value -o tsv)
SVC_SECRET=$(az keyvault secret show --vault-name akv01-agentarmy \
  --name cf-access-svc-mcp-untool-claude-routine-1-secret --query value -o tsv)

curl -sS -X POST https://mcp.untool.ai/mcp \
  -H "CF-Access-Client-Id: $SVC_ID" \
  -H "CF-Access-Client-Secret: $SVC_SECRET" \
  -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

Check `tools/logs/mcp-audit.log.YYYY-MM-DD` — should see
`principal: cfaccess-edge:service:mcp-untool-claude-routine-1`.

### 10. Roll out to cloud agents

Each cloud agent that needs MCP access uses its own service token. No bearer
token, no env var paste, no JWT OAuth dance. Just two headers on every
request:

```
CF-Access-Client-Id: <id>
CF-Access-Client-Secret: <secret>
```

CF Access enforces auth at the edge, injects `Cf-Access-Jwt-Assertion`
with the verified identity, our server reads it.

## Revoking a cloud agent

CF Access → Service Auth → find the token → Delete.

Effect is **immediate at the edge** — no MCP server restart needed.

## Tightening later (optional)

Once you're confident the edge path is working for all consumers, you can
drop the legacy bearer fallback for non-localhost requests:

1. Edit `server.mjs` checkAuth to require `cf-access-jwt-assertion` when
   `req.headers["cf-connecting-ip"]` is present (i.e. came through CF).
2. Localhost can still use the legacy bearer (debug path).

This makes the bearer registry purely a localhost-debug tool. Cloud agents
must go through CF Access. Tighter security posture, zero loss of
functionality.

## Localhost stays open

Direct calls to `http://127.0.0.1:8765/mcp` from your laptop never go
through CF Access — they use the legacy bearer registry directly. This
keeps local dev fast and avoids requiring CF for every test.
