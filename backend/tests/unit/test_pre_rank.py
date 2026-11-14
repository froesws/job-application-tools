"""Pre-ranking scores every master item against the digest, without a model."""

from __future__ import annotations

from typing import Any

from cvtailor.core.gaps import pre_rank

DIGEST: dict[str, Any] = {
    "enterprise_name": "Acme",
    "date": "2026-11-14",
    "job_title": "Backend Engineer",
    "level": "mid_level",
    "resume": "Python and PostgreSQL services.",
    "hard_skills": ["Python"],
    "soft_skills": [],
}


def test_scores_cover_every_section(master: dict[str, Any]) -> None:
    scores = pre_rank(master, DIGEST)

    assert set(scores) == {"roles", "summaries", "bullets", "skills", "projects", "research"}
    assert set(scores["roles"]) == {"sweng"}
    assert set(scores["bullets"]) == {"b1", "b2"}


def test_a_bullet_that_mentions_the_skill_outranks_one_that_does_not(
    master: dict[str, Any],
) -> None:
    master["experience"][0]["roles"][0]["bullets"][0]["en"] = "Built a Python service."

    scores = pre_rank(master, DIGEST)

    assert scores["bullets"]["b1"] > scores["bullets"]["b2"]


def test_the_same_inputs_give_the_same_scores(master: dict[str, Any]) -> None:
    assert pre_rank(master, DIGEST) == pre_rank(master, DIGEST)


def test_an_unrelated_digest_scores_zero_everywhere(master: dict[str, Any]) -> None:
    scores = pre_rank(
        master,
        {**DIGEST, "job_title": "Chef", "resume": "", "hard_skills": [], "soft_skills": []},
    )

    assert all(value == 0 for value in scores["bullets"].values())
