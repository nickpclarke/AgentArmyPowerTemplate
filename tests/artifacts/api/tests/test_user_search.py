"""Tests for GET /api/v1/users/search.

Coverage targets
----------------
* Happy path: matching results with correct pagination envelope
* Empty result set
* Pagination: limit/offset arithmetic, has_next flag
* Input validation: missing param, limit out of range, empty search_term
* Case-insensitive matching
* Match across all three searchable fields (username, email, display_name)
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.tests.conftest import create_user

SEARCH_URL = "/api/v1/users/search"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def seed_users(db: AsyncSession) -> None:
    """Insert a predictable set of users for search tests."""
    await create_user(db, username="alice_wonder", email="alice@example.com", display_name="Alice W")
    await create_user(db, username="bob_builder", email="bob@example.com", display_name="Bob B")
    await create_user(db, username="charlie", email="charlie@example.com", display_name="Charlie Chaplin")
    await create_user(db, username="diana", email="diana@example.com", display_name="Diana Prince")
    await create_user(db, username="eve_smith", email="eve@example.com", display_name="Eve S")


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------
class TestSearchHappyPath:
    @pytest.mark.asyncio
    async def test_returns_matching_users(
        self, async_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await seed_users(db_session)

        resp = await async_client.get(SEARCH_URL, params={"search_term": "alice"})

        assert resp.status_code == 200
        body = resp.json()
        assert body["pagination"]["total"] >= 1
        usernames = [u["username"] for u in body["results"]]
        assert "alice_wonder" in usernames

    @pytest.mark.asyncio
    async def test_response_envelope_shape(
        self, async_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await seed_users(db_session)

        resp = await async_client.get(SEARCH_URL, params={"search_term": "bob"})

        assert resp.status_code == 200
        body = resp.json()
        # Top-level keys
        assert set(body.keys()) == {"results", "pagination"}
        # Pagination meta keys
        assert set(body["pagination"].keys()) == {"total", "limit", "offset", "has_next"}
        # Result item keys
        item = body["results"][0]
        assert {"id", "username", "email", "display_name", "created_at"}.issubset(item.keys())

    @pytest.mark.asyncio
    async def test_case_insensitive_match(
        self, async_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await seed_users(db_session)

        resp = await async_client.get(SEARCH_URL, params={"search_term": "ALICE"})

        assert resp.status_code == 200
        assert resp.json()["pagination"]["total"] >= 1

    @pytest.mark.asyncio
    async def test_matches_by_email(
        self, async_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await seed_users(db_session)

        resp = await async_client.get(SEARCH_URL, params={"search_term": "charlie@example"})

        assert resp.status_code == 200
        assert resp.json()["pagination"]["total"] >= 1
        assert resp.json()["results"][0]["username"] == "charlie"

    @pytest.mark.asyncio
    async def test_matches_by_display_name(
        self, async_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await seed_users(db_session)

        resp = await async_client.get(SEARCH_URL, params={"search_term": "Chaplin"})

        assert resp.status_code == 200
        assert resp.json()["pagination"]["total"] >= 1


# ---------------------------------------------------------------------------
# Empty results
# ---------------------------------------------------------------------------
class TestSearchEmptyResults:
    @pytest.mark.asyncio
    async def test_no_match_returns_empty_list(
        self, async_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await seed_users(db_session)

        resp = await async_client.get(SEARCH_URL, params={"search_term": "zzz_no_match_xyz"})

        assert resp.status_code == 200
        body = resp.json()
        assert body["results"] == []
        assert body["pagination"]["total"] == 0
        assert body["pagination"]["has_next"] is False


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------
class TestPagination:
    @pytest.mark.asyncio
    async def test_limit_restricts_results(
        self, async_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await seed_users(db_session)

        resp = await async_client.get(
            SEARCH_URL, params={"search_term": "example", "limit": 2, "offset": 0}
        )

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["results"]) <= 2

    @pytest.mark.asyncio
    async def test_has_next_true_when_more_pages(
        self, async_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await seed_users(db_session)

        resp = await async_client.get(
            SEARCH_URL, params={"search_term": "example", "limit": 2, "offset": 0}
        )

        body = resp.json()
        total = body["pagination"]["total"]
        if total > 2:
            assert body["pagination"]["has_next"] is True

    @pytest.mark.asyncio
    async def test_has_next_false_on_last_page(
        self, async_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await seed_users(db_session)

        # Fetch with a large offset guaranteed to exhaust results
        resp = await async_client.get(
            SEARCH_URL, params={"search_term": "example", "limit": 100, "offset": 0}
        )

        body = resp.json()
        assert body["pagination"]["has_next"] is False

    @pytest.mark.asyncio
    async def test_offset_shifts_window(
        self, async_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        await seed_users(db_session)

        page1 = await async_client.get(
            SEARCH_URL, params={"search_term": "example", "limit": 2, "offset": 0}
        )
        page2 = await async_client.get(
            SEARCH_URL, params={"search_term": "example", "limit": 2, "offset": 2}
        )

        ids_p1 = {u["id"] for u in page1.json()["results"]}
        ids_p2 = {u["id"] for u in page2.json()["results"]}
        assert ids_p1.isdisjoint(ids_p2), "Pages must not overlap"

    @pytest.mark.asyncio
    async def test_default_limit_is_20(
        self, async_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        resp = await async_client.get(SEARCH_URL, params={"search_term": "x"})

        assert resp.status_code == 200
        assert resp.json()["pagination"]["limit"] == 20

    @pytest.mark.asyncio
    async def test_default_offset_is_0(
        self, async_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        resp = await async_client.get(SEARCH_URL, params={"search_term": "x"})

        assert resp.status_code == 200
        assert resp.json()["pagination"]["offset"] == 0


# ---------------------------------------------------------------------------
# Input validation — 422 Unprocessable Entity
# ---------------------------------------------------------------------------
class TestInputValidation:
    @pytest.mark.asyncio
    async def test_missing_search_term_returns_422(
        self, async_client: AsyncClient
    ) -> None:
        resp = await async_client.get(SEARCH_URL)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_search_term_returns_422(
        self, async_client: AsyncClient
    ) -> None:
        resp = await async_client.get(SEARCH_URL, params={"search_term": ""})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_limit_zero_returns_422(
        self, async_client: AsyncClient
    ) -> None:
        resp = await async_client.get(
            SEARCH_URL, params={"search_term": "alice", "limit": 0}
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_limit_exceeds_max_returns_422(
        self, async_client: AsyncClient
    ) -> None:
        resp = await async_client.get(
            SEARCH_URL, params={"search_term": "alice", "limit": 101}
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_negative_offset_returns_422(
        self, async_client: AsyncClient
    ) -> None:
        resp = await async_client.get(
            SEARCH_URL, params={"search_term": "alice", "offset": -1}
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_search_term_too_long_returns_422(
        self, async_client: AsyncClient
    ) -> None:
        resp = await async_client.get(
            SEARCH_URL, params={"search_term": "x" * 201}
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_non_integer_limit_returns_422(
        self, async_client: AsyncClient
    ) -> None:
        resp = await async_client.get(
            SEARCH_URL, params={"search_term": "alice", "limit": "abc"}
        )
        assert resp.status_code == 422
