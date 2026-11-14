"""Validation reports what is wrong in the user's words, and never renders."""

from __future__ import annotations

import copy
from typing import Any

from cvtailor.core.errors import INVALID_SELECTION, Problem
from cvtailor.core.selection import Selection
from cvtailor.core.validation import validate_selection


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


def test_a_valid_selection_has_no_problems(master: dict[str, Any]) -> None:
    assert validate_selection(master, selection()) == []


def test_unknown_role_is_reported(master: dict[str, Any]) -> None:
    problems = validate_selection(master, selection(role_id="missing"))

    assert problems == [
        Problem(
            code=INVALID_SELECTION,
            message="role_id unknown: missing",
            item_id="missing",
        )
    ]


def test_unknown_summary_is_reported(master: dict[str, Any]) -> None:
    problems = validate_selection(master, selection(summary_ids=["missing"]))

    assert [problem.item_id for problem in problems] == ["missing"]
    assert "summary id unknown" in problems[0].message


def test_the_first_summary_must_be_a_lead_block(master: dict[str, Any]) -> None:
    problems = validate_selection(master, selection(summary_ids=["s2"]))

    assert any("lead" in problem.message for problem in problems)


def test_duplicate_bullets_are_reported(master: dict[str, Any]) -> None:
    problems = validate_selection(master, selection(experience={"role1": ["b1", "b1"]}))

    assert any("duplicate bullet ids" in problem.message for problem in problems)


def test_out_of_range_bullet_count_is_reported(master: dict[str, Any]) -> None:
    wide = copy.deepcopy(master)
    bullets = wide["experience"][0]["roles"][0]["bullets"]
    for index in range(3, 10):
        bullets.append({"id": f"b{index}", "en": f"Bullet {index}.", "pt": f"Item {index}."})
    ids = [bullet["id"] for bullet in bullets]

    problems = validate_selection(master=wide, selection=selection(experience={"role1": ids}))

    assert any("needs 1 to 7 bullets" in problem.message for problem in problems)


def test_unknown_bullet_is_reported(master: dict[str, Any]) -> None:
    problems = validate_selection(master, selection(experience={"role1": ["b1", "zzz"]}))

    assert any(problem.item_id == "zzz" for problem in problems)


def test_unknown_skill_is_reported(master: dict[str, Any]) -> None:
    problems = validate_selection(master, selection(skill_priority=["COBOL"]))

    assert any(problem.item_id == "COBOL" for problem in problems)


def test_unknown_project_is_reported(master: dict[str, Any]) -> None:
    problems = validate_selection(master, selection(project_ids=["nope"]))

    assert any(problem.item_id == "nope" for problem in problems)
