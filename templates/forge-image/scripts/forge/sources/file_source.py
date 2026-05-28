"""Local file source — reads `file://`/absolute paths into bytes."""
from __future__ import annotations

import os
from urllib.parse import unquote, urlparse

from . import SourceResult


def load(uri: str) -> SourceResult:
    path = _path_from_uri(uri)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"file not found: {path}")
    with open(path, "rb") as f:
        data = f.read()
    return SourceResult(bytes=data, source_uri=uri)


def _path_from_uri(uri: str) -> str:
    if uri.startswith("file://"):
        parsed = urlparse(uri)
        path = unquote(parsed.path)
        # On Windows, urlparse leaves a leading slash before drive letters
        # ("/C:/foo"). Strip it so os.path treats it as native.
        if os.name == "nt" and len(path) >= 3 and path[0] == "/" and path[2] == ":":
            path = path[1:]
        return path
    return uri
