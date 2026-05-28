"""Input source adapters — turn a URI into (bytes, content-type, source_uri).

Three flavors:
  * file://path/to/model.{yaml,ttl,jsonld,nt}
  * http://host/path  /  https://host/path
  * azureblob://account/container/key  (managed identity preferred)

Each returns a `SourceResult` so callers can pick a parser by extension.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class SourceResult:
    bytes: bytes
    source_uri: str
    """Original input URI — threaded into IR for emitter file-headers."""
    etag: Optional[str] = None
    """ETag from HTTP responses, for conditional GET on the next poll."""


def load(uri: str, *, if_none_match: Optional[str] = None) -> SourceResult:
    """Dispatch to the right source adapter by URI scheme."""
    if uri.startswith("file://") or uri.startswith("/") or (
        len(uri) >= 2 and uri[1] == ":"
    ):
        # Win32 absolute path like C:\foo is treated as file://
        from . import file_source

        return file_source.load(uri)
    if uri.startswith("azureblob://"):
        from . import blob_source

        return blob_source.load(uri)
    if uri.startswith("http://") or uri.startswith("https://"):
        from . import http_source

        return http_source.load(uri, if_none_match=if_none_match)
    raise ValueError(f"unsupported source scheme: {uri!r}")
