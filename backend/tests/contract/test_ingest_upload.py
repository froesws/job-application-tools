"""Uploading creates a draft that can be read and discarded."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import pytest
from cvtailor.api.app import create_app
from cvtailor.storage.paths import Paths
from cvtailor.storage.profiles import save_master
from docx import Document
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

LONG = "Backend engineer with Python and PostgreSQL. " * 8


def pdf_bytes(text: str) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 720, text)
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def docx_bytes(text: str) -> bytes:
    document = Document()
    document.add_paragraph(text)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


@pytest.fixture()
def client(tmp_path: Path, master: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> TestClient:
    layout = Paths(profile_root=tmp_path / "profile", data_root=tmp_path / "data")
    save_master(layout, "software-engineer", master)
    monkeypatch.setenv("CVTAILOR_PROFILE_ROOT", str(layout.profile_root))
    monkeypatch.setenv("CVTAILOR_DATA_ROOT", str(layout.data_root))
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    return TestClient(create_app())


def upload(client: TestClient, files: list[tuple[str, bytes, str]]) -> Any:
    return client.post(
        "/api/ingestions",
        data={"profile": "software-engineer", "create_if_missing": "true"},
        files=[("files", (name, data, mime)) for name, data, mime in files],
    )


def test_a_text_pdf_creates_a_readable_draft(client: TestClient) -> None:
    created = upload(client, [("cv.pdf", pdf_bytes(LONG), "application/pdf")])

    assert created.status_code == 202
    draft = created.json()
    assert draft["state"] == "processing"
    assert draft["extraction"]["files_read"] == 1
    assert draft["sources"][0]["format"] == "pdf"

    read = client.get(f"/api/ingestions/{draft['id']}")
    assert read.status_code == 200
    body = read.json()
    assert body["blocks"]
    assert body["counts"]["pending"] == 0
    assert body["readiness"]["ready"] is False


def test_a_docx_is_accepted(client: TestClient) -> None:
    created = upload(client, [("cv.docx", docx_bytes(LONG), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")])

    assert created.status_code == 202
    assert created.json()["sources"][0]["format"] == "docx"


def test_a_scanned_file_is_skipped_and_named(client: TestClient) -> None:
    created = upload(
        client,
        [
            ("good.pdf", pdf_bytes(LONG), "application/pdf"),
            ("scan.pdf", pdf_bytes(""), "application/pdf"),
        ],
    )

    body = created.json()
    assert body["extraction"]["files_read"] == 1
    assert body["extraction"]["files_skipped"] == [{"name": "scan.pdf", "reason": "no_text_layer"}]


def test_only_scanned_files_fail_the_upload(client: TestClient) -> None:
    response = upload(client, [("scan.pdf", pdf_bytes(""), "application/pdf")])

    assert response.status_code == 422
    assert response.json()["code"] == "no_text_layer"


def test_an_unsupported_file_is_refused(client: TestClient) -> None:
    response = upload(client, [("cv.doc", b"binary", "application/msword")])

    assert response.status_code == 400
    assert response.json()["code"] == "unsupported_file"


def test_more_than_five_files_is_refused(client: TestClient) -> None:
    files = [(f"cv{index}.pdf", pdf_bytes(LONG), "application/pdf") for index in range(6)]

    response = upload(client, files)

    assert response.status_code == 400
    assert response.json()["code"] == "too_many_files"


def test_discard_removes_the_draft(client: TestClient) -> None:
    draft = upload(client, [("cv.pdf", pdf_bytes(LONG), "application/pdf")]).json()

    assert client.delete(f"/api/ingestions/{draft['id']}").status_code == 204
    assert client.get(f"/api/ingestions/{draft['id']}").status_code == 404


def test_the_uploaded_file_is_never_stored(client: TestClient, tmp_path: Path) -> None:
    draft = upload(client, [("cv.pdf", pdf_bytes(LONG), "application/pdf")]).json()

    directory = tmp_path / "data" / "ingestions" / draft["id"]
    assert sorted(path.name for path in directory.iterdir()) == ["blocks.json", "draft.json"]
