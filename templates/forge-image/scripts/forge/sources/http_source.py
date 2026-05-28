"""HTTP source — fetches backend-core's /ontology/snapshot (or any HTTP URL).

Implements conditional GET via `If-None-Match: <etag>` per BE-7's contract:
when the server returns 304 we surface that as an empty SourceResult so the
caller knows it can skip a generation cycle.

Bearer auth via env `FORGE_HTTP_BEARER` (optional — backend-core may be
inside the same network and auth-free for fleet calls, or behind a sidecar).
"""
from __future__ import annotations

import os
from typing import Optional

import httpx

from . import SourceResult


def load(uri: str, *, if_none_match: Optional[str] = None) -> SourceResult:
    headers: dict[str, str] = {
        "Accept": "text/turtle, application/ld+json, application/n-triples;q=0.9, "
        "application/x-yaml;q=0.8, text/yaml;q=0.7, */*;q=0.5",
    }
    if if_none_match:
        headers["If-None-Match"] = if_none_match
    bearer = os.getenv("FORGE_HTTP_BEARER")
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"

    with httpx.Client(timeout=httpx.Timeout(30.0)) as client:
        resp = client.get(uri, headers=headers, follow_redirects=True)
    if resp.status_code == 304:
        # Caller can short-circuit on this. We still return a SourceResult so
        # they can read the etag back and log the no-op.
        return SourceResult(bytes=b"", source_uri=uri, etag=if_none_match)
    if resp.status_code >= 400:
        raise RuntimeError(
            f"HTTP source fetch failed: {uri} -> {resp.status_code}: {resp.text[:200]}"
        )
    return SourceResult(
        bytes=resp.content,
        source_uri=uri,
        etag=resp.headers.get("ETag"),
    )
