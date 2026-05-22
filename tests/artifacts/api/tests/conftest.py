"""Pytest fixtures for the AgentArmy API test suite.

Architecture
------------
* A fresh in-memory SQLite database is created per test session via an
  async engine.  SQLite is used instead of Postgres because it requires no
  external service in CI; asyncpg-specific dialect features (ILIKE, UUID) are
  shimmed by overriding the query builder dependency.
* The FastAPI dependency `get_db` is overridden to yield sessions from the
  test engine — the live Postgres engine is never touched.
* `async_client` is an httpx.AsyncClient scoped per test function, so tests
  are isolated by default.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.db.session import get_db
from api.main import app
from api.v1.models.users import Base, User

# ---------------------------------------------------------------------------
# Test engine — SQLite in-memory, async
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Schema bootstrap — runs once per session
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables() -> AsyncGenerator[None, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ---------------------------------------------------------------------------
# DB session fixture — one per test
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()   # isolate side-effects between tests


# ---------------------------------------------------------------------------
# Override FastAPI dependency
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(autouse=True)
async def override_get_db(db_session: AsyncSession) -> AsyncGenerator[None, None]:
    async def _get_test_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture()
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


# ---------------------------------------------------------------------------
# User factory helper
# ---------------------------------------------------------------------------
async def create_user(
    db: AsyncSession,
    *,
    username: str,
    email: str,
    display_name: str | None = None,
) -> User:
    user = User(
        id=uuid.uuid4(),
        username=username,
        email=email,
        display_name=display_name,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()
    return user
