#!/usr/bin/env python3
"""L1 (syntactic) validation of the self-model IR against the canonical schema."""
import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
schema = json.loads((ROOT / "templates" / "ontology-project" / "ontology.ir.schema.json").read_text(encoding="utf-8"))
model = yaml.safe_load((ROOT / "ontology" / "platform-self-model" / "model" / "model.yaml").read_text(encoding="utf-8"))

errs = sorted(Draft202012Validator(schema).iter_errors(model), key=lambda e: list(e.path))
if not errs:
    n_types = len(model.get("types", []))
    n_rel = len(model.get("relators", []))
    print(f"L1 OK - well-formed IR ({n_types} types, {n_rel} relators, unique ids, valid stereotypes)")
    sys.exit(0)
for e in errs:
    print(f"  L1 FAIL {list(e.path)}: {e.message}")
sys.exit(1)
