"""The remaining CLI commands: render, runs list, runs show, review."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from cvtailor.cli import main
from cvtailor.storage.paths import Paths
from cvtailor.storage.profiles import save_master


@pytest.fixture()
def workspace(tmp_path: Path, master: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    layout = Paths(profile_root=tmp_path / "profile", data_root=tmp_path / "data")
    master["experience"][0]["roles"][0]["bullets"][0]["en"] = "Built a Python service."
    save_master(layout, "software-engineer", master)
    monkeypatch.setenv("CVTAILOR_PROFILE_ROOT", str(layout.profile_root))
    monkeypatch.setenv("CVTAILOR_DATA_ROOT", str(layout.data_root))
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    posting = tmp_path / "posting.txt"
    posting.write_text("We are hiring a Backend Engineer with Python.", encoding="utf-8")
    assert main(["tailor", "--profile", "software-engineer", "--posting", str(posting), "--json"]) == 0
    run_ids = sorted(path.name for path in layout.runs_root.iterdir())
    return {"paths": layout, "run_id": run_ids[-1], "tmp_path": tmp_path}


def test_runs_list_returns_the_run(workspace: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["runs", "list", "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert [record["id"] for record in payload] == [workspace["run_id"]]


def test_runs_show_returns_the_record(workspace: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["runs", "show", workspace["run_id"], "--json"]) == 0

    record = json.loads(capsys.readouterr().out)
    assert record["profile"] == "software-engineer"
    assert record["mode"] == "tailor"
    assert record["review"]["coverage"] == 1.0


def test_render_creates_a_derived_run(workspace: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    selection = workspace["paths"].runs_root / workspace["run_id"] / "selection.json"
    payload = json.loads(selection.read_text(encoding="utf-8"))
    edited = workspace["tmp_path"] / "edited.json"
    payload["experience"] = {"role1": ["b2"]}
    edited.write_text(json.dumps(payload), encoding="utf-8")

    assert main([
        "render", "--profile", "software-engineer",
        "--origin", workspace["run_id"], "--selection", str(edited), "--json",
    ]) == 0

    result = json.loads(capsys.readouterr().out)
    record = json.loads(
        (workspace["paths"].runs_root / result["run_id"] / "run.json").read_text(encoding="utf-8")
    )
    assert record["mode"] == "render"
    assert record["origin_run_id"] == workspace["run_id"]


def test_review_quits(workspace: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("builtins.input", lambda prompt="": "quit")

    assert main(["review", workspace["run_id"]]) == 0
