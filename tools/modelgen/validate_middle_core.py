from __future__ import annotations

import argparse
from pathlib import Path

from middle_core_model import load_model, validate_model


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the middle-core model.")
    parser.add_argument("--model", required=True, type=Path)
    args = parser.parse_args()

    model = load_model(args.model)
    errors = validate_model(model, args.model)
    if errors:
        print("middle-core model FAIL")
        for error in errors:
            print(f"ERROR {error}")
        return 1

    print(f"middle-core model PASS ({model.get('model_id')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
