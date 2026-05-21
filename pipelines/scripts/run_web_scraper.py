"""
Run the generic web scraper pipeline.

Fetches a list of URLs, parses the visible text content and (optionally) all
outbound links, then loads the results into a local DuckDB file.

Run from the ``pipelines/`` directory:

    python scripts/run_web_scraper.py

You can customise the target URLs and the ``extract_links`` flag directly in
the ``URLS`` / ``EXTRACT_LINKS`` constants below, or pass them as positional
CLI arguments:

    python scripts/run_web_scraper.py https://example.com https://httpbin.org/html

The DuckDB file will be created at ``data/demo.duckdb`` (relative to the
``pipelines/`` directory).  You can override the path via the
``DESTINATION__DUCKDB__CREDENTIALS`` environment variable.

Tables created
--------------
``scraped_data.web_pages``
"""

from __future__ import annotations

import sys
from pathlib import Path

_PIPELINES_ROOT = Path(__file__).resolve().parent.parent
if str(_PIPELINES_ROOT) not in sys.path:
    sys.path.insert(0, str(_PIPELINES_ROOT))

from dlt_pipelines.destinations import get_duckdb_pipeline
from dlt_pipelines.sources.unstructured.web_scraper import web_scraper_source

# ── Default configuration ────────────────────────────────────────────────────

# Override at the command line: python scripts/run_web_scraper.py <url1> <url2> ...
DEFAULT_URLS = [
    "https://example.com",
    "https://httpbin.org/html",
]

# Set to True to include all outbound href links in each record.
EXTRACT_LINKS = False

# ── Pipeline ──────────────────────────────────────────────────────────────────


def main() -> None:
    # Accept optional URL arguments from the command line
    urls: list[str] = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_URLS

    pipeline = get_duckdb_pipeline(
        pipeline_name="web_scraper_demo",
        dataset_name="scraped_data",
    )

    source = web_scraper_source(
        urls=urls,
        extract_links=EXTRACT_LINKS,
    )

    print(
        f"Running web scraper pipeline — "
        f"{len(urls)} URL(s), extract_links={EXTRACT_LINKS}"
    )
    for url in urls:
        print(f"  {url}")

    load_info = pipeline.run(source)

    print("\nLoad info:")
    print(load_info)
    print(f"\nData written to: {pipeline.dataset_name!r} dataset")


if __name__ == "__main__":
    main()
