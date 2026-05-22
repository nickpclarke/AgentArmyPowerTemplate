"""AgentArmy API — application factory and lifespan wiring.

Entry point::

    uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.db.session import engine
from api.v1.routers import users


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown hooks (replaces deprecated @app.on_event)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage engine lifecycle: pool is warmed on startup, disposed on shutdown."""
    # Yield control to the application; engine is already created at import time.
    yield
    # Graceful shutdown: drain the connection pool before the process exits.
    await engine.dispose()


# ---------------------------------------------------------------------------
# Application instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production via env var
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(users.router, prefix="/api/v1")
