"""The CLI is a thin adapter: it reads input, calls the service, and maps codes to exits."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from cvtailor.cli import main
from cvtailor.storage.paths import Paths
from cvtailor.storage.profiles import save_master


@pytest.fixture()
def cli_env(tmp_path: Path, master: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> Paths:
    layout = Paths(profile_root=tmp_path / "profile", data_root=tmp_path / "data")
    save_master(layout, "software-engineer", master)
    monkeypatch.setenv("CVTAILOR_PROFILE_ROOT", str(layout.profile_root))
    monkeypatch.setenv("CVTAILOR_DATA_ROOT", str(layout.data_root))
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    return layout


def test_tailor_prints_one_json_object(
    cli_env: Paths, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    posting = tmp_path / "posting.txt"
    posting.write_text("Backend Engineer. Python.", encoding="utf-8")

    exit_code = main(
        ["tailor", "--profile", "software-engineer", "--posting", str(posting), "--json"]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["pages"] == 1
    assert payload["profile"] == "software-engineer"
    assert Path(payload["pdf_path"]).is_file()
    assert Path(payload["report_path"]).is_file()


def test_an_unknown_profile_exits_nine(
    cli_env: Paths, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    posting = tmp_path / "posting.txt"
    posting.write_text("Backend Engineer.", encoding="utf-8")

    exit_code = main(["tailor", "--profile", "missing", "--posting", str(posting), "--json"])

    error = json.loads(capsys.readouterr().out)
    assert exit_code == 9
    assert error["code"] == "profile_not_found"


def test_an_empty_posting_exits_three(
    cli_env: Paths, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    posting = tmp_path / "posting.txt"
    posting.write_text("   ", encoding="utf-8")

    exit_code = main(
        ["tailor", "--profile", "software-engineer", "--posting", str(posting), "--json"]
    )

    assert exit_code == 3
    assert json.loads(capsys.readouterr().out)["code"] == "invalid_posting"


def test_a_missing_posting_file_is_a_usage_error(
    cli_env: Paths, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main(
        ["tailor", "--profile", "software-engineer", "--posting", "/nope/missing.txt", "--json"]
    )

    assert exit_code == 2
