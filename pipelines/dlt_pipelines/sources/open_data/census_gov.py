"""
US Census Bureau — American Community Survey (ACS) 5-year estimates source.

Fetches county-level population data from the Census Bureau's public API at
https://api.census.gov/data/.

An API key is optional but recommended for production use.  Register free at:
https://api.census.gov/data/key_signup.html

Set the ``CENSUS_API_KEY`` environment variable (or dlt secret) to enable it.

Usage
-----
    from dlt_pipelines.sources.open_data.census_gov import census_gov_source

    source = census_gov_source(state_fips=["06", "36"], year=2022)
"""

from __future__ import annotations

import logging
import os
from typing import Iterator

import dlt
import requests

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.census.gov/data"
_REQUEST_TIMEOUT = 30


def _get_api_key() -> str:
    """Return the Census API key from dlt secrets or environment, empty string if absent."""
    try:
        key = dlt.secrets.get("census_api_key") or ""
    except Exception:
        key = ""
    if not key:
        key = os.environ.get("CENSUS_API_KEY", "")
    return key


def _fetch_acs5_county(state_fips: str, year: int, api_key: str) -> list[list[str]]:
    """Fetch raw ACS 5-year county population rows for one state."""
    url = f"{_BASE_URL}/{year}/acs/acs5"
    params: dict[str, str] = {
        "get": "NAME,B01001_001E",
        "for": "county:*",
        "in": f"state:{state_fips}",
    }
    if api_key:
        params["key"] = api_key

    try:
        response = requests.get(url, params=params, timeout=_REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Census API request failed for state %s year %d: %s", state_fips, year, exc)
        return []

    data: list[list[str]] = response.json()
    return data


@dlt.resource(
    name="acs5_population",
    write_disposition="merge",
    primary_key=["state_fips", "county_fips", "year"],
)
def acs5_population(
    state_fips: list[str] | None = None,
    year: int = 2022,
) -> Iterator[dict]:
    """Yield county-level population estimates from the ACS 5-year survey.

    Parameters
    ----------
    state_fips:
        List of two-digit state FIPS codes, e.g. ``["06", "36"]`` for CA and NY.
        Pass ``None`` to fetch all 50 states + DC (51 API calls).
    year:
        ACS 5-year survey year to query.  The Census API holds data from 2009
        through the most recently completed survey (typically 2 years behind today).
    """
    api_key = _get_api_key()

    if state_fips is None:
        # All US states + DC (FIPS 01–56, skipping unassigned codes)
        all_fips = [
            "01","02","04","05","06","08","09","10","11","12","13","15","16","17","18",
            "19","20","21","22","23","24","25","26","27","28","29","30","31","32","33",
            "34","35","36","37","38","39","40","41","42","44","45","46","47","48","49",
            "50","51","53","54","55","56",
        ]
        states_to_fetch = all_fips
    else:
        states_to_fetch = list(state_fips)

    for state in states_to_fetch:
        logger.info("Fetching ACS5 population for state FIPS %s, year %d", state, year)
        rows = _fetch_acs5_county(state, year, api_key)
        if not rows:
            continue

        # First row is the header: ["NAME", "B01001_001E", "state", "county"]
        header, *data_rows = rows
        name_idx = header.index("NAME")
        pop_idx = header.index("B01001_001E")
        state_idx = header.index("state")
        county_idx = header.index("county")

        for row in data_rows:
            try:
                population = int(row[pop_idx]) if row[pop_idx] else None
            except ValueError:
                population = None

            yield {
                "name": row[name_idx],
                "state_fips": row[state_idx],
                "county_fips": row[county_idx],
                "population": population,
                "year": year,
            }


@dlt.source(name="census_gov")
def census_gov_source(
    state_fips: list[str] | None = None,
    year: int = 2022,
) -> dlt.sources.DltSource:
    """dlt source wrapping the US Census Bureau ACS 5-year API.

    Returns a single resource: ``acs5_population``.
    """
    return acs5_population(state_fips=state_fips, year=year)
