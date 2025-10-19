"""Command-line interface for the jptext_extract package."""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Callable

from .pdf_processing import extract_text_from_txt, extract_text_per_page
from .tokenizer import tokenize_and_deduplicate


def _prompt(message: str, validator: Callable[[str], bool]) -> str:
    while True:
        try:
            value = input(message).strip()
        except EOFError:
            print("", file=sys.stderr)
            raise SystemExit(0)

        if validator(value):
            return value
        print("入力が正しくありません。もう一度試してください。")


def _ensure_csv_suffix(filename: str) -> str:
    if not filename.lower().endswith(".csv"):
        return f"{filename}.csv"
    return filename


def main() -> None:
    """Run the interactive extraction workflow."""
    print("JPText Extract — Japanese vocabulary extractor")
    print("Ctrl+C or type 'q' at the file prompt to exit.\n")

    while True:
        source_value = input("PDF or TXT path (or 'q' to quit): ").strip()
        if source_value.lower() in {"q", "quit", "exit"}:
            print("終了します。")
            return
        source_path = Path(source_value).expanduser()
        if not source_path.exists():
            print(f"ファイルが見つかりません: {source_path}")
            continue

        suffix = source_path.suffix.lower()
        if suffix not in {".pdf", ".txt"}:
            print("PDF または UTF-8 テキスト (.txt) を指定してください。")
            continue

        output_dir_value = _prompt(
            "Output directory: ",
            lambda value: bool(value.strip()),
        )
        output_dir = Path(output_dir_value).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        csv_name_value = _prompt(
            "CSV filename (without path): ",
            lambda value: bool(value.strip()),
        )
        csv_filename = _ensure_csv_suffix(csv_name_value)
        csv_path = output_dir / csv_filename

        try:
            if suffix == ".pdf":
                pages = extract_text_per_page(
                    source_path,
                    progress_callback=lambda current, total: print(
                        f"Processing page {current}/{total}..."
                    ),
                )
            else:
                pages = extract_text_from_txt(source_path)
        except Exception as exc:  # pragma: no cover - CLI feedback
            print(f"処理に失敗しました: {exc}")
            continue

        tokens = tokenize_and_deduplicate(pages)
        surfaces = [surface for _reading, surface in tokens if surface]

        try:
            with csv_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                for surface in surfaces:
                    writer.writerow([surface])
        except OSError as exc:  # pragma: no cover - IO errors
            print(f"Failed to write CSV: {exc}")
            continue

        print(f"Wrote {len(surfaces)} entries to {csv_path}")
        print("処理が完了しました。\n")


def entry_point() -> None:
    """Console script entry point."""
    try:
        main()
    except KeyboardInterrupt:  # pragma: no cover - user interruption
        print("\n終了します。")


if __name__ == "__main__":
    entry_point()
