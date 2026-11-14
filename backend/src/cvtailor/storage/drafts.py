"""Draft persistence.

A draft holds the extracted text and the decisions taken so far. It is deleted on save, on
discard, and by a seven-day sweep, so personal data never accumulates on disk.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path

from cvtailor.core.errors import DRAFT_NOT_FOUND, TailorError
from cvtailor.core.extraction import Block
from cvtailor.core.ingestion import Draft
from cvtailor.storage.paths import Paths

TTL = timedelta(days=7)


def draft_dir(paths: Paths, draft_id: str) -> Path:
    return paths.ingestions_root / draft_id


def save_draft(paths: Paths, draft: Draft) -> None:
    directory = draft_dir(paths, draft.id)
    directory.mkdir(parents=True, exist_ok=True)
    temporary = directory / ".draft.json.tmp"
    temporary.write_text(json.dumps(draft.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(directory / "draft.json")


def load_draft(paths: Paths, draft_id: str) -> Draft:
    path = draft_dir(paths, draft_id) / "draft.json"
    if not path.is_file():
        raise TailorError(DRAFT_NOT_FOUND, f"Unknown draft: {draft_id}")
    return Draft.from_dict(json.loads(path.read_text(encoding="utf-8")))


def save_blocks(paths: Paths, draft_id: str, blocks: list[Block]) -> None:
    directory = draft_dir(paths, draft_id)
    directory.mkdir(parents=True, exist_ok=True)
    payload = [asdict(block) for block in blocks]
    (directory / "blocks.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_blocks(paths: Paths, draft_id: str) -> list[Block]:
    path = draft_dir(paths, draft_id) / "blocks.json"
    if not path.is_file():
        return []
    return [Block(**item) for item in json.loads(path.read_text(encoding="utf-8"))]


def delete_draft(paths: Paths, draft_id: str) -> None:
    directory = draft_dir(paths, draft_id)
    if not directory.is_dir():
        raise TailorError(DRAFT_NOT_FOUND, f"Unknown draft: {draft_id}")
    shutil.rmtree(directory)


def sweep(paths: Paths, *, now: datetime | None = None) -> list[str]:
    """Delete drafts older than the TTL. Returns the removed ids."""
    if not paths.ingestions_root.is_dir():
        return []
    moment = now or datetime.now()
    removed: list[str] = []
    for directory in paths.ingestions_root.iterdir():
        if not directory.is_dir():
            continue
        record = directory / "draft.json"
        if not record.is_file():
            continue
        draft = Draft.from_dict(json.loads(record.read_text(encoding="utf-8")))
        age = moment - datetime.fromisoformat(draft.updated_at)
        if age > TTL:
            shutil.rmtree(directory)
            removed.append(draft.id)
    return removed
