"""Roots come from the environment, with repository-relative defaults."""

from __future__ import annotations

from pathlib import Path

import pytest
from cvtailor.storage.paths import from_env


def test_environment_overrides_the_roots(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CVTAILOR_PROFILE_ROOT", str(tmp_path / "p"))
    monkeypatch.setenv("CVTAILOR_DATA_ROOT", str(tmp_path / "d"))

    paths = from_env()

    assert paths.profile_root == tmp_path / "p"
    assert paths.data_root == tmp_path / "d"
    assert paths.runs_root == tmp_path / "d" / "runs"
    assert paths.corpus_path == tmp_path / "d" / "corpus.jsonl"


def test_defaults_are_repository_relative(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("CVTAILOR_PROFILE_ROOT", raising=False)
    monkeypatch.delenv("CVTAILOR_DATA_ROOT", raising=False)
    monkeypatch.chdir(tmp_path)

    paths = from_env()

    assert paths.profile_root == Path("profile")
    assert paths.data_root == Path("data")
    assert paths.runs_root == Path("data") / "runs"
