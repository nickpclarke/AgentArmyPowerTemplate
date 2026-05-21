"""
Run the World Bank Open Data pipeline.

Fetches GDP (current USD) and total population for the G7 countries from the
World Bank API and loads them into a local DuckDB file.

Run from the ``pipelines/`` directory:

    python scripts/run_world_bank.py

The DuckDB file will be created at ``data/demo.duckdb`` (relative to the
``pipelines/`` directory).  You can override the path via the
``DESTINATION__DUCKDB__CREDENTIALS`` environment variable.

Tables created
--------------
``wb_data.world_development_indicators``
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running from any working directory as long as the pipelines/ root is on the path.
_PIPELINES_ROOT = Path(__file__).resolve().parent.parent
if str(_PIPELINES_ROOT) not in sys.path:
    sys.path.insert(0, str(_PIPELINES_ROOT))

from dlt_pipelines.destinations import get_duckdb_pipeline
from dlt_pipelines.sources.open_data.world_bank import world_bank_source

# ── Configuration ────────────────────────────────────────────────────────────

# World Bank indicator codes:
#   NY.GDP.MKTP.CD  — GDP (current US$)
#   SP.POP.TOTL     — Population, total
INDICATOR_CODES = ["NY.GDP.MKTP.CD", "SP.POP.TOTL"]

# ISO 3166-1 alpha-2 codes for G7 nations
COUNTRY_CODES = ["US", "GB", "DE", "FR", "IT", "CA", "JP"]

# Fetch data from 2010 onwards
START_YEAR = 2010

# ── Pipeline ──────────────────────────────────────────────────────────────────


def main() -> None:
    pipeline = get_duckdb_pipeline(
        pipeline_name="world_bank_demo",
        dataset_name="wb_data",
    )

    source = world_bank_source(
        indicator_codes=INDICATOR_CODES,
        country_codes=COUNTRY_CODES,
        start_year=START_YEAR,
    )

    print(
        f"Running World Bank pipeline — "
        f"{len(INDICATOR_CODES)} indicator(s), {len(COUNTRY_CODES)} country/ies, "
        f"from {START_YEAR} to 2024"
    )

    load_info = pipeline.run(source)

    print("\nLoad info:")
    print(load_info)
    print(f"\nData written to: {pipeline.dataset_name!r} dataset")


if __name__ == "__main__":
    main()
