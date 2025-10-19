"""Tokenization and deduplication helpers built around SudachiPy."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Dict, Iterable, List, Tuple

from sudachipy import dictionary, tokenizer as sudachi_tokenizer

LOGGER = logging.getLogger(__name__)

Tokenizer = sudachi_tokenizer.Tokenizer
SplitMode = sudachi_tokenizer.Tokenizer.SplitMode


@lru_cache(maxsize=1)
def _get_tokenizer() -> Tokenizer:
    """Create and cache a SudachiPy tokenizer instance."""
    return dictionary.Dictionary().create()


def _katakana_to_hiragana(text: str) -> str:
    result = []
    for char in text:
        code = ord(char)
        if 0x30A1 <= code <= 0x30F6:
            result.append(chr(code - 0x60))
        else:
            result.append(char)
    return "".join(result)


def _contains_kanji(text: str) -> bool:
    return any(0x4E00 <= ord(ch) <= 0x9FFF for ch in text)


def tokenize_and_deduplicate(texts: Iterable[str]) -> List[Tuple[str, str]]:
    """Tokenize text, deduplicate by reading, and keep canonical forms.

    Args:
        texts: Iterable of normalized Japanese text strings.

    Returns:
        A list of tuples ``(hiragana_reading, canonical_surface)`` sorted by
        the reading and prioritising kanji surfaces before kana for each
        reading. Canonical surface retains kanji when available and multiple
        surfaces for the same reading are preserved.
    """

    tokenizer = _get_tokenizer()
    mode = SplitMode.C

    by_reading: Dict[str, Dict[str, int]] = {}

    for text in texts:
        if not text:
            continue
        for morpheme in tokenizer.tokenize(text, mode):
            pos = morpheme.part_of_speech()
            if pos[0] == "記号":
                continue

            reading = _katakana_to_hiragana(morpheme.reading_form() or "")
            reading = reading.strip()
            if not reading:
                continue

            canonical = morpheme.dictionary_form() or morpheme.surface()
            if _contains_kanji(canonical):
                surface = canonical
            else:
                surface = morpheme.surface()

            reading_surfaces = by_reading.setdefault(reading, {})
            if surface not in reading_surfaces:
                reading_surfaces[surface] = len(reading_surfaces)

    results: List[Tuple[str, str]] = []
    for reading in sorted(by_reading.keys()):
        surfaces = by_reading[reading]
        ordered_surfaces = sorted(
            surfaces.items(),
            key=lambda item: (0 if _contains_kanji(item[0]) else 1, item[1]),
        )
        for surface, _order in ordered_surfaces:
            results.append((reading, surface))

    return results


__all__ = ["tokenize_and_deduplicate"]
