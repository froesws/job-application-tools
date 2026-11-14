"""The HTTP contract: routes, shapes, statuses, and redaction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from cvtailor.api.app import create_app
from cvtailor.storage.paths import Paths
from cvtailor.storage.profiles import save_master
from fastapi.testclient import TestClient

POSTING = "We are hiring a Backend Engineer with Python."


@pytest.fixture()
def client(tmp_path: Path, master: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> TestClient:
    layout = Paths(profile_root=tmp_path / "profile", data_root=tmp_path / "data")
    master["experience"][0]["roles"][0]["bullets"][0]["en"] = "Built a Python service."
    save_master(layout, "software-engineer", master)
    monkeypatch.setenv("CVTAILOR_PROFILE_ROOT", str(layout.profile_root))
    monkeypatch.setenv("CVTAILOR_DATA_ROOT", str(layout.data_root))
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    return TestClient(create_app())


def test_profiles_are_listed_in_order(client: TestClient) -> None:
    response = client.get("/api/profiles")

    assert response.status_code == 200
    assert response.json() == {"profiles": [{"slug": "software-engineer", "has_blocklist": False}]}


def test_analyze_returns_the_digest_and_appends_once(client: TestClient) -> None:
    first = client.post("/api/jobs/analyze", json={"posting": POSTING})
    second = client.post("/api/jobs/analyze", json={"posting": POSTING})

    body = first.json()
    assert first.status_code == 200
    assert set(body["digest"]) == {
        "enterprise_name",
        "date",
        "job_title",
        "level",
        "resume",
        "hard_skills",
        "soft_skills",
    }
    assert body["corpus_appended"] is True
    assert second.json()["corpus_appended"] is False


def test_tailor_writes_a_run_the_other_routes_serve(client: TestClient) -> None:
    created = client.post("/api/tailor", json={"posting": POSTING, "profile": "software-engineer"})

    assert created.status_code == 201
    summary = created.json()
    run_id = summary["id"]
    assert summary["mode"] == "tailor"

    listed = client.get("/api/runs").json()["runs"]
    assert [run["id"] for run in listed] == [run_id]

    detail = client.get(f"/api/runs/{run_id}").json()
    assert detail["digest"]["job_title"]
    assert detail["selection"]["role_id"]
    assert detail["review"]["coverage"] == 1.0

    pdf = client.get(f"/api/runs/{run_id}/cv.pdf")
    report = client.get(f"/api/runs/{run_id}/report.md")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert report.status_code == 200
    assert "coverage" in report.text.lower()


def test_render_derives_from_an_origin(client: TestClient) -> None:
    origin = client.post("/api/tailor", json={"posting": POSTING, "profile": "software-engineer"}).json()
    selection = client.get(f"/api/runs/{origin['id']}").json()["selection"]

    derived = client.post(
        "/api/render",
        json={"profile": "software-engineer", "origin_run_id": origin["id"], "selection": selection},
    )

    assert derived.status_code == 201
    assert derived.json()["origin_run_id"] == origin["id"]
    assert derived.json()["mode"] == "render"


def test_settings_report_state_without_the_key_value(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret-value")

    body = client.get("/api/settings").json()

    assert isinstance(body["api_key_set"], bool)
    assert body["chains"]["analyze"][0]["provider"] == "fake"
    assert "sk-secret-value" not in json.dumps(body)


def test_an_empty_posting_is_a_documented_error(client: TestClient) -> None:
    response = client.post("/api/jobs/analyze", json={"posting": "   "})

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_posting"


def test_an_unknown_profile_is_not_found(client: TestClient) -> None:
    response = client.post(
        "/api/tailor", json={"posting": POSTING, "profile": "missing"}
    )

    assert response.status_code == 404
    assert response.json()["code"] == "profile_not_found"


def test_the_posting_never_appears_in_a_response(client: TestClient) -> None:
    created = client.post("/api/tailor", json={"posting": POSTING, "profile": "software-engineer"})
    run_id = created.json()["id"]

    for path in ("/api/runs", f"/api/runs/{run_id}", f"/api/runs/{run_id}/report.md"):
        assert POSTING not in client.get(path).text
