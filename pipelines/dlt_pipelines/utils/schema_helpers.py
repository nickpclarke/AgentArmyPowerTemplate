"""
Schema and pipeline utility helpers.

These thin wrappers centralise common patterns so every source in this package
applies metadata and incremental configuration consistently.

Usage
-----
    from dlt_pipelines.utils.schema_helpers import add_load_metadata, make_incremental_hint

    # Stamp a record with pipeline metadata before yielding:
    record = add_load_metadata({"country": "US", "value": 42})

    # Build an incremental cursor for a resource:
    incremental = make_incremental_hint("year")

    @dlt.resource(incremental=incremental)
    def my_resource(): ...
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import dlt

_PIPELINE_VERSION = "1.0.0"


def add_load_metadata(record: dict[str, Any]) -> dict[str, Any]:
    """Return ``record`` with two extra fields appended in-place.

    Added fields
    ------------
    ``_loaded_at``
        ISO-8601 UTC timestamp of when this record was produced by the pipeline.
    ``_pipeline_version``
        Semver string identifying the pipeline package version that produced
        this record.  Useful for debugging schema migrations across releases.

    Parameters
    ----------
    record:
        Any dict representing a data record.  Modified in-place *and* returned
        so the function can be used inline (``yield add_load_metadata(row)``).

    Returns
    -------
    dict
        The same dict object with the two metadata keys added.

    Examples
    --------
    >>> row = add_load_metadata({"id": 1, "name": "Alice"})
    >>> "_loaded_at" in row
    True
    >>> row["_pipeline_version"]
    '1.0.0'
    """
    record["_loaded_at"] = datetime.now(tz=timezone.utc).isoformat()
    record["_pipeline_version"] = _PIPELINE_VERSION
    return record


def make_incremental_hint(cursor_field: str) -> dlt.sources.incremental:  # type: ignore[type-arg]
    """Return a ``dlt.sources.incremental`` instance for the given cursor field.

    This is a thin factory that lets source authors declare incremental loading
    in one line without having to import ``dlt.sources`` directly everywhere.

    Parameters
    ----------
    cursor_field:
        Name of the field dlt should use to track the high-water mark across
        pipeline runs.  The field must exist in the records yielded by the
        resource.  dlt will persist the maximum value seen and filter out
        records with a lower or equal cursor value on subsequent runs.

    Returns
    -------
    dlt.sources.incremental
        A configured incremental object ready to be passed as the
        ``incremental`` parameter of a ``@dlt.resource`` decorator or used
        as a resource function argument annotated with
        ``dlt.sources.incremental[<type>]``.

    Examples
    --------
    Create a year-based incremental cursor::

        from dlt_pipelines.utils.schema_helpers import make_incremental_hint

        year_incremental = make_incremental_hint("year")

        @dlt.resource(name="my_table")
        def my_resource(updated=year_incremental):
            for row in fetch_data(since=updated.last_value):
                yield row
    """
    return dlt.sources.incremental(cursor_field)
