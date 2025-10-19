"""Tokenization and deduplication helpers built around SudachiPy."""

from __future__ import annotations

import logging
from collections import OrderedDict
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


def _register_surface(by_reading: Dict[str, Dict[str, object]], reading: str, surface: str) -> None:
    """Register a surface form for a reading, preferring kanji variants."""

    if not reading or not surface:
        return

    entry = by_reading.setdefault(
        reading,
        {"order": OrderedDict(), "has_kanji": False},
    )
    order: OrderedDict[str, int] = entry["order"]  # type: ignore[assignment]

    if surface in order:
        return

    contains_kanji = _contains_kanji(surface)

    if contains_kanji:
        if not entry["has_kanji"]:
            order.clear()
        entry["has_kanji"] = True
        order[surface] = len(order)
        return

    if entry["has_kanji"]:
        return

    order[surface] = len(order)


def tokenize_and_deduplicate(texts: Iterable[str]) -> List[Tuple[str, str]]:
    """Tokenize text, deduplicate by reading, and keep canonical forms.

    Args:
        texts: Iterable of normalized Japanese text strings.

    Returns:
        A list of tuples ``(hiragana_reading, canonical_surface)`` sorted by
        the reading. Kanji surfaces are preferred over kana duplicates while
        multi-word phrases are also emitted.
    """

    tokenizer = _get_tokenizer()
    mode = SplitMode.C

    by_reading: Dict[str, Dict[str, object]] = {}

    for text in texts:
        if not text:
            continue

        token_infos = []

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

            _register_surface(by_reading, reading, surface)

            token_infos.append(
                {
                    "reading": reading,
                    "surface": surface,
                    "original_surface": morpheme.surface(),
                    "pos_major": pos[0],
                }
            )

        if len(token_infos) >= 2 and any(info["pos_major"] != "名詞" for info in token_infos):
            phrase_reading = "".join(info["reading"] for info in token_infos).strip()
            phrase_surface = "".join(info["original_surface"] for info in token_infos).strip()
            _register_surface(by_reading, phrase_reading, phrase_surface)

    results: List[Tuple[str, str]] = []
    for reading in sorted(by_reading.keys()):
        order: OrderedDict[str, int] = by_reading[reading]["order"]  # type: ignore[assignment]
        results.extend((reading, surface) for surface in order.keys())

    return results


__all__ = ["tokenize_and_deduplicate"]
