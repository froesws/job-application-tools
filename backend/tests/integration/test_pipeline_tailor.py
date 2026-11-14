"""A tailor run writes every artifact and a one-page PDF."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cvtailor.llm.fake import FakeClient
from cvtailor.pipeline import run_tailor
from cvtailor.storage.paths import Paths


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


def selection() -> dict[str, Any]:
    return {
        "role_id": "sweng",
        "summary_ids": ["s1"],
        "experience": {"role1": ["b1", "b2"]},
        "skill_priority": ["Python"],
        "project_ids": ["p1"],
    }


def test_a_tailor_run_writes_the_seven_artifacts(
    tmp_path: Path, master: dict[str, Any]
) -> None:
    paths = Paths(profile_root=tmp_path / "profile", data_root=tmp_path / "data")
    client = FakeClient([json.dumps(digest()), json.dumps(selection())])

    result = run_tailor(
        paths=paths,
        master=master,
        profile="software-engineer",
        posting="Backend Engineer. Python.",
        language="en-US",
        client=client,
        models={"analyze": "fake:scripted", "tailor": "fake:scripted"},
        validation_retries=2,
        now=datetime(2026, 11, 14, 15, 0, 0, tzinfo=UTC),
    )

    files = {path.name for path in result.run_dir.iterdir()}
    assert files == {
        "run.json",
        "digest.json",
        "analysis.json",
        "selection.json",
        "cv.pdf",
        "report.md",
        "posting.txt",
    }
    record = json.loads((result.run_dir / "run.json").read_text(encoding="utf-8"))
    assert record["profile"] == "software-engineer"
    assert record["mode"] == "tailor"
    assert record["requested_language"] == "en-US"
    assert result.pages == 1


def test_the_run_appends_one_corpus_record(
    tmp_path: Path, master: dict[str, Any]
) -> None:
    paths = Paths(profile_root=tmp_path / "profile", data_root=tmp_path / "data")
    for _ in range(2):
        client = FakeClient([json.dumps(digest()), json.dumps(selection())])
        run_tailor(
            paths=paths,
            master=master,
            profile="software-engineer",
            posting="Backend Engineer. Python.",
            language="en-US",
            client=client,
            models={"analyze": "fake:scripted", "tailor": "fake:scripted"},
            validation_retries=2,
        )

    lines = paths.corpus_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1


def test_a_blocklisted_bullet_stops_the_run(
    tmp_path: Path, master: dict[str, Any]
) -> None:
    from cvtailor.core.errors import BLOCKLIST_HIT, TailorError

    master["experience"][0]["roles"][0]["bullets"][0]["en"] = "Built Acme billing."
    paths = Paths(profile_root=tmp_path / "profile", data_root=tmp_path / "data")
    blocklist = paths.profile_root / "software-engineer" / "blocklist.txt"
    blocklist.parent.mkdir(parents=True)
    blocklist.write_text("Acme\n", encoding="utf-8")
    client = FakeClient([json.dumps(digest()), json.dumps(selection())])

    try:
        run_tailor(
            paths=paths,
            master=master,
            profile="software-engineer",
            posting="Backend Engineer.",
            language="en-US",
            client=client,
            models={"analyze": "fake:scripted", "tailor": "fake:scripted"},
            validation_retries=2,
        )
    except TailorError as error:
        assert error.code == BLOCKLIST_HIT
        assert error.item_ids == ["b1"]
    else:  # pragma: no cover - the assertion above is the point
        raise AssertionError("the blocklist did not stop the run")

    assert list(paths.runs_root.glob("*")) == []
