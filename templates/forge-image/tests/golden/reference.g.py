"""@generated — emitted by agentarmy-forge.

forge.version: 0.1.0
model.version: 1.0.0
source.uri:    file:///work/reference.model.yaml

DO NOT EDIT. Re-run forge against the source ontology to regenerate.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    """Platform user"""
    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    handle: str
    created_at: datetime
    documents: list['Document'] = []


class Document(BaseModel):
    """Knowledge document"""
    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    title: str
    body: Optional[str] = None
    word_count: int
    created_at: datetime
    author: Optional['User'] = None


User.model_rebuild()
Document.model_rebuild()
