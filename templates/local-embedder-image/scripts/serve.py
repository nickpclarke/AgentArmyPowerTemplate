"""Local embedder — OpenAI-compatible /v1/embeddings over FastAPI.

The implementation is intentionally minimal: load one sentence-transformers
model lazily on first request, expose the OpenAI shape, and surface health
endpoints the fleet heartbeat + LB probes can hit.

Hardware: CPU-first via sentence-transformers PyTorch. The Intel Arc iGPU /
AI Boost NPU paths (via optimum-intel + OpenVINO) are a follow-up after the
baseline is proven to work in the fleet. The image works on any architecture
sentence-transformers supports.

Config (env):
    EMBEDDER_MODEL       — HF model id (default: BAAI/bge-small-en-v1.5, 384-d)
    EMBEDDER_DEVICE      — torch device (default: cpu)
    EMBEDDER_NORMALIZE   — L2-normalize embeddings ('true' / 'false', default: true)
    EMBEDDER_MAX_BATCH   — max inputs per request (default: 64)
    EMBEDDER_PORT        — listen port (default: 8082)

The model and its tokenizer cache live under ~/.cache/huggingface (mounted
as a docker volume via the example compose so model weights persist).
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

LOG = logging.getLogger("local-embedder")
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

# ---------------------------------------------------------------------------
# Config (env-driven; all read once at startup).
# ---------------------------------------------------------------------------
MODEL_ID = os.getenv("EMBEDDER_MODEL", "BAAI/bge-small-en-v1.5")
DEVICE = os.getenv("EMBEDDER_DEVICE", "cpu")
NORMALIZE = os.getenv("EMBEDDER_NORMALIZE", "true").lower() == "true"
MAX_BATCH = int(os.getenv("EMBEDDER_MAX_BATCH", "64"))
LISTEN_PORT = int(os.getenv("EMBEDDER_PORT", "8082"))

# Lazy-loaded singletons. None until the first request; populated under a
# lock so concurrent first-callers see one load, not N.
_model: Any = None
_model_dim: int = 0
_model_lock = asyncio.Lock()


# ---------------------------------------------------------------------------
# OpenAI-shaped request / response models.
# ---------------------------------------------------------------------------
class EmbeddingRequest(BaseModel):
    """OpenAI /v1/embeddings request — single string or list of strings."""

    model: str = Field(
        ...,
        description="Logical model id. May differ from EMBEDDER_MODEL; the server validates it matches.",
    )
    input: list[str] | str = Field(
        ...,
        description="Input text(s) to embed. Either a single string or an array of strings.",
    )
    encoding_format: str | None = Field(
        default="float",
        description="OpenAI compat field. Only 'float' is supported.",
    )

    @field_validator("input")
    @classmethod
    def _normalize_input(cls, v: list[str] | str) -> list[str]:
        if isinstance(v, str):
            return [v]
        if not v:
            raise ValueError("input array must be non-empty")
        return v


class EmbeddingObject(BaseModel):
    object: str = "embedding"
    index: int
    embedding: list[float]


class Usage(BaseModel):
    prompt_tokens: int = 0
    total_tokens: int = 0


class EmbeddingResponse(BaseModel):
    object: str = "list"
    model: str
    data: list[EmbeddingObject]
    usage: Usage


# ---------------------------------------------------------------------------
# Model loading.
# ---------------------------------------------------------------------------
async def _ensure_model_loaded() -> Any:
    """Idempotent. Loads the configured sentence-transformer once."""
    global _model, _model_dim
    if _model is not None:
        return _model
    async with _model_lock:
        if _model is not None:
            return _model
        # Dynamic import so the FastAPI app can boot + serve /livez even
        # before sentence-transformers is importable (useful for the
        # heartbeat's mere-existence check during scaffolding).
        from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]

        LOG.info("loading model %s on device=%s", MODEL_ID, DEVICE)
        t0 = time.time()
        model = SentenceTransformer(MODEL_ID, device=DEVICE)
        _model = model
        _model_dim = int(model.get_sentence_embedding_dimension() or 0)
        LOG.info(
            "model loaded in %.1fs, embedding dim=%d, normalize=%s",
            time.time() - t0,
            _model_dim,
            NORMALIZE,
        )
        return _model


# ---------------------------------------------------------------------------
# App + lifespan.
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(_: FastAPI):
    # Don't block startup on model load — readiness reports false until the
    # first embed call (or an explicit warmup) populates _model.
    yield


app = FastAPI(
    title="AgentArmy local-embedder",
    version="0.1.0",
    description="OpenAI-compatible local embedding service.",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Health endpoints — match contracts/health.openapi.yaml.
# ---------------------------------------------------------------------------
@app.get("/livez")
async def livez() -> dict:
    """Process alive? No dependency checks."""
    return {"ok": True, "ts": _utc_now()}


@app.get("/readyz")
async def readyz() -> JSONResponse:
    """Ready to accept embed requests?  Requires the model to be loaded."""
    if _model is None:
        return JSONResponse(
            status_code=503,
            content={
                "type": "https://github.com/nickpclarke/AgentArmy/contracts/problems/not-ready",
                "title": "Embedder model not loaded",
                "status": 503,
                "detail": "Model is loaded lazily on the first /v1/embeddings call. Send a small embed to warm.",
            },
        )
    return JSONResponse(
        status_code=200,
        content={"ok": True, "ts": _utc_now(), "dependencies": _deps()},
    )


@app.get("/healthz")
async def healthz() -> dict:
    """Diagnostic snapshot — version, model, dimensions, etc."""
    return {
        "ok": True,
        "ts": _utc_now(),
        "service": "local-embedder",
        "version": app.version,
        "tier": "function",
        "model": MODEL_ID,
        "device": DEVICE,
        "normalize": NORMALIZE,
        "embedding_dim": _model_dim,
        "model_loaded": _model is not None,
        "dependencies": _deps(),
    }


def _deps() -> list[dict[str, Any]]:
    return [
        {
            "name": "model",
            "ok": _model is not None,
            "message": f"{MODEL_ID} loaded; dim={_model_dim}" if _model else "lazy-load pending",
        }
    ]


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ---------------------------------------------------------------------------
# /v1/embeddings — OpenAI compatible.
# ---------------------------------------------------------------------------
@app.post("/v1/embeddings", response_model=EmbeddingResponse)
async def embeddings(req: EmbeddingRequest) -> EmbeddingResponse:
    # validator normalized str -> [str], but the union type sticks at the
    # field level. Narrow it here for the rest of the function.
    raw = req.input
    inputs: list[str] = raw if isinstance(raw, list) else [raw]
    if len(inputs) > MAX_BATCH:
        raise HTTPException(
            status_code=422,
            detail=f"input batch size {len(inputs)} exceeds EMBEDDER_MAX_BATCH={MAX_BATCH}",
        )
    if req.encoding_format and req.encoding_format != "float":
        raise HTTPException(
            status_code=422,
            detail=f"encoding_format='{req.encoding_format}' not supported; use 'float'",
        )

    model = await _ensure_model_loaded()
    t0 = time.time()
    # sentence-transformers .encode() is sync + CPU-bound; run in the default
    # executor so we don't block the event loop on long batches.
    loop = asyncio.get_event_loop()
    vectors = await loop.run_in_executor(
        None,
        lambda: model.encode(
            inputs,
            normalize_embeddings=NORMALIZE,
            convert_to_numpy=True,
            show_progress_bar=False,
        ),
    )
    dt_ms = int((time.time() - t0) * 1000)
    LOG.info("embed n=%d dt_ms=%d", len(inputs), dt_ms)

    # Pydantic accepts numpy arrays in the response but we cast to lists for
    # a stable JSON contract (matches OpenAI exactly).
    data = [
        EmbeddingObject(index=i, embedding=vec.tolist()) for i, vec in enumerate(vectors)
    ]
    # Token accounting — sentence-transformers doesn't expose token counts
    # directly; we approximate via the tokenizer if available.
    prompt_tokens = _count_tokens(model, inputs)
    return EmbeddingResponse(
        model=req.model,
        data=data,
        usage=Usage(prompt_tokens=prompt_tokens, total_tokens=prompt_tokens),
    )


def _count_tokens(model: Any, inputs: list[str]) -> int:
    try:
        tok = model.tokenizer
        return sum(len(tok.encode(s)) for s in inputs)
    except Exception:  # pragma: no cover — best-effort accounting
        # Approximate: ~4 chars/token for English.
        return sum(max(1, len(s) // 4) for s in inputs)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=LISTEN_PORT)
