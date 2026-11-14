"""The tailor step asks for ids, then the domain validator decides."""

from __future__ import annotations

from typing import Any

from cvtailor.agents.tailor import selection_problems
from cvtailor.core.selection import Selection

CATALOG: dict[str, Any] = {
    "roles": ["sweng"],
    "summaries": [{"id": "s1", "lead": True}],
    "bullets": {"role1": ["b1", "b2"]},
    "skills": ["Python"],
    "projects": ["p1"],
    "research": [],
}


def test_a_valid_answer_has_no_problems(master: dict[str, Any]) -> None:
    payload = {
        "role_id": "sweng",
        "summary_ids": ["s1"],
        "experience": {"role1": ["b1"]},
        "project_ids": ["p1"],
    }

    assert selection_problems(payload, master, "en-US") == []


def test_an_unknown_id_is_reported(master: dict[str, Any]) -> None:
    payload = {
        "role_id": "sweng",
        "summary_ids": ["s1"],
        "experience": {"role1": ["ghost"]},
    }

    problems = selection_problems(payload, master, "en-US")

    assert problems == ["experience/role1: bullet id not in master: ghost"]


def test_malformed_json_shape_is_reported(master: dict[str, Any]) -> None:
    assert selection_problems({"role_id": 3}, master, "en-US") == [
        "role_id must be a string",
        "summary_ids must be a list",
    ]


def test_the_result_is_a_selection_in_the_run_language(master: dict[str, Any]) -> None:
    from cvtailor.agents.tailor import parsed_selection

    selection = parsed_selection(
        {"role_id": "sweng", "summary_ids": ["s1"], "experience": {"role1": ["b1"]}},
        "pt-BR",
    )

    assert isinstance(selection, Selection)
    assert selection.language == "pt-BR"
