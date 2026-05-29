"""Dedicated, single-purpose MCP server for the AgentArmy abstraction meta-service
(ARC-ADR-036) — usable by external AND internal AI coding agents.

Deliberately NOT part of the untool fleet (ops) MCP: this server exposes exactly two
clean tools and proxies to backend-core's ``/abstract`` (keys stay server-side).

    stdio (a local/internal agent spawns it):   python tools/mcp-abstraction/server.py
    sse   (host behind CF Access for externals): MCP_TRANSPORT=sse python tools/mcp-abstraction/server.py

Config (env): ABSTRACTION_API_URL (default http://127.0.0.1:8000),
              ABSTRACTION_TOKEN_FILE or ABSTRACTION_TOKEN (bearer for backend-core).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # so `import client` works when spawned

import client  # noqa: E402
from mcp.server.fastmcp import FastMCP  # noqa: E402

# Port defaults to 8181 (the URL middle-core's .mcp.json points at) — NOT 8000,
# which backend-core owns. Overridable via MCP_HOST / MCP_PORT.
mcp = FastMCP(
    "agentarmy-abstraction",
    host=os.environ.get("MCP_HOST", "127.0.0.1"),
    port=int(os.environ.get("MCP_PORT", "8181")),
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
