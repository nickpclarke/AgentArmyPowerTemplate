"""Async SQLAlchemy session factory for PostgreSQL.

Provides a request-scoped AsyncSession via FastAPI dependency injection.
Connection pool settings are tuned for a typical ASGI worker configuration;
tune pool_size / max_overflow at the deployment layer (environment variables).
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.config import settings

# ---------------------------------------------------------------------------
# Engine
# One engine per process — created once at import time, reused across requests.
# ---------------------------------------------------------------------------
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,   # detect stale connections before each checkout
    echo=settings.db_echo,
)

# ---------------------------------------------------------------------------
# Session factory
# expire_on_commit=False avoids lazy-load errors after commit in async code.
# ---------------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# FastAPI dependency — yields a session, guarantees close on teardown
# ---------------------------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped async database session.

    Usage::

        @router.get("/")
        async def my_route(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
