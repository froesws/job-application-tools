"""Page-fit evaluation: overflow is an error, trimming and scaling are warnings."""

from __future__ import annotations

from typing import Any

from cvtailor.core.layout import evaluate
from cvtailor.core.selection import Selection


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


def render(pages: int = 1, font_scale: float = 1.0, bullet_cap: int | None = None) -> dict[str, Any]:
    return {"pages": pages, "font_scale": font_scale, "bullet_cap": bullet_cap, "font": "CV", "path": "cv.pdf"}


def test_a_clean_fit_has_no_warnings(master: dict[str, Any]) -> None:
    report = evaluate(render(), selection(), master)

    assert report.overflow is False
    assert report.warnings == []
    assert report.pages == 1


def test_more_than_one_page_is_overflow(master: dict[str, Any]) -> None:
    report = evaluate(render(pages=2), selection(), master)

    assert report.overflow is True


def test_a_shrunk_font_is_a_warning(master: dict[str, Any]) -> None:
    report = evaluate(render(font_scale=0.94), selection(), master)

    assert report.overflow is False
    assert [(warning.code, warning.font_scale) for warning in report.warnings] == [
        ("font_scaled", 0.94)
    ]


def test_trimmed_bullets_are_named(master: dict[str, Any]) -> None:
    wide = _with_bullets(master, 5)
    picked = selection(experience={"role1": ["b1", "b2", "b3", "b4", "b5"]})

    report = evaluate(render(bullet_cap=3), picked, wide)

    trimmed = [warning for warning in report.warnings if warning.code == "bullets_trimmed"]
    assert trimmed[0].removed_bullet_ids == ("b4", "b5")


def test_an_omitted_role_is_trimmed_in_master_order(master: dict[str, Any]) -> None:
    wide = _with_bullets(master, 5)
    picked = selection(experience={})

    report = evaluate(render(bullet_cap=3), picked, wide)

    trimmed = [warning for warning in report.warnings if warning.code == "bullets_trimmed"]
    assert trimmed[0].removed_bullet_ids == ("b4", "b5")


def test_section_counts_reflect_the_selection(master: dict[str, Any]) -> None:
    report = evaluate(render(), selection(), master)

    assert report.section_counts == {
        "summaries": 1,
        "experience_bullets": 2,
        "research_bullets": 0,
        "projects": 1,
        "skills": 1,
    }


def _with_bullets(master: dict[str, Any], count: int) -> dict[str, Any]:
    role = master["experience"][0]["roles"][0]
    role["bullets"] = [
        {"id": f"b{index}", "en": f"Bullet {index}.", "pt": f"Item {index}."}
        for index in range(1, count + 1)
    ]
    return master
