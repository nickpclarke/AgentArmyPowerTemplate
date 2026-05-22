"""Reusable pagination primitives.

PaginationParams is injected as a dependency; PaginationMeta is embedded in
every paginated response envelope.  Both are generic so callers can type the
'results' field to whatever item schema they need.
"""

from typing import Annotated, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field, computed_field

ItemT = TypeVar("ItemT")


# ---------------------------------------------------------------------------
# Query-parameter dependency
# ---------------------------------------------------------------------------
class PaginationParams(BaseModel):
    """Validated pagination query parameters injected via Depends().

    FastAPI resolves each field from the query string automatically when the
    model is declared as a dependency using Depends(PaginationParams).
    Field-level constraints (ge/le) generate correct OpenAPI schema and raise
    422 Unprocessable Entity with structured error detail on violation — no
    manual validation code needed.
    """

    model_config = {"frozen": True}  # params are read-only after construction

    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            description="Maximum number of results to return (1–100).",
            openapi_examples={"default": {"value": 20}},
        ),
    ] = 20

    offset: Annotated[
        int,
        Query(
            ge=0,
            description="Number of results to skip before returning data.",
            openapi_examples={"default": {"value": 0}},
        ),
    ] = 0


# ---------------------------------------------------------------------------
# Response envelope
# ---------------------------------------------------------------------------
class PaginationMeta(BaseModel):
    """Pagination metadata returned with every paginated response."""

    total: int = Field(ge=0, description="Total number of records matching the query.")
    limit: int = Field(ge=1, description="Page size requested.")
    offset: int = Field(ge=0, description="Number of records skipped.")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_next(self) -> bool:
        """True when more records exist beyond the current page."""
        return self.offset + self.limit < self.total


class PaginatedResponse(BaseModel, Generic[ItemT]):
    """Generic paginated response envelope.

    Usage::

        PaginatedResponse[UserResult]
    """

    results: list[ItemT]
    pagination: PaginationMeta
