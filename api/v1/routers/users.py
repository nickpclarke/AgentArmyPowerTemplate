"""User search router — GET /api/v1/users/search.

Design decisions
----------------
* search_term is a plain Query param validated here (min/max length) so the
  400/422 error happens before any DB round-trip.
* PaginationParams is injected via Depends() — FastAPI resolves limit/offset
  from the query string and runs field validators automatically.
* The route function is async; the SQLAlchemy queries use await so the event
  loop is never blocked on I/O.
* Two queries (COUNT + SELECT) run sequentially inside a single transaction.
  If you need them concurrent, see the python-pro escalation note in the
  module docstring at the bottom.
* response_model forces serialisation through PaginatedResponse[UserResult],
  which means ORM objects never leak raw data outside their declared schema.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.session import get_db
from api.v1.models.pagination import PaginatedResponse, PaginationMeta, PaginationParams
from api.v1.models.users import User, UserResult

router = APIRouter(prefix="/users", tags=["Users"])


# ---------------------------------------------------------------------------
# Query builder — keeps the route handler readable
# ---------------------------------------------------------------------------
def _build_search_query(search_term: str) -> Select:
    """Return a SELECT that filters users by username, email, or display_name.

    Uses ILIKE for case-insensitive partial matching.  For production-scale
    datasets replace this with a full-text GIN index query or a dedicated
    search service — that optimisation lives in python-pro / database-optimizer
    territory, not here.
    """
    pattern = f"%{search_term}%"
    return select(User).where(
        User.username.ilike(pattern)
        | User.email.ilike(pattern)
        | User.display_name.ilike(pattern)
    )


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------
@router.get(
    "/search",
    response_model=PaginatedResponse[UserResult],
    summary="Search users",
    description=(
        "Full-text partial match across username, email, and display_name. "
        "Returns a paginated envelope with total count and has_next flag."
    ),
    responses={
        200: {"description": "Paginated list of matching users."},
        422: {"description": "Validation error — check query parameter constraints."},
    },
)
async def search_users(
    search_term: Annotated[
        str,
        Query(
            min_length=1,
            max_length=200,
            description="Partial match string (case-insensitive) against username, email, display_name.",
            openapi_examples={"example": {"value": "alice"}},
        ),
    ],
    pagination: Annotated[PaginationParams, Depends(PaginationParams)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaginatedResponse[UserResult]:
    """Search users with pagination.

    Both COUNT and data queries share the same filter predicate; the helper
    _build_search_query() constructs the base Select so the predicate is
    defined exactly once.
    """
    base_query = _build_search_query(search_term)

    # -- total count (scalar subquery) ------------------------------------
    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total: int = count_result.scalar_one()

    # -- page data ---------------------------------------------------------
    rows = await db.execute(
        base_query
        .order_by(User.username)          # stable ordering is required for pagination
        .offset(pagination.offset)
        .limit(pagination.limit)
    )
    users = rows.scalars().all()

    return PaginatedResponse[UserResult](
        results=[UserResult.model_validate(u) for u in users],
        pagination=PaginationMeta(
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
        ),
    )
