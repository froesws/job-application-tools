"""A run that cannot satisfy a gate leaves nothing behind."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from cvtailor.core.errors import PAGE_OVERFLOW, TailorError
from cvtailor.llm.fake import FakeClient
from cvtailor.pipeline import run_tailor
from cvtailor.storage.paths import Paths


def huge_master(master: dict[str, Any]) -> dict[str, Any]:
    """Enough long content that even the smallest attempt exceeds one page."""
    template = copy.deepcopy(master)
    role_template = template["experience"][0]["roles"][0]
    entries = []
    for entry_index in range(4):
        roles = []
        for role_index in range(2):
            role = copy.deepcopy(role_template)
            role["id"] = f"role{entry_index}{role_index}"
            role["bullets"] = [
                {"id": f"b{entry_index}{role_index}{bullet_index}", "en": "x" * 1500, "pt": "x" * 1500}
                for bullet_index in range(7)
            ]
            roles.append(role)
        entries.append(
            {
                "header_en": f"Company {entry_index}",
                "header_pt": f"Company {entry_index}",
                "date_en": "2020-2024",
                "date_pt": "2020-2024",
                "roles": roles,
            }
        )
    template["experience"] = entries
    return template


def overflow_selection(master: dict[str, Any]) -> dict[str, Any]:
    return {
        "role_id": "sweng",
        "summary_ids": ["s1"],
        "experience": {
            role["id"]: [bullet["id"] for bullet in role["bullets"]]
            for entry in master["experience"]
            for role in entry["roles"]
        },
    }


def digest() -> dict[str, Any]:
    return {
        "enterprise_name": "Acme",
        "date": "2026-11-14",
        "job_title": "Backend Engineer",
        "level": "mid_level",
        "resume": "Builds services.",
        "hard_skills": ["Python"],
        "soft_skills": [],
    }


def test_an_overflowing_selection_is_refused_and_leaves_no_run(tmp_path: Path, master: dict[str, Any]) -> None:
    wide = huge_master(master)
    paths = Paths(profile_root=tmp_path / "profile", data_root=tmp_path / "data")
    client = FakeClient([json.dumps(digest()), json.dumps(overflow_selection(wide))])

    with pytest.raises(TailorError) as caught:
        run_tailor(
            paths=paths,
            master=wide,
            profile="software-engineer",
            posting="Backend Engineer.",
            language="en-US",
            client=client,
            models={"analyze": "fake:scripted", "tailor": "fake:scripted"},
            validation_retries=2,
        )

    assert caught.value.code == PAGE_OVERFLOW
    assert "experience_bullets" in caught.value.message
    assert not paths.runs_root.exists() or list(paths.runs_root.glob("*")) == []
