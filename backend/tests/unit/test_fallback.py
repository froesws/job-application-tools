"""The fallback builds a valid selection from scores, or fails loudly."""

from __future__ import annotations

from typing import Any

import pytest
from cvtailor.core.errors import FALLBACK_EXHAUSTED, TailorError
from cvtailor.core.fallback import fallback_selection
from cvtailor.core.validation import validate_selection

DIGEST: dict[str, Any] = {
    "enterprise_name": "Acme",
    "date": "2026-11-14",
    "job_title": "Backend Engineer",
    "level": "mid_level",
    "resume": "Python and PostgreSQL services.",
    "hard_skills": ["Python"],
    "soft_skills": [],
}


def test_the_result_passes_the_validator(master: dict[str, Any]) -> None:
    selection = fallback_selection(master, DIGEST, "en-US")

    assert validate_selection(master, selection) == []


def test_the_lead_block_comes_first(master: dict[str, Any]) -> None:
    master["summary_blocks"][1]["en"] = "Python and PostgreSQL every day."

    selection = fallback_selection(master, DIGEST, "en-US")

    assert selection.summary_ids[0] == "s1"


def test_the_same_inputs_give_the_same_selection(master: dict[str, Any]) -> None:
    first = fallback_selection(master, DIGEST, "en-US")
    second = fallback_selection(master, DIGEST, "en-US")

    assert first == second


def test_it_picks_at_least_one_bullet_per_role(master: dict[str, Any]) -> None:
    selection = fallback_selection(master, DIGEST, "en-US")

    assert selection.experience["role1"]


def test_a_master_without_a_lead_block_exhausts_the_fallback(master: dict[str, Any]) -> None:
    for block in master["summary_blocks"]:
        block.pop("lead", None)

    with pytest.raises(TailorError) as caught:
        fallback_selection(master, DIGEST, "en-US")

    assert caught.value.code == FALLBACK_EXHAUSTED
