"""Azure Blob source — `azureblob://<account>/<container>/<key>`.

Auth precedence:
  1. `AZURE_STORAGE_CONNECTION_STRING` (dev convenience; full SAS or shared key)
  2. `DefaultAzureCredential` (managed identity in production; Az CLI locally)

The dev doctor sets `SKIP_AZURE=1` to PASS-with-skip when no creds are
configured — see scripts/forge-doctor.sh. Production deployments should use
managed identity and remove the env entirely.
"""
from __future__ import annotations

import os
from typing import Optional
from urllib.parse import urlparse

from . import SourceResult


def load(uri: str) -> SourceResult:
    account, container, key = _parse_uri(uri)
    conn = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

    # Lazy import — azure-storage-blob is heavy and the doctor's SKIP_AZURE
    # path doesn't want to pay the import cost.
    from azure.storage.blob import BlobServiceClient  # type: ignore[import-not-found]

    if conn:
        client: "BlobServiceClient" = BlobServiceClient.from_connection_string(conn)
    else:
        from azure.identity import DefaultAzureCredential  # type: ignore[import-not-found]

        cred = DefaultAzureCredential()
        client = BlobServiceClient(
            account_url=f"https://{account}.blob.core.windows.net",
            credential=cred,
        )

    blob = client.get_blob_client(container=container, blob=key)
    data = blob.download_blob().readall()
    return SourceResult(bytes=bytes(data), source_uri=uri)


def _parse_uri(uri: str) -> tuple[str, str, str]:
    """`azureblob://account/container/key` -> (account, container, key)."""
    parsed = urlparse(uri)
    if parsed.scheme != "azureblob":
        raise ValueError(f"not an azureblob:// URI: {uri!r}")
    account = parsed.netloc
    path = parsed.path.lstrip("/")
    if "/" not in path:
        raise ValueError(f"azureblob URI missing container/key: {uri!r}")
    container, key = path.split("/", 1)
    return account, container, key


# Re-export the typing helper for callers — saves a `from typing import`.
__all__ = ["load"]
_Optional = Optional  # noqa: F841
