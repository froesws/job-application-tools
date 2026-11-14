"""A derived run copies the origin's analysis and never touches the origin."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cvtailor.core.selection import Selection
from cvtailor.llm.fake import FakeClient
from cvtailor.pipeline import render_run, run_tailor
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

SELECTION = {
    "role_id": "sweng",
    "summary_ids": ["s1"],
    "experience": {"role1": ["b1"]},
    "project_ids": ["p1"],
}


def origin(tmp_path: Path, master: dict[str, Any]):
    paths = Paths(profile_root=tmp_path / "profile", data_root=tmp_path / "data")
    master["experience"][0]["roles"][0]["bullets"][0]["en"] = "Built a Python service."
    client = FakeClient([json.dumps(DIGEST), json.dumps(SELECTION)])
    return paths, run_tailor(
        paths=paths,
        master=master,
        profile="software-engineer",
        posting="Backend Engineer. Python.",
        language="en-US",
        client=client,
        models={"analyze": "fake:scripted", "tailor": "fake:scripted"},
        validation_retries=2,
    )


def test_a_derived_run_links_to_its_origin(tmp_path: Path, master: dict[str, Any]) -> None:
    paths, base = origin(tmp_path, master)
    selection = Selection(
        language="en-US",
        role_id="sweng",
        summary_ids=["s1"],
        experience={"role1": ["b2"]},
        project_ids=["p1"],
    )

    derived = render_run(
        paths=paths,
        master=master,
        profile="software-engineer",
        origin_run_id=base.run_id,
        selection=selection,
    )

    record = json.loads((derived.run_dir / "run.json").read_text(encoding="utf-8"))
    assert record["mode"] == "render"
    assert record["origin_run_id"] == base.run_id
    assert (derived.run_dir / "digest.json").is_file()
    assert (derived.run_dir / "analysis.json").is_file()
    assert derived.pages == 1


def test_the_origin_is_unchanged(tmp_path: Path, master: dict[str, Any]) -> None:
    paths, base = origin(tmp_path, master)
    before = {path.name: path.read_bytes() for path in base.run_dir.iterdir()}
    selection = Selection(language="en-US", role_id="sweng", summary_ids=["s1"], experience={"role1": ["b1"]})

    render_run(
        paths=paths,
        master=master,
        profile="software-engineer",
        origin_run_id=base.run_id,
        selection=selection,
    )

    after = {path.name: path.read_bytes() for path in base.run_dir.iterdir()}
    assert after == before
