"""When the model never produces valid ids, the run still renders from scores."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cvtailor.llm.fake import FakeClient
from cvtailor.pipeline import run_tailor
from cvtailor.storage.paths import Paths

DIGEST = {
    "enterprise_name": "Acme",
    "date": "2026-11-14",
    "job_title": "Backend Engineer",
    "level": "mid_level",
    "resume": "Python services.",
    "hard_skills": ["Python"],
    "soft_skills": [],
}

INVALID = {"role_id": "ghost", "summary_ids": ["s1"]}


def test_a_model_that_never_validates_falls_back_and_renders(
    tmp_path: Path, master: dict[str, Any]
) -> None:
    paths = Paths(profile_root=tmp_path / "profile", data_root=tmp_path / "data")
    master["experience"][0]["roles"][0]["bullets"][0]["en"] = "Built a Python service."
    client = FakeClient([json.dumps(DIGEST), json.dumps(INVALID), json.dumps(INVALID)])

    result = run_tailor(
        paths=paths,
        master=master,
        profile="software-engineer",
        posting="We are hiring a Backend Engineer with Python.",
        language="en-US",
        client=client,
        models={"analyze": "fake:scripted", "tailor": "fake:scripted"},
        validation_retries=2,
    )

    record = json.loads((result.run_dir / "run.json").read_text(encoding="utf-8"))
    analysis = json.loads((result.run_dir / "analysis.json").read_text(encoding="utf-8"))
    assert result.pages == 1
    assert record["fallback_used"] is True
    assert analysis["pre_rank"]["bullets"]["b1"] > 0
    assert analysis["detected_language"] == "en-US"
    assert "Fallback used: yes" in (result.run_dir / "report.md").read_text(encoding="utf-8")
