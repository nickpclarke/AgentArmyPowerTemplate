"""
Destination factory helpers.

Usage
-----
    from dlt_pipelines.destinations import get_duckdb_pipeline, get_filesystem_pipeline

    pipeline = get_duckdb_pipeline("world_bank", "wb_data")
    load_info = pipeline.run(some_source)
"""

from __future__ import annotations

import dlt


def get_duckdb_pipeline(
    pipeline_name: str,
    dataset_name: str,
    db_path: str = "data/demo.duckdb",
) -> dlt.Pipeline:
    """Return a dlt Pipeline configured to write to a local DuckDB file.

    Parameters
    ----------
    pipeline_name:
        Unique name for this pipeline. dlt uses it to store pipeline state
        (schema, load ids, etc.) under ``~/.dlt/pipelines/<pipeline_name>``.
    dataset_name:
        The DuckDB schema (namespace) that tables will be created inside.
    db_path:
        Path to the DuckDB file, relative to the current working directory
        or absolute.  Defaults to ``data/demo.duckdb`` so that all demo runs
        share one file.  Override via the ``DESTINATION__DUCKDB__CREDENTIALS``
        env var if preferred.
    """
    return dlt.pipeline(
        pipeline_name=pipeline_name,
        destination=dlt.destinations.duckdb(credentials=db_path),
        dataset_name=dataset_name,
    )


def get_filesystem_pipeline(
    pipeline_name: str,
    dataset_name: str,
    base_path: str = "data/",
) -> dlt.Pipeline:
    """Return a dlt Pipeline configured to write Parquet files to the local filesystem.

    Files land at ``<base_path>/<dataset_name>/<table_name>/*.parquet``.

    Parameters
    ----------
    pipeline_name:
        Unique name for this pipeline.
    dataset_name:
        Sub-directory under ``base_path`` that groups related tables.
    base_path:
        Root output directory.  Defaults to ``data/``.  Override via the
        ``DESTINATION__FILESYSTEM__BUCKET_URL`` env var if preferred.
    """
    return dlt.pipeline(
        pipeline_name=pipeline_name,
        destination=dlt.destinations.filesystem(bucket_url=base_path),
        dataset_name=dataset_name,
    )
