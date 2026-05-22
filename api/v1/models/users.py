"""User domain models — ORM table definition and Pydantic response schema.

Keeps the SQLAlchemy mapped class and the Pydantic output schema in the same
file so the field contract is visible in one place.  The ORM model is never
exposed directly to callers; the response schema is what leaves the API.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# ORM base (shared across all mapped classes in the application)
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# SQLAlchemy 2.0 mapped class — uses the typed Mapped[T] API
# ---------------------------------------------------------------------------
class User(Base):
    """users table."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Pydantic v2 response schema — decoupled from the ORM model
# ---------------------------------------------------------------------------
class UserResult(BaseModel):
    """A single user record returned by the search endpoint.

    model_config from_attributes=True allows Pydantic to read values from
    ORM instances directly without an explicit .model_validate(row.__dict__).
    """

    model_config = {"from_attributes": True}

    id: uuid.UUID = Field(description="Unique user identifier.")
    username: str = Field(description="Unique login handle.")
    email: EmailStr = Field(description="Primary email address.")
    display_name: str | None = Field(default=None, description="Human-readable display name.")
    created_at: datetime = Field(description="UTC timestamp of account creation.")
