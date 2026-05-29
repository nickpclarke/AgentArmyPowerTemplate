"""Thin proxy to backend-core's ``POST /api/v1/ontology/abstract`` — the engine of the
abstraction meta-service (ARC-ADR-036). Kept separate from the MCP wiring so it has
NO mcp dependency and is unit-testable on its own.

The point of the proxy: the engine, the embedder, and the provider keys stay
server-side in backend-core. The MCP server only forwards a request (+ a bearer
token), so an *external* AI coding agent never needs our secrets, and an *internal*
agent calls the exact same surface — just a different ``ABSTRACTION_API_URL``.
"""
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

import httpx

DEFAULT_API = "http://127.0.0.1:8000"


def _api_base() -> str:
    base = (os.environ.get("ABSTRACTION_API_URL") or DEFAULT_API).rstrip("/")
    if urlparse(base).scheme not in ("http", "https"):
        raise ValueError(f"ABSTRACTION_API_URL must be http(s): {base!r}")
    return base


def _token() -> str:
    # Prefer a token FILE (rotate without restart) over an inline env var.
    path = os.environ.get("ABSTRACTION_TOKEN_FILE")
    if path and Path(path).exists():
        return Path(path).read_text(encoding="utf-8").strip()
    return os.environ.get("ABSTRACTION_TOKEN", "")


def _post(body: dict, timeout: float = 180.0) -> dict:
    headers = {"Content-Type": "application/json"}
    token = _token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = httpx.post(f"{_api_base()}/api/v1/ontology/abstract", json=body, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def abstract_schemas(schemas: list[dict], vocabulary: str = "api-interface") -> dict:
    """Concept-level: discover the canonical concepts shared across N API schemas, the
    per-source adapter map, and bottom-up proposals."""
    return _post({"schemas": schemas, "vocabulary": vocabulary, "mode": "concept"})


def build_adapter(schemas: list[dict], components: dict, vocabulary: str = "workitem-fields",
                  escalate: bool = True) -> dict:
    """Field-level: build a VALIDATED field adapter (canonical field <- source field),
    escalating the ambiguous band to a cited model, returning a snapped|quarantined
    verdict per source."""
    return _post({"schemas": schemas, "vocabulary": vocabulary, "mode": "field",
                  "components": components, "escalate": escalate, "run_validation": True})
