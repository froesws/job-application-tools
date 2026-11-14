"""Drafts live under the data root, are read back intact, and expire."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cvtailor.core.extraction import Block
from cvtailor.core.ingestion import Draft, DraftItem, new_draft_sections
from cvtailor.storage.drafts import (
    delete_draft,
    draft_dir,
    load_blocks,
    load_draft,
    save_blocks,
    save_draft,
    sweep,
)
from cvtailor.storage.paths import Paths


def paths(tmp_path: Path) -> Paths:
    return Paths(profile_root=tmp_path / "profile", data_root=tmp_path / "data")


def draft(moment: datetime) -> Draft:
    return Draft(
        id="20261114T150000Z-abcd",
        created_at=moment.isoformat(),
        updated_at=moment.isoformat(),
        profile="software-engineer",
        create_if_missing=True,
        state="processing",
        sources=[{"name": "cv.pdf", "bytes": 10, "hash": "h", "format": "pdf"}],
        sections=new_draft_sections(),
        items=[DraftItem(id="it-1", kind="bullet", section="experience", fields={"en": "x"})],
        extraction={"blocks": 1, "characters": 10, "files_read": 1, "files_skipped": []},
    )


def test_a_draft_round_trips(tmp_path: Path) -> None:
    layout = paths(tmp_path)
    moment = datetime(2026, 11, 14, 15, 0, tzinfo=UTC)
    original = draft(moment)

    save_draft(layout, original)
    restored = load_draft(layout, original.id)

    assert restored.to_dict() == original.to_dict()
    assert json.loads((draft_dir(layout, original.id) / "draft.json").read_text())["profile"] == "software-engineer"


def test_blocks_round_trip(tmp_path: Path) -> None:
    layout = paths(tmp_path)
    blocks = [Block(index=0, source="cv.pdf", location="page 1", text="Python")]

    save_blocks(layout, "d1", blocks)

    assert load_blocks(layout, "d1") == blocks


def test_deleting_removes_the_draft(tmp_path: Path) -> None:
    layout = paths(tmp_path)
    save_draft(layout, draft(datetime.now(UTC)))

    delete_draft(layout, "20261114T150000Z-abcd")

    assert not draft_dir(layout, "20261114T150000Z-abcd").exists()


def test_the_sweep_removes_drafts_older_than_seven_days(tmp_path: Path) -> None:
    layout = paths(tmp_path)
    old = datetime.now(UTC) - timedelta(days=8)
    fresh = datetime.now(UTC)
    save_draft(layout, draft(old))
    fresh_draft = draft(fresh)
    fresh_draft.id = "20261114T160000Z-beef"
    save_draft(layout, fresh_draft)

    removed = sweep(layout, now=fresh)

    assert removed == ["20261114T150000Z-abcd"]
    assert draft_dir(layout, "20261114T160000Z-beef").exists()
