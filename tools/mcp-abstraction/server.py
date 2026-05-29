"""Dedicated, single-purpose MCP server for the AgentArmy abstraction meta-service
(ARC-ADR-036) — usable by external AND internal AI coding agents.

Deliberately NOT part of the untool fleet (ops) MCP: this server exposes exactly two
clean tools and proxies to backend-core's ``/abstract`` (keys stay server-side).

    stdio (a local/internal agent spawns it):   python tools/mcp-abstraction/server.py
    http  (host behind CF Access for externals): MCP_TRANSPORT=streamable-http python tools/mcp-abstraction/server.py

The HTTP endpoint is served at path ``/abstract`` (not the FastMCP default ``/mcp``), so
it slots cleanly under the existing ``mcp.untool.ai`` CF Access app as
``https://mcp.untool.ai/abstract`` — no new subdomain, no new Access app. Locally that is
``http://127.0.0.1:8181/abstract``.

Config (env): ABSTRACTION_API_URL (default http://127.0.0.1:8000),
              ABSTRACTION_TOKEN_FILE or ABSTRACTION_TOKEN (bearer for backend-core),
              MCP_PATH (default /abstract), MCP_HOST (127.0.0.1), MCP_PORT (8181).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # so `import client` works when spawned

import client  # noqa: E402
from mcp.server.fastmcp import FastMCP  # noqa: E402
from mcp.server.transport_security import TransportSecuritySettings  # noqa: E402

# DNS-rebinding protection stays ON. FastMCP's localhost default only trusts
# localhost Host/Origin, so when fronted by the CF tunnel (which forwards
# Host: mcp.untool.ai) the SDK would 421 "Invalid Host header". We explicitly
# allowlist the public host alongside localhost rather than disabling the check.
_public = os.environ.get("MCP_PUBLIC_HOST", "mcp.untool.ai")
_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=[_public, "127.0.0.1:*", "localhost:*", "[::1]:*"],
    allowed_origins=[f"https://{_public}", "http://127.0.0.1:*", "http://localhost:*"],
)

# Port defaults to 8181 (the URL middle-core's .mcp.json points at) — NOT 8000,
# which backend-core owns. Served at path /abstract so it sits under the existing
# mcp.untool.ai CF Access app. Overridable via MCP_HOST / MCP_PORT / MCP_PATH.
mcp = FastMCP(
    "agentarmy-abstraction",
    host=os.environ.get("MCP_HOST", "127.0.0.1"),
    port=int(os.environ.get("MCP_PORT", "8181")),
    streamable_http_path=os.environ.get("MCP_PATH", "/abstract"),
    transport_security=_security,
)


@mcp.tool()
def abstract_schemas(schemas: list[dict], vocabulary: str = "api-interface") -> dict:
    """Discover the canonical concepts shared across N API schemas, plus the per-source
    adapter map and bottom-up proposals.

    schemas: list of {"name": str, "spec": <OpenAPI/AsyncAPI/JSON-Schema dict>}.
    vocabulary: api-interface | business-mid | board | workitem-fields.
    Returns: {canonical[], adapters{}, divergences[], proposed[], summary{}}.
    """
    return client.abstract_schemas(schemas, vocabulary)


@mcp.tool()
def build_adapter(schemas: list[dict], components: dict, vocabulary: str = "workitem-fields",
                  escalate: bool = True) -> dict:
    """Build a VALIDATED field-level adapter (canonical field <- source field) across N
    schemas — the runtime-safe mapping an integration applies.

    Ambiguous fields escalate to a cited model; the result includes a per-source
    validation verdict: snapped (runtime-safe) or quarantined (+ the reasons).
    components: {source_name: [component types to extract fields from]}.
    """
    return client.build_adapter(schemas, components, vocabulary, escalate)


if __name__ == "__main__":
    mcp.run(transport=os.environ.get("MCP_TRANSPORT", "stdio"))  # type: ignore[arg-type]
