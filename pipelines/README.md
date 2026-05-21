# agentarmy-pipelines

A `dlt`-powered demo data pipeline toolkit for the AgentArmy repository.
Provides batteries-included pipeline scaffolding so AI data-engineer agents
can drop in new data sources with minimal boilerplate.

Pipelines write to **DuckDB** (local, zero-config) or **local Parquet files**
out of the box.  All sources are runnable immediately with no API keys
required (optional keys unlock higher rate limits for Census data).

---

## Installation

From the `pipelines/` directory:

```bash
pip install -e ".[dev]"
```

To include the optional `unstructured` extras (large PDF/DOCX parsing via
the `unstructured` library):

```bash
pip install -e ".[dev,unstructured]"
```

Python 3.11+ is required.

---

## Quick start

1. Copy `.env.example` to `.env` (no edits required to run the demos):

   ```bash
   cp .env.example .env
   ```

2. Run a demo pipeline from the `pipelines/` directory:

   ```bash
   # World Bank GDP + population data for G7 countries
   python scripts/run_world_bank.py

   # US Census county population for CA and NY
   python scripts/run_census.py

   # Scrape two public pages and load text into DuckDB
   python scripts/run_web_scraper.py
   # or pass custom URLs:
   python scripts/run_web_scraper.py https://example.com https://news.ycombinator.com
   ```

3. Query the results with DuckDB CLI or any SQL tool:

   ```bash
   duckdb data/demo.duckdb "SELECT * FROM wb_data.world_development_indicators LIMIT 10"
   ```

---

## Available sources

| Source module | dlt source function | Description |
|---|---|---|
| `sources/open_data/world_bank.py` | `world_bank_source()` | World Bank WDI indicator data via REST API |
| `sources/open_data/census_gov.py` | `census_gov_source()` | US Census ACS 5-year county population |
| `sources/open_data/github_trending.py` | `github_trending_source()` | GitHub Trending repos (daily/weekly/monthly) |
| `sources/unstructured/pdf_extractor.py` | `pdf_extractor_source()` | Page-level text extraction from local PDFs |
| `sources/unstructured/web_scraper.py` | `web_scraper_source()` | Fetch and parse arbitrary web pages |

---

## Destinations

Two destination helpers are provided in `dlt_pipelines/destinations.py`:

| Function | Destination | Output |
|---|---|---|
| `get_duckdb_pipeline(name, dataset, db_path)` | DuckDB | Tables in a local `.duckdb` file |
| `get_filesystem_pipeline(name, dataset, base_path)` | Filesystem | Parquet files under `base_path/<dataset>/<table>/` |

Both helpers accept `pipeline_name` and `dataset_name` as required arguments.
All other parameters have sensible defaults and can be overridden via the
environment variables documented below.

---

## Unstructured content processing

The `unstructured/` sub-package handles non-tabular content:

### PDF extraction

```python
from dlt_pipelines.destinations import get_duckdb_pipeline
from dlt_pipelines.sources.unstructured.pdf_extractor import pdf_extractor_source

pipeline = get_duckdb_pipeline("pdf_demo", "docs")
load_info = pipeline.run(pdf_extractor_source(file_path="path/to/report.pdf"))
print(load_info)
```

Each page becomes one row with `file_name`, `page_number`, `text`,
`char_count`, `word_count`, and `extracted_at` fields.

### Web page scraping

```python
from dlt_pipelines.destinations import get_duckdb_pipeline
from dlt_pipelines.sources.unstructured.web_scraper import web_scraper_source

pipeline = get_duckdb_pipeline("web_demo", "scraped_data")
load_info = pipeline.run(
    web_scraper_source(
        urls=["https://example.com"],
        extract_links=True,
    )
)
print(load_info)
```

Each URL becomes one row with `url`, `title`, `h1`, `text_content`,
`word_count`, `links`, and `scraped_at` fields.

For heavier document processing (DOCX, PPTX, email, etc.) install the
`unstructured` extra (`pip install -e ".[unstructured]"`) and integrate
the `unstructured` library directly in a custom source.

---

## How to add a new source (for agents)

Adding a new data source takes three steps:

### Step 1 — Create the source module

Add a new file under `dlt_pipelines/sources/open_data/` (for APIs/scrapers)
or `dlt_pipelines/sources/unstructured/` (for file-based sources).

Minimal template:

```python
# dlt_pipelines/sources/open_data/my_source.py
from __future__ import annotations
from typing import Iterator
import dlt
import requests

@dlt.resource(name="my_table", write_disposition="merge", primary_key=["id"])
def my_resource(param: str = "default") -> Iterator[dict]:
    """Yield records from my data source."""
    response = requests.get(f"https://api.example.com/data?q={param}", timeout=30)
    response.raise_for_status()
    for item in response.json():
        yield {"id": item["id"], "value": item["value"]}

@dlt.source(name="my_source")
def my_source(param: str = "default") -> dlt.sources.DltSource:
    return my_resource(param=param)
```

### Step 2 — Add a run script

Create `scripts/run_my_source.py` following the pattern in the existing
scripts.  Import `get_duckdb_pipeline` and your new source function, then
call `pipeline.run(source)`.

### Step 3 — Update the sources table in this README

Add a row to the "Available sources" table above so other agents know the
source exists.

That is all.  dlt handles schema inference, state tracking, and incremental
loading automatically.

---

## Utility helpers

`dlt_pipelines/utils/schema_helpers.py` exposes two helpers:

```python
from dlt_pipelines.utils.schema_helpers import add_load_metadata, make_incremental_hint

# Stamp any record dict with _loaded_at and _pipeline_version fields:
record = add_load_metadata({"country": "US", "gdp": 21_000_000_000_000})

# Create a dlt incremental cursor for a resource:
year_cursor = make_incremental_hint("year")
```

---

## Environment variables

Copy `.env.example` to `.env` and customise as needed.

| Variable | Required | Description |
|---|---|---|
| `DESTINATION__DUCKDB__CREDENTIALS` | No | Path to the DuckDB file (default: `data/demo.duckdb`) |
| `DESTINATION__FILESYSTEM__BUCKET_URL` | No | Base directory for Parquet output (default: `data/`) |
| `CENSUS_API_KEY` | No | Census Bureau API key — anonymous access works but is rate-limited |
| `RUNTIME__DLTHUB_TELEMETRY` | No | Set to `false` to disable dlt anonymous telemetry (default: `false`) |
| `RUNTIME__LOG_LEVEL` | No | dlt log verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: `INFO`) |

Register for a free Census API key at https://api.census.gov/data/key_signup.html.

---

## Project layout

```
pipelines/
├── README.md                          # this file
├── pyproject.toml                     # PEP 621 package definition
├── .env.example                       # environment variable reference
├── dlt_pipelines/
│   ├── __init__.py
│   ├── destinations.py                # get_duckdb_pipeline / get_filesystem_pipeline
│   ├── sources/
│   │   ├── open_data/
│   │   │   ├── world_bank.py          # World Bank WDI REST API
│   │   │   ├── census_gov.py          # US Census ACS 5-year API
│   │   │   └── github_trending.py     # GitHub Trending scraper
│   │   └── unstructured/
│   │       ├── pdf_extractor.py       # PDF page text via pdfplumber
│   │       └── web_scraper.py         # Web page text via requests + BS4
│   └── utils/
│       └── schema_helpers.py          # load metadata + incremental helpers
└── scripts/
    ├── run_world_bank.py
    ├── run_census.py
    └── run_web_scraper.py
```
