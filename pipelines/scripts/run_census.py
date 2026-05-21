"""
Run the US Census Bureau ACS 5-year pipeline.

Fetches county-level population estimates for California and New York from the
Census Bureau's public API and loads them into a local DuckDB file.

Run from the ``pipelines/`` directory:

    python scripts/run_census.py

The DuckDB file will be created at ``data/demo.duckdb`` (relative to the
``pipelines/`` directory).  You can override the path via the
``DESTINATION__DUCKDB__CREDENTIALS`` environment variable.

Optional: set ``CENSUS_API_KEY`` in your ``.env`` to avoid anonymous rate limits.

Tables created
--------------
``census_data.acs5_population``
"""

from __future__ import annotations

import sys
from pathlib import Path

_PIPELINES_ROOT = Path(__file__).resolve().parent.parent
if str(_PIPELINES_ROOT) not in sys.path:
    sys.path.insert(0, str(_PIPELINES_ROOT))

from dlt_pipelines.destinations import get_duckdb_pipeline
from dlt_pipelines.sources.open_data.census_gov import census_gov_source

# ── Configuration ────────────────────────────────────────────────────────────

# FIPS codes: 06 = California, 36 = New York
# Add more codes from https://www.census.gov/library/reference/code-lists/ansi/ansi-codes-for-states.html
# or pass None to fetch all 50 states (takes ~1–2 minutes due to 51 API calls).
STATE_FIPS = ["06", "36"]

# Most recent completed ACS 5-year survey year (2 years behind today is typical)
SURVEY_YEAR = 2022

# ── Pipeline ──────────────────────────────────────────────────────────────────


def main() -> None:
    pipeline = get_duckdb_pipeline(
        pipeline_name="census_demo",
        dataset_name="census_data",
    )

    source = census_gov_source(
        state_fips=STATE_FIPS,
        year=SURVEY_YEAR,
    )

    print(
        f"Running Census pipeline — "
        f"states: {STATE_FIPS}, ACS survey year: {SURVEY_YEAR}"
    )

    load_info = pipeline.run(source)

    print("\nLoad info:")
    print(load_info)
    print(f"\nData written to: {pipeline.dataset_name!r} dataset")


if __name__ == "__main__":
    main()
