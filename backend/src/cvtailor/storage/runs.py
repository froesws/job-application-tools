"""Run directories: staging first, rename last, so a crash never leaves a half-run.

Ids are UTC timestamps with a short random suffix: sortable, and distinct even when two
runs start in the same second.
"""

from __future__ import annotations

import json
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cvtailor.core.errors import RUN_NOT_FOUND, TailorError
from cvtailor.storage.paths import Paths

RECORD = "run.json"


def new_run_id(moment: datetime | None = None) -> str:
    stamp = (moment or datetime.now(UTC)).astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{secrets.token_hex(2)}"


def run_dir(paths: Paths, run_id: str) -> Path:
    return paths.runs_root / run_id


def create_staging(paths: Paths, run_id: str) -> Path:
    staging = paths.runs_root / f".tmp-{run_id}"
    staging.mkdir(parents=True, exist_ok=False)
    return staging


def commit_run(staging: Path, paths: Paths, run_id: str) -> Path:
    final = run_dir(paths, run_id)
    staging.rename(final)
    return final


def list_runs(paths: Paths) -> list[str]:
    """Completed runs, newest first. Staging directories are invisible."""
    if not paths.runs_root.is_dir():
        return []
    run_ids = [
        directory.name
        for directory in paths.runs_root.iterdir()
        if directory.is_dir() and not directory.name.startswith(".tmp-")
        and (directory / RECORD).is_file()
    ]
    return sorted(run_ids, reverse=True)


def read_run(paths: Paths, run_id: str) -> dict[str, Any]:
    path = run_dir(paths, run_id) / RECORD
    if not path.is_file():
        raise TailorError(RUN_NOT_FOUND, f"Unknown run: {run_id}")
    return json.loads(path.read_text(encoding="utf-8"))
