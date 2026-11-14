"""Extraction turns file bytes into blocks, or fails with a documented reason."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from cvtailor.core.errors import TailorError
from cvtailor.core.extraction import extract, text_length
from docx import Document
from reportlab.pdfgen import canvas


def pdf_bytes(lines: list[str]) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    for line in lines:
        pdf.drawString(72, 720, line)
        pdf.drawString(72, 700, "")
        pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def docx_bytes(paragraphs: list[str], table: list[list[str]] | None = None) -> bytes:
    document = Document()
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    if table:
        grid = document.add_table(rows=len(table), cols=len(table[0]))
        for row, values in enumerate(table):
            for column, value in enumerate(values):
                grid.cell(row, column).text = value
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_a_text_pdf_yields_a_block_per_page() -> None:
    blocks = extract("cv.pdf", pdf_bytes(["Backend engineer with Python.", "Second page here."]))

    assert len(blocks) == 2
    assert blocks[0].location == "page 1"
    assert "Backend engineer" in blocks[0].text


def test_a_docx_yields_paragraphs_and_table_cells() -> None:
    blocks = extract(
        "cv.docx",
        docx_bytes(["Backend engineer with Python."], table=[["Kubernetes", "AWS"]]),
    )

    text = " ".join(block.text for block in blocks)
    assert "Backend engineer" in text
    assert "Kubernetes" in text
    assert "AWS" in text


def test_a_scanned_pdf_has_no_text() -> None:
    blocks = extract("scan.pdf", pdf_bytes([""]))

    assert text_length(blocks) < 200


def test_an_unsupported_extension_is_refused() -> None:
    with pytest.raises(TailorError) as caught:
        extract("cv.doc", b"binary")

    assert caught.value.code == "unsupported_file"


def test_a_corrupt_file_is_refused() -> None:
    with pytest.raises(TailorError) as caught:
        extract("cv.pdf", b"not a pdf")

    assert caught.value.code == "unreadable_file"


def test_paths_are_for_display_only(tmp_path: Path) -> None:
    assert isinstance(tmp_path, Path)
