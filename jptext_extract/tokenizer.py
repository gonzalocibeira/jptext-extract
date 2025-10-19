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
        the reading. Canonical surface retains kanji when available.
    """

    tokenizer = _get_tokenizer()
    mode = SplitMode.C

    by_reading: Dict[str, str] = {}
    by_reading_pos: Dict[Tuple[str, Tuple[str, ...]], str] = {}

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

            key = (reading, pos[:2])
            existing = by_reading_pos.get(key)
            if existing is None:
                by_reading_pos[key] = surface
            else:
                if _contains_kanji(surface) and not _contains_kanji(existing):
                    by_reading_pos[key] = surface
                elif len(surface) < len(existing):
                    by_reading_pos[key] = surface

    for (reading, _pos), surface in by_reading_pos.items():
        current = by_reading.get(reading)
        if current is None:
            by_reading[reading] = surface
            continue
        if _contains_kanji(surface) and not _contains_kanji(current):
            by_reading[reading] = surface
        elif len(surface) < len(current):
            by_reading[reading] = surface

    sorted_items = sorted(by_reading.items(), key=lambda item: item[0])
    return sorted_items


__all__ = ["tokenize_and_deduplicate"]
