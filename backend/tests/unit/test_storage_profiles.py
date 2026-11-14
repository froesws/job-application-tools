"""Profiles are directories named by slug, listed in order, saved with a backup."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from cvtailor.core.errors import PROFILE_NOT_FOUND, TailorError
from cvtailor.storage.paths import Paths
from cvtailor.storage.profiles import (
    list_profiles,
    load_master,
    profile_dir,
    save_master,
)


def paths(root: Path) -> Paths:
    return Paths(profile_root=root, data_root=root / "data")


def test_profiles_are_listed_in_slug_order(tmp_path: Path) -> None:
    for slug in ("zeta", "alpha", "mid"):
        directory = tmp_path / slug
        directory.mkdir()
        (directory / "master.json").write_text("{}", encoding="utf-8")

    assert [summary.slug for summary in list_profiles(paths(tmp_path))] == [
        "alpha",
        "mid",
        "zeta",
    ]


def test_a_profile_with_a_blocklist_says_so(tmp_path: Path) -> None:
    guarded = tmp_path / "guarded"
    guarded.mkdir()
    (guarded / "master.json").write_text("{}", encoding="utf-8")
    (guarded / "blocklist.txt").write_text("Acme\n", encoding="utf-8")
    plain = tmp_path / "plain"
    plain.mkdir()
    (plain / "master.json").write_text("{}", encoding="utf-8")

    summaries = {summary.slug: summary.has_blocklist for summary in list_profiles(paths(tmp_path))}

    assert summaries == {"guarded": True, "plain": False}


def test_flat_examples_are_not_profiles(tmp_path: Path) -> None:
    (tmp_path / "master.example.json").write_text("{}", encoding="utf-8")
    directory = tmp_path / "without-master"
    directory.mkdir()

    assert list_profiles(paths(tmp_path)) == []


def test_load_master_reads_the_file(tmp_path: Path) -> None:
    directory = tmp_path / "demo"
    directory.mkdir()
    (directory / "master.json").write_text(json.dumps({"certs": {"en": "x"}}), encoding="utf-8")

    assert load_master(paths(tmp_path), "demo") == {"certs": {"en": "x"}}


def test_unknown_profile_is_a_typed_error(tmp_path: Path) -> None:
    with pytest.raises(TailorError) as caught:
        load_master(paths(tmp_path), "missing")

    assert caught.value.code == PROFILE_NOT_FOUND


def test_save_writes_pretty_json_and_keeps_a_backup(tmp_path: Path) -> None:
    master: dict[str, Any] = {"person": {"name": "A"}}
    save_master(paths(tmp_path), "demo", master)
    master["person"]["name"] = "B"
    save_master(paths(tmp_path), "demo", master)

    written = json.loads((tmp_path / "demo" / "master.json").read_text(encoding="utf-8"))
    backups = list((tmp_path / "demo").glob("master.json.bak.*"))

    assert written["person"]["name"] == "B"
    assert len(backups) == 1
    assert json.loads(backups[0].read_text(encoding="utf-8"))["person"]["name"] == "A"
    assert (tmp_path / "demo" / "master.json").read_text(encoding="utf-8").endswith("\n")


def test_profile_dir_is_built_from_the_slug(tmp_path: Path) -> None:
    assert profile_dir(paths(tmp_path), "demo") == tmp_path / "demo"
