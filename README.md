# JPText Extract

JPText Extract is a small toolkit for extracting Japanese text from PDF documents and converting it into a deduplicated vocabulary list. It combines PDF parsing, OCR fallback, and SudachiPy-based tokenization to produce a CSV of Japanese terms ordered by their readings.

## Features

- **PDF text extraction** powered by `pdfminer.six`, with automatic normalization to retain only Japanese characters.
- **OCR fallback** using `pytesseract` and `pdf2image` when a PDF page lacks selectable text (requires external binaries).
- **Vocabulary tokenization** via SudachiPy, deduplicating entries while preferring kanji forms when available.
- **Interactive CLI workflow** for quickly turning a PDF into a CSV vocabulary file.

## Requirements

- Python 3.9+
- System dependencies for OCR support (optional but recommended):
  - [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) with the Japanese language pack (`tesseract-ocr-jpn` on many distributions).
  - [Poppler](https://poppler.freedesktop.org/) utilities for `pdf2image` to render PDF pages.

The package itself depends on:

- `pdfminer.six`
- `pytesseract`
- `pdf2image`
- `SudachiPy`

Install Poppler and Tesseract using your operating system's package manager. On Ubuntu/Debian for example:

```bash
sudo apt update && sudo apt install tesseract-ocr tesseract-ocr-jpn poppler-utils
```

## Installation

Install the package from a local checkout:

```bash
pip install .
```

Or install directly from source using `pip`:

```bash
pip install git+https://github.com/your-org/jptext-extract.git
```

This installs the `jptext-extract` console script.

## Usage

### CLI workflow

Run the interactive extractor by invoking the installed script:

```bash
jptext-extract
```

You will be prompted for:

1. **PDF path** — enter the path to the Japanese-language PDF.
2. **Output directory** — the directory in which the CSV should be written.
3. **CSV filename** — the filename (without path). The tool will append `.csv` if needed.

While processing, the CLI reports progress for each page. When finished it writes a CSV containing one vocabulary term per row in UTF-8 encoding.

Exit the program at any time with `Ctrl+C` or by entering `q` at the PDF prompt.

### Example session

```
JPText Extract — Japanese vocabulary extractor
Ctrl+C or type 'q' at the PDF prompt to exit.

PDF path (or 'q' to quit): ~/Documents/japanese-article.pdf
Output directory: ~/Desktop
CSV filename (without path): article_vocab
Processing page 1/5...
Processing page 2/5...
...
Wrote 128 entries to /home/user/Desktop/article_vocab.csv
処理が完了しました。
```

### Programmatic usage

You can also call the modules directly in Python:

```python
from pathlib import Path

from jptext_extract.pdf_processing import extract_text_per_page
from jptext_extract.tokenizer import tokenize_and_deduplicate

pdf_path = Path("~/Documents/japanese-article.pdf").expanduser()
pages = extract_text_per_page(pdf_path)
entries = tokenize_and_deduplicate(pages)

for reading, surface in entries[:10]:
    print(reading, surface)
```

`extract_text_per_page` returns a list of normalized strings per page, automatically running OCR if a page has no embedded text. `tokenize_and_deduplicate` produces `(reading, surface)` pairs sorted by their reading.

## Troubleshooting

- **OCR dependencies missing**: If OCR libraries are unavailable, the extractor logs a debug message and skips OCR fallback. Install Tesseract and Poppler as described above.
- **No text extracted**: Some PDFs may be scanned images without embedded text; make sure OCR dependencies are installed so the fallback path can recover the text.
- **Sudachi dictionaries**: The default SudachiPy installation downloads the Small dictionary. Install the Core or Full dictionary if you need broader vocabulary coverage (`pip install sudachidict_core`).

## Development

Clone the repository and install the project in editable mode with development dependencies:

```bash
git clone https://github.com/your-org/jptext-extract.git
cd jptext-extract
pip install -e .[dev]
```

Run the CLI from source via `python -m jptext_extract.cli` during development.

## License

This project is licensed under the terms of the [MIT License](LICENSE.md).
