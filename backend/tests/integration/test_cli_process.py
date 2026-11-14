"""The CLI as a process: stdout is JSON and the exit code carries the outcome."""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from cvtailor.storage.paths import Paths
from cvtailor.storage.profiles import MASTER, save_master

BACKEND_SRC = Path(__file__).resolve().parents[2] / "src"


def run_cli(tmp_path: Path, profile: str, posting: str) -> subprocess.CompletedProcess[str]:
    posting_path = tmp_path / "posting.txt"
    posting_path.write_text(posting, encoding="utf-8")
    env = {
        **os.environ,
        "PYTHONPATH": str(BACKEND_SRC),
        "CVTAILOR_PROFILE_ROOT": str(tmp_path / "profile"),
        "CVTAILOR_DATA_ROOT": str(tmp_path / "data"),
        "LLM_PROVIDER": "fake",
    }
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "cvtailor.cli",
            "tailor",
            "--profile",
            profile,
            "--posting",
            str(posting_path),
            "--json",
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
        check=False,
    )


def test_success_exits_zero(tmp_path: Path, master: dict[str, Any]) -> None:
    save_master(Paths(profile_root=tmp_path / "profile", data_root=tmp_path / "data"), "demo", master)

    result = run_cli(tmp_path, "demo", "Backend Engineer. Python.")

    assert result.returncode == 0
    assert json.loads(result.stdout)["pages"] == 1


def test_unknown_profile_exits_nine(tmp_path: Path) -> None:
    result = run_cli(tmp_path, "missing", "Backend Engineer.")

    assert result.returncode == 9
    assert json.loads(result.stdout)["code"] == "profile_not_found"


def test_empty_posting_exits_three(tmp_path: Path, master: dict[str, Any]) -> None:
    save_master(Paths(profile_root=tmp_path / "profile", data_root=tmp_path / "data"), "demo", master)

    result = run_cli(tmp_path, "demo", "   ")

    assert result.returncode == 3


def test_a_blocklisted_bullet_exits_four(tmp_path: Path, master: dict[str, Any]) -> None:
    layout = Paths(profile_root=tmp_path / "profile", data_root=tmp_path / "data")
    guarded = copy.deepcopy(master)
    guarded["experience"][0]["roles"][0]["bullets"][0]["pt"] = "Trabalhou na Acme."
    save_master(layout, "demo", guarded)
    (layout.profile_root / "demo" / "blocklist.txt").write_text("Acme\n", encoding="utf-8")

    result = run_cli(tmp_path, "demo", "Backend Engineer.")

    assert result.returncode == 4
    assert json.loads(result.stdout)["item_ids"] == ["b1"]


def test_the_master_file_is_the_one_the_cli_reads(tmp_path: Path, master: dict[str, Any]) -> None:
    layout = Paths(profile_root=tmp_path / "profile", data_root=tmp_path / "data")
    save_master(layout, "demo", master)
    assert (layout.profile_root / "demo" / MASTER).is_file()

    result = run_cli(tmp_path, "demo", "Backend Engineer.")

    assert result.returncode == 0
