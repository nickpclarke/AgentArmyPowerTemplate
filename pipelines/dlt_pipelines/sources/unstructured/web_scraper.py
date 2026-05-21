"""
Generic web page scraper source.

Fetches one or more URLs with ``requests`` and parses the HTML with
``BeautifulSoup``.  Optionally extracts all ``<a href>`` links found on each
page.  HTTP errors are logged and skipped so a bad URL never kills the whole
pipeline run.

Usage
-----
    from dlt_pipelines.sources.unstructured.web_scraper import web_scraper_source

    source = web_scraper_source(
        urls=["https://example.com", "https://httpbin.org/html"],
        extract_links=True,
    )
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Iterator
from urllib.parse import urljoin

import dlt
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT = 20
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def _extract_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    """Return a deduplicated list of absolute hrefs found in the page."""
    seen: set[str] = set()
    links: list[str] = []
    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:")):
            continue
        absolute = urljoin(base_url, href)
        if absolute not in seen:
            seen.add(absolute)
            links.append(absolute)
    return links


def _fetch_page(url: str, extract_links: bool) -> dict | None:
    """Fetch a single URL and return a parsed record dict, or None on failure."""
    try:
        response = requests.get(url, headers=_HEADERS, timeout=_REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.HTTPError as exc:
        logger.warning("HTTP error fetching %s: %s", url, exc)
        return None
    except requests.RequestException as exc:
        logger.warning("Request failed for %s: %s", url, exc)
        return None

    soup = BeautifulSoup(response.text, "lxml")

    # Title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # First H1
    h1_tag = soup.find("h1")
    h1 = h1_tag.get_text(strip=True) if h1_tag else ""

    # Body text — remove script and style nodes first
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text_content = soup.get_text(separator=" ", strip=True)
    word_count = len(text_content.split()) if text_content else 0

    links: list[str] = _extract_links(soup, url) if extract_links else []

    return {
        "url": url,
        "title": title,
        "h1": h1,
        "text_content": text_content,
        "word_count": word_count,
        "links": links,
        "scraped_at": datetime.now(tz=timezone.utc).isoformat(),
    }


@dlt.resource(
    name="web_pages",
    write_disposition="replace",
)
def web_pages(
    urls: list[str],
    extract_links: bool = False,
) -> Iterator[dict]:
    """Yield one record per successfully fetched URL.

    Parameters
    ----------
    urls:
        List of HTTP/HTTPS URLs to scrape.
    extract_links:
        When ``True``, each record includes a ``links`` field containing all
        absolute hrefs found on the page.  Defaults to ``False`` to keep rows
        compact for large crawls.

    Yields
    ------
    dict
        A record containing:
        ``url``             — the original request URL
        ``title``           — contents of the ``<title>`` tag
        ``h1``              — text of the first ``<h1>`` element
        ``text_content``    — visible body text with scripts/styles stripped
        ``word_count``      — approximate word count of ``text_content``
        ``links``           — list of absolute hrefs (empty list if not requested)
        ``scraped_at``      — ISO-8601 UTC timestamp of the fetch
    """
    for url in urls:
        logger.info("Scraping URL: %s (extract_links=%s)", url, extract_links)
        record = _fetch_page(url, extract_links=extract_links)
        if record is not None:
            yield record
        else:
            logger.warning("Skipping URL due to fetch error: %s", url)


@dlt.source(name="web_scraper")
def web_scraper_source(
    urls: list[str],
    extract_links: bool = False,
) -> dlt.sources.DltSource:
    """dlt source that scrapes a list of web pages.

    Returns a single resource: ``web_pages``.

    Parameters
    ----------
    urls:
        One or more HTTP/HTTPS URLs to fetch and parse.
    extract_links:
        Include all page links in the output records (default ``False``).
    """
    return web_pages(urls=urls, extract_links=extract_links)
