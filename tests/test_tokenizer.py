import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jptext_extract import tokenizer as tokenizer_module


class StubMorpheme:
    def __init__(self, surface, reading, dictionary_form, pos):
        self._surface = surface
        self._reading = reading
        self._dictionary_form = dictionary_form
        self._pos = pos

    def part_of_speech(self):
        return self._pos

    def reading_form(self):
        return self._reading

    def dictionary_form(self):
        return self._dictionary_form

    def surface(self):
        return self._surface


@pytest.fixture
def stub_tokenizer():
    noun = ("名詞", "普通名詞", "一般", "*", "*", "*")

    token_sequences = {
        "sample1": [
            StubMorpheme("橋", "ハシ", "橋", noun),
            StubMorpheme("端", "ハシ", "端", noun),
        ],
        "sample2": [
            StubMorpheme("仮名", "カナ", "仮名", noun),
            StubMorpheme("かな", "カナ", "", noun),
        ],
        "sample3": [
            StubMorpheme("東京タワー", "トウキョウタワー", "東京タワー", noun),
            StubMorpheme("タワー", "トウキョウタワー", "タワー", noun),
        ],
    }

    def tokenize(text, _mode):
        return token_sequences.get(text, [])

    return types.SimpleNamespace(tokenize=tokenize)


def test_tokenize_and_deduplicate_preserves_homophones(monkeypatch, stub_tokenizer):
    monkeypatch.setattr(tokenizer_module, "_get_tokenizer", lambda: stub_tokenizer)

    result = tokenizer_module.tokenize_and_deduplicate(["sample1", "sample2", "sample3"])

    assert result == [
        ("かな", "仮名"),
        ("かな", "かな"),
        ("とうきょうたわー", "東京タワー"),
        ("とうきょうたわー", "タワー"),
        ("はし", "橋"),
        ("はし", "端"),
    ]
