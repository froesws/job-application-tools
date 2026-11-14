"""The report carries the review material and never leaks the posting."""

from __future__ import annotations

from typing import Any

from cvtailor.core.gaps import GapReport
from cvtailor.core.layout import LayoutReport, LayoutWarning
from cvtailor.core.report import render_report

DIGEST: dict[str, Any] = {
    "enterprise_name": "Acme",
    "date": "2026-11-14",
    "job_title": "Backend Engineer",
    "level": "mid_level",
    "resume": "Builds services.",
    "hard_skills": ["Python", "PostgreSQL"],
    "soft_skills": ["Ownership"],
}


def report(layout: LayoutReport | None = None) -> str:
    return render_report(
        digest=DIGEST,
        section_counts={"summaries": 1, "experience_bullets": 2, "research_bullets": 0, "projects": 1, "skills": 1},
        layout=layout
        or LayoutReport(pages=1, overflow=False, warnings=[], section_counts={}),
        gap_report=GapReport(
            gaps=[{"skill": "PostgreSQL", "severity": "must_have"}],
            coverage=0.5,
            red_flags=[{"code": "uncovered_must_have", "message": "Some hard skills are not in the CV."}],
            section_counts={},
            checklist=["Confirm the enterprise name."],
        ),
        models={"analyze": {"id": "fake:scripted", "admitted": False}, "tailor": {"id": "fake:scripted", "admitted": False}},
        retries={"analyze": 0, "tailor": 1},
        fallback_used=False,
        profile="software-engineer",
    )


def test_the_report_repeats_the_digest() -> None:
    text = report()

    assert "Acme" in text
    assert "Backend Engineer" in text
    assert "mid_level" in text
    assert "Python" in text
    assert "Ownership" in text


def test_the_report_shows_counts_models_and_retries() -> None:
    text = report()

    assert "experience_bullets" in text
    assert "fake:scripted" in text
    assert "1" in text


def test_the_report_marks_an_unadmitted_model() -> None:
    assert "model_unadmitted" in report()


def test_gaps_coverage_and_checklist_are_in_the_report() -> None:
    text = report()

    assert "PostgreSQL" in text
    assert "50%" in text
    assert "uncovered_must_have" in text
    assert "Confirm the enterprise name." in text


def test_layout_warnings_are_repeated_in_the_report() -> None:
    layout = LayoutReport(
        pages=1,
        overflow=False,
        warnings=[LayoutWarning(code="bullets_trimmed", detail="2 bullets dropped.", removed_bullet_ids=("b2",))],
        section_counts={},
    )

    assert "b2" in report(layout)
