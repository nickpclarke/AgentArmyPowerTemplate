from __future__ import annotations

import hashlib
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "model" / "middle-core" / "model.yaml"
GENERATOR = ROOT / "tools" / "modelgen" / "generate_middle_core.py"
VALIDATOR = ROOT / "tools" / "modelgen" / "validate_middle_core.py"
HAS_PYSHACL = importlib.util.find_spec("pyshacl") is not None


class MiddleCoreModelgenTests(unittest.TestCase):
    def test_model_validates(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), "--model", str(MODEL)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("middle-core model PASS", result.stdout)

    def test_missing_workflow_step_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_model_dir = Path(temp) / "middle-core"
            shutil.copytree(MODEL.parent, temp_model_dir)
            temp_model = temp_model_dir / "model.yaml"
            payload = yaml.safe_load(temp_model.read_text(encoding="utf-8"))
            payload["scenarios"][0]["workflow_steps"].append("not-a-real-step")
            temp_model.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--model", str(temp_model)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown workflow step not-a-real-step", result.stdout)

    def test_invalid_state_transition_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_model_dir = Path(temp) / "middle-core"
            shutil.copytree(MODEL.parent, temp_model_dir)
            temp_model = temp_model_dir / "model.yaml"
            payload = yaml.safe_load(temp_model.read_text(encoding="utf-8"))
            payload["state_machines"][0]["transitions"].append(
                {"from": "not-a-real-state", "to": "searchable", "trigger": "bad-transition"}
            )
            temp_model.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--model", str(temp_model)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("transition from unknown state not-a-real-state", result.stdout)

    def test_generation_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            out_dir = Path(temp) / "generated"
            self.run_generator(out_dir)
            first = self.hash_generated_tree(out_dir)
            self.run_generator(out_dir)
            second = self.hash_generated_tree(out_dir)

        self.assertEqual(first, second)

    def test_generator_emits_shacl_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            out_dir = Path(temp) / "generated"
            self.run_generator(out_dir)

            self.assertTrue((out_dir / "model-runtime.shacl.ttl").exists())
            self.assertTrue((out_dir / "model-runtime.fixture.ttl").exists())

    def test_generator_refuses_hand_authored_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            out_dir = Path(temp) / "generated"
            out_dir.mkdir()
            (out_dir / "BusinessObjectTypes.g.cs").write_text("// hand-authored\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(GENERATOR), "--model", str(MODEL), "--out", str(out_dir)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Refusing to overwrite", result.stderr + result.stdout)

    @unittest.skipUnless(HAS_PYSHACL, "pyshacl is not installed")
    def test_generated_shacl_fixture_validates(self) -> None:
        from pyshacl import validate

        with tempfile.TemporaryDirectory() as temp:
            out_dir = Path(temp) / "generated"
            self.run_generator(out_dir)

            conforms, _, report = validate(
                data_graph=str(out_dir / "model-runtime.fixture.ttl"),
                shacl_graph=str(out_dir / "model-runtime.shacl.ttl"),
            )

        self.assertTrue(conforms, str(report))

    def run_generator(self, out_dir: Path) -> None:
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--model", str(MODEL), "--out", str(out_dir)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @staticmethod
    def hash_generated_tree(out_dir: Path) -> str:
        digest = hashlib.sha256()
        for path in sorted(out_dir.rglob("*")):
            if path.is_file():
                digest.update(path.relative_to(out_dir).as_posix().encode("utf-8"))
                digest.update(path.read_bytes())
        return digest.hexdigest()


if __name__ == "__main__":
    unittest.main()
