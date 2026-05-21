"""
GitHub Trending repositories scraper source.

Scrapes https://github.com/trending to produce a daily/weekly/monthly snapshot
of trending repositories.  No API key required.

Usage
-----
    from dlt_pipelines.sources.open_data.github_trending import github_trending_source

    source = github_trending_source(language="python", since="daily")
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Iterator

import dlt
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_BASE_URL = "https://github.com/trending"
_REQUEST_TIMEOUT = 20
_HEADERS = {
    # A realistic User-Agent helps avoid GitHub's bot-detection returning 429s.
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def _parse_int(text: str | None) -> int | None:
    """Strip commas/whitespace and parse an integer; return None on failure."""
    if text is None:
        return None
    clean = text.strip().replace(",", "").replace(" ", "")
    try:
        return int(clean)
    except ValueError:
        return None


def _scrape_trending(language: str, since: str) -> list[dict]:
    """Fetch and parse the GitHub Trending page; return a list of repo dicts."""
    lang_segment = language.strip().lower().replace(" ", "-") if language else ""
    url = f"{_BASE_URL}/{lang_segment}?since={since}" if lang_segment else f"{_BASE_URL}?since={since}"

    try:
        response = requests.get(url, headers=_HEADERS, timeout=_REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("GitHub Trending request failed (url=%s): %s", url, exc)
        return []

    soup = BeautifulSoup(response.text, "lxml")
    repo_items = soup.select("article.Box-row")

    results: list[dict] = []
    for rank, item in enumerate(repo_items, start=1):
        # Repo full name e.g. "owner/repo"
        h2 = item.select_one("h2.h3 a")
        if not h2:
            continue
        full_name_raw = h2.get_text(separator="/", strip=True)
        # GitHub renders it as "owner / repo" with surrounding whitespace
        parts = [p.strip() for p in full_name_raw.split("/") if p.strip()]
        if len(parts) < 2:
            continue
        owner, repo = parts[0], parts[1]

        # Description
        desc_el = item.select_one("p.col-9")
        description = desc_el.get_text(strip=True) if desc_el else ""

        # Language (may be absent for repos without a dominant language)
        lang_el = item.select_one("[itemprop='programmingLanguage']")
        detected_language = lang_el.get_text(strip=True) if lang_el else ""

        # Stars and forks — both are <a> links with svg icons inside
        star_fork_links = item.select("div.f6.color-fg-muted a")
        total_stars: int | None = None
        total_forks: int | None = None
        for link in star_fork_links:
            href = link.get("href", "")
            if "/stargazers" in href:
                total_stars = _parse_int(link.get_text(strip=True))
            elif "/forks" in href:
                total_forks = _parse_int(link.get_text(strip=True))

        # Stars today / this week / this month — the last span in the meta row
        stars_today_el = item.select_one("span.d-inline-block.float-sm-right")
        stars_today_text = stars_today_el.get_text(strip=True) if stars_today_el else ""
        # Text looks like "123 stars today" or "1,234 stars this week"
        stars_today = _parse_int(stars_today_text.split()[0]) if stars_today_text else None

        results.append({
            "rank": rank,
            "owner": owner,
            "repo": repo,
            "full_name": f"{owner}/{repo}",
            "description": description,
            "language": detected_language,
            "stars": total_stars,
            "forks": total_forks,
            "stars_today": stars_today,
            "scraped_at": datetime.now(tz=timezone.utc).isoformat(),
        })

    return results


@dlt.resource(
    name="trending_repositories",
    write_disposition="replace",
)
def trending_repositories(
    language: str = "",
    since: str = "daily",
) -> Iterator[dict]:
    """Yield trending GitHub repository records.

    Parameters
    ----------
    language:
        Filter by programming language slug (e.g. ``"python"``, ``"typescript"``).
        Pass an empty string (default) to get all languages.
    since:
        Time window for trending calculation.  One of ``"daily"``, ``"weekly"``,
        or ``"monthly"``.
    """
    repos = _scrape_trending(language=language, since=since)
    logger.info("Scraped %d trending repositories (language=%r, since=%r)", len(repos), language, since)
    yield from repos


@dlt.source(name="github_trending")
def github_trending_source(
    language: str = "",
    since: str = "daily",
) -> dlt.sources.DltSource:
    """dlt source that scrapes GitHub Trending repositories.

    Returns a single resource: ``trending_repositories``.
    """
    return trending_repositories(language=language, since=since)
