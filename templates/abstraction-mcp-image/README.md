# Abstraction meta-service MCP — function-tier image

The **durable container home** for the abstraction meta-service MCP server
([ARC-ADR-036](../../docs/decisions/ARC-ADR-036-abstraction-validation-distribution-service.md)).
On the operator box it runs as a logon Scheduled Task (`AgentArmy-AbstractionMCP`); this
image is what runs it **persistently on ACA** (function tier per [ARC-ADR-023](../../docs/decisions/ARC-ADR-023-container-tiering-strategy.md)).

It exposes exactly two tools — `abstract_schemas`, `build_adapter` — and **proxies**
backend-core's `POST /api/v1/ontology/abstract`. The engine, embedder, and provider keys
stay server-side, so an external AI coding agent never holds our secrets.

## No drift
The canonical server is `tools/mcp-abstraction/{server.py,client.py,requirements.txt}` —
the single source of truth, also used for stdio/local runs. This image does **not** vendor
a copy; its build context is the **repo root** and the Dockerfile copies the canonical files.

```bash
# from the repo root:
docker build -f templates/abstraction-mcp-image/Dockerfile -t agentarmy-abstraction-mcp .
docker run --rm agentarmy-abstraction-mcp            # doctor (offline correctness gate)
docker run --rm -p 8181:8181 \
  -e ABSTRACTION_API_URL=http://host.docker.internal:8000 \
  agentarmy-abstraction-mcp serve                    # run the MCP at /abstract on :8181
```

## Doctor (offline, no backend/keys)
`python doctor.py` proves: both tools registered, the streamable-http surface mounts at
`/abstract`, and the proxy refuses a non-http backend URL (keys stay server-side). The
live path (`https://mcp.untool.ai/abstract` through CF Access → MCP `initialize` 200) is
verified separately.

## Env
- `ABSTRACTION_API_URL` — backend-core base (default `http://host.docker.internal:8000`).
- `ABSTRACTION_TOKEN_FILE` (preferred, rotatable) or `ABSTRACTION_TOKEN` — bearer for backend-core.
- `MCP_PUBLIC_HOST` — host allowlisted for DNS-rebinding protection (default `mcp.untool.ai`).
- `MCP_HOST` / `MCP_PORT` / `MCP_TRANSPORT` — bind + transport (image defaults: `0.0.0.0` / `8181` / `streamable-http`).

## Deploy
Run `serve` as an ACA app (internal ingress on 8181). Front it via the existing
`mcp.untool.ai/abstract` tunnel path or ACA ingress, set `ABSTRACTION_API_URL` to the
in-cluster backend-core, and `MCP_PUBLIC_HOST` to the public host. See the parent
`tools/mcp-abstraction/README.md` for the CF Access hosting details.
