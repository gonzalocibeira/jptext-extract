import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jptext_extract import cli as cli_module
from jptext_extract.pdf_processing import extract_text_from_txt


def test_extract_text_from_txt_filters_ascii(tmp_path):
    txt_path = tmp_path / "sample.txt"
    txt_path.write_text("abc カタカナ\n\u3000かな", encoding="utf-8")

    [result] = extract_text_from_txt(txt_path)

    assert result == "カタカナ かな"


def _iter_inputs(*responses):
    values = iter(responses)

    def _next_input(_prompt: str) -> str:
        try:
            return next(values)
        except StopIteration:  # pragma: no cover - defensive
            raise EOFError

    return _next_input


def test_cli_accepts_txt_file(monkeypatch, tmp_path):
    input_txt = tmp_path / "input.txt"
    input_txt.write_text("テスト", encoding="utf-8")

    output_dir = tmp_path / "output"

    called = {}

    def fake_extract_text_from_txt(path: Path):
        called["txt_path"] = path
        return ["正規化"]

    def fake_tokenize(pages):
        called["pages"] = pages
        return [("よみ", "語")]

    def fail_extract_pdf(*_args, **_kwargs):
        raise AssertionError("PDF extractor should not be used for .txt input")

    monkeypatch.setattr(cli_module, "extract_text_from_txt", fake_extract_text_from_txt)
    monkeypatch.setattr(cli_module, "tokenize_and_deduplicate", fake_tokenize)
    monkeypatch.setattr(cli_module, "extract_text_per_page", fail_extract_pdf)
    monkeypatch.setattr(
        "builtins.input",
        _iter_inputs(
            str(input_txt),
            str(output_dir),
            "vocab",  # CSV filename without suffix
            "q",  # Exit after first iteration
        ),
    )

    cli_module.main()

    csv_path = output_dir / "vocab.csv"
    assert csv_path.exists()
    assert called["txt_path"] == input_txt
    assert called["pages"] == ["正規化"]

    with csv_path.open("r", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))

    assert rows == [["語"]]
