"""Tests for the forge Rust emitter (#305) — deterministic, byte-identical .g.rs.

Run from templates/forge-image/:  python -m pytest tests/test_rust_emitter.py -q
Self-contained: no HTTP server, no Docker. Mirrors the C# golden discipline.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
GOLDEN = HERE / "golden"
sys.path.insert(0, str(SCRIPTS))

from forge.emitters import rust  # noqa: E402
from forge.ir import Field, Model, ObjectType  # noqa: E402
from forge.parsers import yaml_parser  # noqa: E402


def _emit(model: Model, tmp_path) -> str:
    rust.emit(model, str(tmp_path))
    return (tmp_path / "data_platform_contracts.g.rs").read_text(encoding="utf-8")


def test_reference_model_byte_identical(tmp_path):
    """yaml_parser(reference.model.yaml) -> rust.emit must match the frozen golden,
    exercising relations (Vec / Option<Box>), Option<>, datetime/uuid -> String, snake_case."""
    src = (GOLDEN / "reference.model.yaml").read_bytes()
    model = yaml_parser.parse(src, source_uri="file:///work/reference.model.yaml")
    got = _emit(model, tmp_path)
    want = (GOLDEN / "reference.g.rs").read_text(encoding="utf-8")
    assert got == want, "rust emit drifted from tests/golden/reference.g.rs"


def test_state_machine_enum(tmp_path):
    """The state_property field is retyped to a `{Name}State` enum (kebab-case serde);
    a string[] field becomes Vec<String> with #[serde(default)]. Variants keep declared order."""
    model = Model(
        version="t.1",
        namespace="Test",
        object_types=[
            ObjectType(
                name="WorkPacketData",
                fields=(
                    Field(name="work_packet_id", type="string"),
                    Field(name="labels", type="string", is_list=True),
                    Field(name="state", type="string"),
                ),
                state_property="state",
                states=("todo", "in-progress", "awaiting-decision"),
            )
        ],
        source_uri="<inline>",
    )
    got = _emit(model, tmp_path)
    assert "pub struct WorkPacketData {" in got
    assert "pub work_packet_id: String," in got
    assert "#[serde(default)]\n    pub labels: Vec<String>," in got
    assert "pub state: WorkPacketDataState," in got
    assert '#[serde(rename_all = "kebab-case")]' in got
    assert "pub enum WorkPacketDataState {" in got
    # declared order preserved; kebab -> PascalCase
    assert got.index("Todo,") < got.index("InProgress,") < got.index("AwaitingDecision,")


def test_determinism(tmp_path):
    """Same model -> byte-identical output across runs (no timestamps / set ordering)."""
    src = (GOLDEN / "reference.model.yaml").read_bytes()
    model = yaml_parser.parse(src, source_uri="file:///work/reference.model.yaml")
    a = _emit(model, tmp_path / "a")
    b = _emit(model, tmp_path / "b")
    assert a == b
