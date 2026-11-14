"""Gaps, coverage, and red flags are computed from the selection, never from a model."""

from __future__ import annotations

from typing import Any

from cvtailor.core.gaps import build_gap_report
from cvtailor.core.layout import LayoutReport, LayoutWarning
from cvtailor.core.selection import Selection

DIGEST: dict[str, Any] = {
    "enterprise_name": "Acme",
    "date": "2026-11-14",
    "job_title": "Backend Engineer",
    "level": "mid_level",
    "resume": "Python and PostgreSQL.",
    "hard_skills": ["Python", "PostgreSQL"],
    "soft_skills": [],
}


def selection(**overrides: Any) -> Selection:
    payload: dict[str, Any] = {
        "language": "en-US",
        "role_id": "sweng",
        "summary_ids": ["s1"],
        "experience": {"role1": ["b1", "b2"]},
        "project_ids": ["p1"],
    }
    payload.update(overrides)
    return Selection(**payload)


def layout(**kwargs: Any) -> LayoutReport:
    return LayoutReport(pages=1, overflow=False, warnings=kwargs.get("warnings", []), section_counts={"summaries": 1})


def test_a_covered_skill_is_not_a_gap(master: dict[str, Any]) -> None:
    master["experience"][0]["roles"][0]["bullets"][0]["en"] = "Built a Python service."

    report = build_gap_report(master, DIGEST, selection(), layout(), models_admitted=False)

    assert [gap["skill"] for gap in report.gaps] == ["PostgreSQL"]


def test_coverage_is_the_share_of_hard_skills_covered(master: dict[str, Any]) -> None:
    master["experience"][0]["roles"][0]["bullets"][0]["en"] = "Built a Python service."

    report = build_gap_report(master, DIGEST, selection(), layout(), models_admitted=False)

    assert report.coverage == 0.5


def test_an_uncovered_gap_is_a_red_flag(master: dict[str, Any]) -> None:
    report = build_gap_report(master, DIGEST, selection(), layout(), models_admitted=True)

    assert any(flag["code"] == "uncovered_must_have" for flag in report.red_flags)


def test_trimming_is_a_red_flag(master: dict[str, Any]) -> None:
    master["experience"][0]["roles"][0]["bullets"][0]["en"] = "Python"

    trimmed = LayoutReport(
        pages=1,
        overflow=False,
        warnings=[LayoutWarning(code="bullets_trimmed", detail="dropped", removed_bullet_ids=("b2",))],
        section_counts={},
    )

    report = build_gap_report(master, DIGEST, selection(), trimmed, models_admitted=True)

    assert any(flag["code"] == "auto_fit_trimmed" for flag in report.red_flags)


def test_an_unadmitted_model_is_a_red_flag(master: dict[str, Any]) -> None:
    report = build_gap_report(master, DIGEST, selection(), layout(), models_admitted=False)

    assert any(flag["code"] == "model_unadmitted" for flag in report.red_flags)


def test_the_checklist_is_fixed(master: dict[str, Any]) -> None:
    report = build_gap_report(master, DIGEST, selection(), layout(), models_admitted=True)

    assert report.checklist
    assert all(isinstance(item, str) and item for item in report.checklist)
