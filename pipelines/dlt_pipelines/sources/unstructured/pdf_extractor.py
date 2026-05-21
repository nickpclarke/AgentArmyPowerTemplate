"""
PDF text and metadata extraction source.

Extracts every page of a local PDF file as a separate row, including the
raw text content and basic character/word counts.  Uses ``pdfplumber`` for
accurate text extraction with layout awareness.

Usage
-----
    from dlt_pipelines.sources.unstructured.pdf_extractor import pdf_extractor_source

    source = pdf_extractor_source(file_path="docs/report.pdf")
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Iterator

import dlt
import pdfplumber

logger = logging.getLogger(__name__)


@dlt.resource(
    name="pdf_pages",
    write_disposition="replace",
)
def pdf_pages(file_path: str) -> Iterator[dict]:
    """Yield one record per page extracted from a PDF file.

    Parameters
    ----------
    file_path:
        Absolute or relative path to the PDF file to process.

    Yields
    ------
    dict
        A record containing:
        ``file_name``       — basename of the source file
        ``page_number``     — 1-based page index
        ``text``            — raw extracted text (empty string if none)
        ``char_count``      — number of characters in the extracted text
        ``word_count``      — approximate word count (whitespace-split tokens)
        ``extracted_at``    — ISO-8601 UTC timestamp of extraction
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"PDF not found: {file_path!r}")

    file_name = os.path.basename(file_path)
    extracted_at = datetime.now(tz=timezone.utc).isoformat()

    logger.info("Opening PDF: %s", file_path)

    with pdfplumber.open(file_path) as pdf:
        total_pages = len(pdf.pages)
        logger.info("PDF has %d page(s): %s", total_pages, file_name)

        for page in pdf.pages:
            page_number = page.page_number  # pdfplumber uses 1-based numbering
            try:
                text = page.extract_text() or ""
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to extract text from page %d of %s: %s",
                    page_number,
                    file_name,
                    exc,
                )
                text = ""

            words = text.split() if text else []

            yield {
                "file_name": file_name,
                "page_number": page_number,
                "text": text,
                "char_count": len(text),
                "word_count": len(words),
                "extracted_at": extracted_at,
            }


@dlt.source(name="pdf_extractor")
def pdf_extractor_source(file_path: str) -> dlt.sources.DltSource:
    """dlt source that extracts page-level text from a local PDF.

    Returns a single resource: ``pdf_pages``.

    Parameters
    ----------
    file_path:
        Path to the PDF file.  Relative paths are resolved against the current
        working directory at pipeline run time.
    """
    return pdf_pages(file_path=file_path)
