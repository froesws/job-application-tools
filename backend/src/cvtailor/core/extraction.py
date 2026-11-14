"""File bytes in, text blocks out.

Deterministic and model-free. The uploaded file is never written anywhere: extraction
works on the bytes it is given and returns blocks with page or paragraph provenance, which
is what the quote verifier needs to point at the source.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

from cvtailor.core.errors import TailorError

UNSUPPORTED_FILE = "unsupported_file"
UNREADABLE_FILE = "unreadable_file"
NO_TEXT_LAYER = "no_text_layer"
MIN_CHARACTERS = 200


@dataclass(frozen=True)
class Block:
    index: int
    source: str
    location: str
    text: str


def extract(filename: str, data: bytes) -> list[Block]:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return _pdf(filename, data)
    if suffix == ".docx":
        return _docx(filename, data)
    raise TailorError(UNSUPPORTED_FILE, f"Unsupported file type: {suffix or filename}")


def text_length(blocks: list[Block]) -> int:
    return sum(len(block.text) for block in blocks)


def has_text_layer(blocks: list[Block]) -> bool:
    return text_length(blocks) >= MIN_CHARACTERS


def _pdf(filename: str, data: bytes) -> list[Block]:
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(data))
        pages = [(page.extract_text() or "").strip() for page in reader.pages]
    except Exception as error:  # pypdf raises several types for a broken file
        raise TailorError(UNREADABLE_FILE, f"Cannot read {filename}") from error
    return [
        Block(index=index, source=filename, location=f"page {index + 1}", text=text)
        for index, text in enumerate(pages)
        if text
    ]


def _docx(filename: str, data: bytes) -> list[Block]:
    from docx import Document

    try:
        document = Document(io.BytesIO(data))
    except Exception as error:
        raise TailorError(UNREADABLE_FILE, f"Cannot read {filename}") from error
    blocks: list[Block] = []
    for text in (paragraph.text.strip() for paragraph in document.paragraphs):
        if text:
            blocks.append(
                Block(index=len(blocks), source=filename, location=f"paragraph {len(blocks) + 1}", text=text)
            )
    for table_index, table in enumerate(document.tables):
        for row_index, row in enumerate(table.rows):
            for column, cell in enumerate(row.cells):
                text = cell.text.strip()
                if text:
                    blocks.append(
                        Block(
                            index=len(blocks),
                            source=filename,
                            location=f"table {table_index + 1}, row {row_index + 1}, cell {column + 1}",
                            text=text,
                        )
                    )
    return blocks
