# Abstraction meta-service — MCP server

A **dedicated, single-purpose** MCP server for the abstraction meta-service
([ARC-ADR-036](../../docs/decisions/ARC-ADR-036-abstraction-validation-distribution-service.md)).
It is **not** part of the untool fleet (ops) MCP — that one drives Docker; this one
abstracts API schemas. Two clean tools, usable by **external and internal** AI coding
agents:

| Tool | Does |
|---|---|
| `abstract_schemas(schemas, vocabulary)` | discover the canonical concepts shared across N schemas + adapter map + bottom-up proposals |
| `build_adapter(schemas, components, vocabulary, escalate)` | a **validated** field-level adapter (canonical field ← source field), escalating the ambiguous band to a cited model; returns snapped (runtime-safe) or quarantined + reasons |

## How it stays clean + safe
It is a **thin proxy** to backend-core's `POST /api/v1/ontology/abstract`. The engine,
the embedder, and the provider keys stay server-side — an external agent never holds
our secrets, it just gets a tool result. `client.py` (the proxy) has no `mcp`
dependency and is unit-tested on its own.

## Configure (external agents — Claude Code, Cursor, …)

stdio, pointed at a reachable backend-core:

```jsonc
// .mcp.json / mcp config
{
  "mcpServers": {
    "agentarmy-abstraction": {
      "command": "python",
      "args": ["/abs/path/AgentArmy/tools/mcp-abstraction/server.py"],
      "env": {
        "ABSTRACTION_API_URL": "https://<backend-core-host>",
        "ABSTRACTION_TOKEN": "<bearer token with contributor/admin>"
      }
    }
  }
}
```

Claude Code one-liner:
```bash
claude mcp add agentarmy-abstraction -- python /abs/path/tools/mcp-abstraction/server.py
```

## Configure (internal agents — middle-core, fleet agents)
Same server, `ABSTRACTION_API_URL=http://127.0.0.1:8000` (or the in-cluster
backend-core URL) and `ABSTRACTION_TOKEN_FILE` pointing at a mounted token. middle-core
points its agent-runtime MCP config at this command.

## Hosted (external, no local spawn) — LIVE at `https://mcp.untool.ai/abstract`
Run it streamable-http on `:8181` and let the existing `untool-tunnel` route it:

```bash
MCP_TRANSPORT=streamable-http \
ABSTRACTION_API_URL=http://127.0.0.1:8000 \
ABSTRACTION_TOKEN_FILE=/abs/path/token \
python server.py            # serves /abstract on 127.0.0.1:8181
```

It is served at path **`/abstract`** (not the FastMCP default `/mcp`) so it sits **under
the existing `mcp.untool.ai` CF Access app** — no new subdomain, no new Access app, no new
DNS. The tunnel has a path rule `mcp.untool.ai ^/abstract → http://localhost:8181` ahead of
the `mcp.untool.ai → :8765` (ops-fleet) rule. The same two CF Access service tokens
(`claude-routine-1`, `claude-yml-hub`) authorize it.

> **DNS-rebinding note:** the MCP SDK 421s any non-localhost `Host`. We keep the protection
> on but allowlist the public host via `TransportSecuritySettings` (see `MCP_PUBLIC_HOST`).

Connect (external agent or a Claude.ai custom connector):
```jsonc
{ "type": "http", "url": "https://mcp.untool.ai/abstract",
  "headers": { "CF-Access-Client-Id": "<id>", "CF-Access-Client-Secret": "<secret>" } }
```

## Env
- `ABSTRACTION_API_URL` — backend-core base (default `http://127.0.0.1:8000`).
- `ABSTRACTION_TOKEN_FILE` (preferred, rotatable) or `ABSTRACTION_TOKEN` — bearer.
- `MCP_TRANSPORT` — `stdio` (default) | `sse` | `streamable-http`.
- `MCP_PATH` — HTTP mount path (default `/abstract`). *Avoid setting via Git Bash env —
  MSYS rewrites a leading-`/` value into a Windows path; pass it from a non-MSYS shell or
  rely on the default.*
- `MCP_PUBLIC_HOST` — host allowlisted for DNS-rebinding protection (default `mcp.untool.ai`).
