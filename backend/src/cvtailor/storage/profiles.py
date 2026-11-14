"""Profiles on disk: one directory per slug, a master, an optional blocklist.

Saving is atomic and keeps a timestamped copy of what was there, because the master is
the only source of candidate facts and losing it means losing the CV.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cvtailor.core.errors import PROFILE_NOT_FOUND, TailorError
from cvtailor.storage.paths import Paths

MASTER = "master.json"
BLOCKLIST = "blocklist.txt"


@dataclass(frozen=True)
class ProfileSummary:
    slug: str
    has_blocklist: bool


def profile_dir(paths: Paths, slug: str) -> Path:
    return paths.profile_root / slug


def list_profiles(paths: Paths) -> list[ProfileSummary]:
    """List directories holding a master, in slug order. Flat examples are ignored."""
    if not paths.profile_root.is_dir():
        return []
    summaries = [
        ProfileSummary(slug=directory.name, has_blocklist=(directory / BLOCKLIST).is_file())
        for directory in paths.profile_root.iterdir()
        if directory.is_dir() and (directory / MASTER).is_file()
    ]
    return sorted(summaries, key=lambda summary: summary.slug)


def load_master(paths: Paths, slug: str) -> dict[str, Any]:
    path = profile_dir(paths, slug) / MASTER
    if not path.is_file():
        raise TailorError(PROFILE_NOT_FOUND, f"Unknown profile: {slug}")
    return json.loads(path.read_text(encoding="utf-8"))


def save_master(paths: Paths, slug: str, master: dict[str, Any]) -> Path:
    """Write the master atomically, backing up whatever was there first."""
    directory = profile_dir(paths, slug)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / MASTER
    if target.is_file():
        backup = directory / f"{MASTER}.bak.{_timestamp()}"
        backup.write_bytes(target.read_bytes())
    temporary = directory / f".{MASTER}.tmp"
    temporary.write_text(json.dumps(master, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, target)
    return target


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
