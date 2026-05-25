"""
Drift gate tests: verify the drift checker catches model edits and hand-edits.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "model" / "middle-core" / "model.yaml"
GENERATED = ROOT / "templates" / "middle-core" / "generated"
DRIFT_GATE = ROOT / "tools" / "modelgen" / "check_drift.py"


class MiddleCoreDriftTests(unittest.TestCase):
    def test_clean_tree_passes(self) -> None:
        """Clean committed tree should pass the drift gate."""
        result = subprocess.run(
            [sys.executable, str(DRIFT_GATE), "--model", str(MODEL), "--generated", str(GENERATED)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("no drift detected", result.stdout)

    def test_model_edit_without_regen_is_caught(self) -> None:
        """Editing the model without regenerating should fail the gate."""
        with tempfile.TemporaryDirectory() as temp:
            # Copy model and generated dirs to temp.
            temp_model_dir = Path(temp) / "middle-core"
            shutil.copytree(MODEL.parent, temp_model_dir)
            temp_model = temp_model_dir / "model.yaml"

            temp_generated = Path(temp) / "generated"
            shutil.copytree(GENERATED, temp_generated)

            # Mutate the model: add a new use_case (doesn't invalidate; changes generated output).
            payload = yaml.safe_load(temp_model.read_text(encoding="utf-8"))
            # Add a new use case to the root use_cases list.
            payload["use_cases"].append({"id": "UC-99", "title": "New use case for testing"})
            # Add it to an object_type so it shows in generated code.
            payload["object_types"][0]["use_cases"].append("UC-99")
            temp_model.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

            # Run the gate: should fail because temp_generated is now stale.
            result = subprocess.run(
                [
                    sys.executable,
                    str(DRIFT_GATE),
                    "--model",
                    str(temp_model),
                    "--generated",
                    str(temp_generated),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("DRIFT DETECTED", result.stderr)

    def test_hand_edit_of_generated_file_is_caught(self) -> None:
        """Hand-editing a .g.cs file should fail the gate."""
        with tempfile.TemporaryDirectory() as temp:
            # Copy generated dir to temp and mutate one file.
            temp_generated = Path(temp) / "generated"
            shutil.copytree(GENERATED, temp_generated)

            # Append a line to one of the generated files.
            biz_obj_file = temp_generated / "BusinessObjectTypes.g.cs"
            original = biz_obj_file.read_text(encoding="utf-8")
            biz_obj_file.write_text(original + "\n// hand-added comment\n", encoding="utf-8")

            # Run the gate: should fail because temp_generated differs from fresh regen.
            result = subprocess.run(
                [
                    sys.executable,
                    str(DRIFT_GATE),
                    "--model",
                    str(MODEL),
                    "--generated",
                    str(temp_generated),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("DRIFT DETECTED", result.stderr)
        self.assertIn("BusinessObjectTypes.g.cs", result.stderr)


if __name__ == "__main__":
    unittest.main()
