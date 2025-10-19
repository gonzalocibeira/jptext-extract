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
  - [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) with the Japanese language pack (installed via Homebrew's `tesseract-lang` formula on macOS).
  - [Poppler](https://poppler.freedesktop.org/) utilities for `pdf2image` to render PDF pages.

The package itself depends on:

- `pdfminer.six`
- `pytesseract`
- `pdf2image`
- `SudachiPy`

Install Poppler and Tesseract using your operating system's package manager. On macOS with [Homebrew](https://brew.sh/):

```bash
brew update
brew install tesseract tesseract-lang poppler
```

The `tesseract-lang` formula installs additional language packs, including Japanese (`jpn`). After installation you can verify the
language data is available:

```bash
ls /opt/homebrew/share/tessdata  # Apple Silicon default prefix
ls /usr/local/share/tessdata     # Intel Mac default prefix
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

Run the interactive extractor by invoking the installed script (Homebrew typically places it on your `PATH`):

```bash
jptext-extract
# or use the full path if needed:
/opt/homebrew/bin/jptext-extract
```

You will be prompted for:

1. **PDF path** — enter the path to the Japanese-language PDF.
2. **Output directory** — the directory in which the CSV should be written.
3. **CSV filename** — the filename (without path). The tool will append `.csv` if needed.

While processing, the CLI reports progress for each page. When finished it writes a CSV containing one vocabulary term per row in UTF-8 encoding.

Exit the program at any time with `Ctrl+C` or by entering `q` at the PDF prompt.

### Running from a source checkout

To execute the CLI without installing the package, run it straight from the repository. On macOS with Homebrew, `python3`, and `pip3`, follow these steps:

1. **Clone the repository (if you haven't already) and switch to it:**

   ```bash
   git clone https://github.com/your-org/jptext-extract.git
   cd jptext-extract
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip3 install --upgrade pip
   ```

3. **Install the Python dependencies without installing the package itself.** These mirror the requirements declared in `pyproject.toml` and include the Sudachi dictionary data used by the tokenizer:

   ```bash
   pip3 install pdfminer.six pytesseract pdf2image sudachipy sudachidict_core
   ```

   SudachiPy needs a dictionary symlinked into place before it can tokenize text. Link the Core dictionary you just installed (or substitute `full` if you prefer the Full dictionary):

   ```bash
   python3 -m sudachipy link -t core
   ```

   You can switch dictionaries later with the same command by passing `small`, `core`, or `full`.

4. **Run the CLI from the repository root:**

   ```bash
   python3 -m jptext_extract.cli
   # or
   python3 jptext_extract/cli.py
   ```

This workflow keeps everything in an isolated environment, bypasses the `pip install` step that registers the console script, and is convenient when developing or testing local changes. When you're finished, exit the virtual environment with `deactivate`.

### Example session

```
JPText Extract — Japanese vocabulary extractor
Ctrl+C or type 'q' at the PDF prompt to exit.

PDF path (or 'q' to quit): /Users/you/Documents/japanese-article.pdf
Output directory: /Users/you/Desktop
CSV filename (without path): article_vocab
Processing page 1/5...
Processing page 2/5...
...
Wrote 128 entries to /Users/you/Desktop/article_vocab.csv
処理が完了しました。
```

### Programmatic usage

You can also call the modules directly in Python:

```python
from pathlib import Path

from jptext_extract.pdf_processing import extract_text_per_page
from jptext_extract.tokenizer import tokenize_and_deduplicate

pdf_path = Path("/Users/you/Documents/japanese-article.pdf")
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
