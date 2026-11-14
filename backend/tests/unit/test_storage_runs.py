"""Runs are written to a staging directory and renamed into place when complete."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

import pytest
from cvtailor.core.errors import RUN_NOT_FOUND, TailorError
from cvtailor.storage.paths import Paths
from cvtailor.storage.runs import (
    commit_run,
    create_staging,
    list_runs,
    new_run_id,
    read_run,
    run_dir,
)


def paths(root: Path) -> Paths:
    return Paths(profile_root=root / "profile", data_root=root / "data")


def test_run_id_is_sortable_and_unique() -> None:
    moment = datetime(2026, 11, 14, 15, 30, 0, tzinfo=UTC)

    first = new_run_id(moment)
    second = new_run_id(moment)

    assert re.fullmatch(r"20261114T153000Z-[0-9a-f]{4}", first)
    assert first != second
    assert sorted([second, first]) == sorted([first, second])


def test_commit_renames_the_staging_directory(tmp_path: Path) -> None:
    layout = paths(tmp_path)
    run_id = "20261114T153000Z-abcd"
    staging = create_staging(layout, run_id)
    (staging / "run.json").write_text("{}", encoding="utf-8")

    final = commit_run(staging, layout, run_id)

    assert final == run_dir(layout, run_id)
    assert (final / "run.json").is_file()
    assert not staging.exists()
    assert final.name == run_id


def test_listing_skips_staging_and_sorts_newest_first(tmp_path: Path) -> None:
    layout = paths(tmp_path)
    for run_id in ("20261114T100000Z-aaaa", "20261114T120000Z-bbbb"):
        directory = run_dir(layout, run_id)
        directory.mkdir(parents=True)
        (directory / "run.json").write_text("{}", encoding="utf-8")
    (layout.runs_root / ".tmp-20261114T130000Z-cccc").mkdir()

    assert list_runs(layout) == ["20261114T120000Z-bbbb", "20261114T100000Z-aaaa"]


def test_reading_an_unknown_run_is_typed(tmp_path: Path) -> None:
    with pytest.raises(TailorError) as caught:
        read_run(paths(tmp_path), "nope")

    assert caught.value.code == RUN_NOT_FOUND


def test_reading_a_run_returns_its_record(tmp_path: Path) -> None:
    layout = paths(tmp_path)
    directory = run_dir(layout, "20261114T100000Z-aaaa")
    directory.mkdir(parents=True)
    (directory / "run.json").write_text('{"id": "x"}', encoding="utf-8")

    assert read_run(layout, "20261114T100000Z-aaaa") == {"id": "x"}
