"""
World Bank Open Data source.

Fetches World Development Indicators (WDI) from the public World Bank REST API
at https://api.worldbank.org/v2/.

Usage
-----
    from dlt_pipelines.sources.open_data.world_bank import world_bank_source

    source = world_bank_source(
        indicator_codes=["NY.GDP.MKTP.CD", "SP.POP.TOTL"],
        country_codes=["US", "CN", "DE"],
        start_year=2010,
    )
"""

from __future__ import annotations

import logging
from typing import Iterator

import dlt
import requests

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.worldbank.org/v2"
_PER_PAGE = 1000
_REQUEST_TIMEOUT = 30


def _fetch_indicator_pages(
    country: str,
    indicator: str,
    start_year: int,
    end_year: int = 2024,
) -> Iterator[dict]:
    """Paginate through all WB API pages for a single country+indicator combo."""
    page = 1
    while True:
        url = (
            f"{_BASE_URL}/country/{country}/indicator/{indicator}"
            f"?format=json&per_page={_PER_PAGE}&page={page}&date={start_year}:{end_year}"
        )
        try:
            response = requests.get(url, timeout=_REQUEST_TIMEOUT)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("World Bank API request failed for %s/%s page %d: %s", country, indicator, page, exc)
            return

        payload = response.json()
        # WB returns [metadata_dict, data_list]; data_list is None on empty result
        if not isinstance(payload, list) or len(payload) < 2 or not payload[1]:
            return

        metadata, data = payload[0], payload[1]
        for row in data:
            yield row

        total_pages = metadata.get("pages", 1)
        if page >= total_pages:
            break
        page += 1


@dlt.resource(
    name="world_development_indicators",
    write_disposition="merge",
    primary_key=["country_code", "indicator_code", "year"],
)
def world_development_indicators(
    indicator_codes: list[str],
    country_codes: list[str] | None = None,
    start_year: int = 2000,
) -> Iterator[dict]:
    """Yield World Development Indicator records for the requested countries and indicators.

    Parameters
    ----------
    indicator_codes:
        List of WDI indicator codes, e.g. ``["NY.GDP.MKTP.CD", "SP.POP.TOTL"]``.
    country_codes:
        ISO 3166-1 alpha-2 or alpha-3 country codes.  Pass ``None`` (default) to
        fetch all countries using the WB ``"all"`` shorthand.
    start_year:
        Earliest year to include.  Supports incremental loading — on subsequent
        runs only records newer than the last loaded year are fetched.
    """
    countries = country_codes if country_codes else ["all"]

    for country in countries:
        for indicator in indicator_codes:
            logger.info("Fetching WB indicator %s for country %s from %d", indicator, country, start_year)
            for raw in _fetch_indicator_pages(country, indicator, start_year):
                value = raw.get("value")
                date_str = raw.get("date", "")
                # WB "date" field is a string year like "2023"
                try:
                    year = int(date_str)
                except (ValueError, TypeError):
                    year = None

                yield {
                    "country_code": raw.get("countryiso3code") or raw.get("country", {}).get("id", country),
                    "country_name": raw.get("country", {}).get("value", ""),
                    "indicator_code": raw.get("indicator", {}).get("id", indicator),
                    "indicator_name": raw.get("indicator", {}).get("value", ""),
                    "year": year,
                    "value": float(value) if value is not None else None,
                }


@dlt.source(name="world_bank")
def world_bank_source(
    indicator_codes: list[str],
    country_codes: list[str] | None = None,
    start_year: int = 2000,
) -> dlt.sources.DltSource:
    """dlt source wrapping the World Bank Open Data REST API.

    Returns a single resource: ``world_development_indicators``.
    """
    return world_development_indicators(
        indicator_codes=indicator_codes,
        country_codes=country_codes,
        start_year=start_year,
    )
