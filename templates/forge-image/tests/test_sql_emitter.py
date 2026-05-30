"""Tests for the forge SQL emitter (#386) — per-object backend SELECT generation.

Run from templates/forge-image/:  python -m pytest tests/test_sql_emitter.py -q
Self-contained: no DB, no network. Mirrors the bindings shapes in
backend-core/rust-api-v2/contracts/bindings.yaml.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from forge.emitters import sql  # noqa: E402
from forge.ir import Field, ObjectType  # noqa: E402


def _ot(name, *fields):
    return ObjectType(name=name, fields=tuple(Field(name=f, type="string") for f in fields))


def test_postgres_column_mapping_and_field_order():
    ot = _ot("KnowledgeSourceData", "source_id", "display_name", "provider_ref", "state")
    binding = {
        "relation": "factory.knowledge_source",
        "columns": {"source_id": "src_id", "display_name": "name",
                    "provider_ref": "provider", "state": "status"},
    }
    q = sql.EMITTERS["postgres"](ot, binding)
    # declared field order preserved; phys AS canonical; unmapped would be bare
    assert q == ("SELECT src_id AS source_id, name AS display_name, "
                 "provider AS provider_ref, status AS state FROM factory.knowledge_source")


def test_postgres_unmapped_field_defaults_to_same_name():
    ot = _ot("X", "a", "b")
    q = sql.EMITTERS["postgres"](ot, {"relation": "t", "columns": {"a": "col_a"}})
    assert q == "SELECT col_a AS a, b FROM t"


def test_arcadedb_defaults_to_field_names():
    ot = _ot("KnowledgeChunkData", "chunk_id", "excerpt", "source_id", "state")
    q = sql.EMITTERS["arcadedb"](ot, {"type": "Chunk"})
    assert q == "SELECT chunk_id, excerpt, source_id, state FROM Chunk"


def test_unknown_column_raises():
    ot = _ot("X", "a")
    with pytest.raises(ValueError, match="unknown field"):
        sql.EMITTERS["postgres"](ot, {"relation": "t", "columns": {"nope": "x"}})


def test_missing_relation_or_type_raises():
    ot = _ot("X", "a")
    with pytest.raises(ValueError, match="missing 'relation'"):
        sql.EMITTERS["postgres"](ot, {})
    with pytest.raises(ValueError, match="missing 'type'"):
        sql.EMITTERS["arcadedb"](ot, {})
