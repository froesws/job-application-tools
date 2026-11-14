"""The corpus is append-only and idempotent on the normalized posting."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cvtailor.storage.corpus import (
    append_if_new,
    normalize_posting,
    posting_hash,
    read_all,
)
from cvtailor.storage.paths import Paths

DIGEST: dict[str, Any] = {
    "enterprise_name": "Acme",
    "date": "2026-11-14",
    "job_title": "Backend Engineer",
    "level": "mid_level",
    "resume": "Builds services.",
    "hard_skills": ["Python"],
    "soft_skills": [],
}


def paths(tmp_path: Path) -> Paths:
    return Paths(profile_root=tmp_path / "profile", data_root=tmp_path / "data")


def test_normalization_ignores_spacing_and_case() -> None:
    assert normalize_posting("  Backend   Engineer \n") == "backend engineer"


def test_the_same_text_hashed_with_different_spacing_matches() -> None:
    assert posting_hash("Backend  Engineer") == posting_hash("backend engineer\n")


def test_a_new_posting_is_appended_once(tmp_path: Path) -> None:
    layout = paths(tmp_path)

    first = append_if_new(
        layout,
        digest=DIGEST,
        posting="Backend Engineer",
        date="2026-11-14",
        detected_language="en-US",
    )
    second = append_if_new(
        layout,
        digest=DIGEST,
        posting="backend   engineer\n",
        date="2026-11-14",
        detected_language="en-US",
    )

    assert first is True
    assert second is False
    assert len(read_all(layout)) == 1


def test_a_different_posting_is_appended(tmp_path: Path) -> None:
    layout = paths(tmp_path)
    append_if_new(layout, digest=DIGEST, posting="One", date="2026-11-14", detected_language="en-US")
    append_if_new(layout, digest=DIGEST, posting="Two", date="2026-11-14", detected_language="en-US")

    assert len(read_all(layout)) == 2


def test_the_record_holds_the_digest_and_never_the_posting(tmp_path: Path) -> None:
    layout = paths(tmp_path)
    append_if_new(
        layout,
        digest=DIGEST,
        posting="Secret posting text",
        date="2026-11-14",
        detected_language="pt-BR",
    )

    raw = layout.corpus_path.read_text(encoding="utf-8")
    record = json.loads(raw)

    assert record["digest"] == DIGEST
    assert record["hash"] == posting_hash("Secret posting text")
    assert record["detected_language"] == "pt-BR"
    assert record["date"] == "2026-11-14"
    assert "Secret posting" not in raw
