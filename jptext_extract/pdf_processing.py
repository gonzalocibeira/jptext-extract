"""Utilities for extracting Japanese text from PDF documents."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Callable, List, Optional
import unicodedata

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
from pdfminer.pdfpage import PDFPage

try:
    from pdf2image import convert_from_path
except ImportError:  # pragma: no cover - optional dependency at runtime
    convert_from_path = None  # type: ignore

try:
    import pytesseract
except ImportError:  # pragma: no cover - optional dependency at runtime
    pytesseract = None  # type: ignore


LOGGER = logging.getLogger(__name__)


_JAPANESE_RANGES = [
    ("\u3000", "\u303F"),  # punctuation
    ("\u3040", "\u309F"),  # hiragana
    ("\u30A0", "\u30FF"),  # katakana
    ("\u31F0", "\u31FF"),  # small katakana extensions
    ("\u3400", "\u4DBF"),  # CJK extension A
    ("\u4E00", "\u9FFF"),  # CJK unified
    ("\uFF01", "\uFF5E"),  # full-width punctuation/ASCII
    ("\uFF66", "\uFF9F"),  # half-width katakana
]


def filter_non_japanese(text: str) -> str:
    """Normalize text to NFKC and keep only Japanese-relevant characters."""
    if not text:
        return ""

    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace("\u3000", " ")
    filtered_chars = []
    for char in normalized:
        if char.isspace():
            filtered_chars.append(" ")
            continue
        code_point = ord(char)
        for start, end in _JAPANESE_RANGES:
            if ord(start) <= code_point <= ord(end):
                filtered_chars.append(char)
                break
    filtered_text = "".join(filtered_chars)
    filtered_text = re.sub(r"\s+", " ", filtered_text)
    return filtered_text.strip()


def _count_pages(pdf_path: Path) -> int:
    with pdf_path.open("rb") as stream:
        return sum(1 for _ in PDFPage.get_pages(stream))


def _ocr_page(pdf_path: Path, page_number: int) -> str:
    """Perform OCR on the given page using pytesseract configured for Japanese."""
    if convert_from_path is None or pytesseract is None:
        LOGGER.debug("OCR dependencies missing; skipping OCR for page %s", page_number)
        return ""

    try:
        images = convert_from_path(str(pdf_path), first_page=page_number, last_page=page_number)
    except Exception as exc:  # pragma: no cover - dependent on external binaries
        LOGGER.warning("Failed to rasterize page %s for OCR: %s", page_number, exc)
        return ""

    if not images:
        return ""

    image = images[0]
    try:
        text = pytesseract.image_to_string(image, lang="jpn")
    except Exception as exc:  # pragma: no cover - runtime issue
        LOGGER.warning("OCR failed on page %s: %s", page_number, exc)
        return ""

    return filter_non_japanese(text)


def extract_text_per_page(
    pdf_path: Path,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> List[str]:
    """Extract normalized Japanese text from each page of the PDF.

    Args:
        pdf_path: Path to the PDF document.
        progress_callback: Optional callable receiving the current page index
            (1-indexed) and total page count.

    Returns:
        A list of normalized Japanese strings, one for each page.
    """

    pdf_path = pdf_path.expanduser().resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    total_pages = _count_pages(pdf_path)
    texts: List[str] = []

    for index, page_layout in enumerate(extract_pages(str(pdf_path)), start=1):
        if progress_callback:
            progress_callback(index, total_pages)

        fragments = [
            element.get_text()
            for element in page_layout
            if isinstance(element, LTTextContainer)
        ]
        raw_text = "".join(fragments)
        normalized = filter_non_japanese(raw_text)

        if not normalized:
            normalized = _ocr_page(pdf_path, index)

        texts.append(normalized)

    return texts


def extract_text_from_txt(txt_path: Path) -> List[str]:
    """Read and normalize Japanese text from a UTF-8 encoded plain text file."""

    txt_path = txt_path.expanduser().resolve()
    with txt_path.open("r", encoding="utf-8") as handle:
        raw_text = handle.read()

    normalized = filter_non_japanese(raw_text)
    return [normalized]


__all__ = ["extract_text_per_page", "extract_text_from_txt", "filter_non_japanese"]
