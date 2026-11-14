"""The digest is normalized before it can influence anything."""

from __future__ import annotations

from typing import Any

from cvtailor.core.digest import normalize_digest

POSTING = "Backend Engineer. Python, PostgreSQL and Kubernetes. Nice to have Rust."


def payload(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "enterprise_name": "  Acme  ",
        "date": "2026-11-14",
        "job_title": "Backend   Engineer",
        "level": "mid_level",
        "resume": "Builds services.",
        "hard_skills": ["Python", "PostgreSQL"],
        "soft_skills": ["Ownership"],
    }
    base.update(overrides)
    return base


def test_text_is_trimmed_and_whitespace_collapsed() -> None:
    digest = normalize_digest(payload(), POSTING)

    assert digest["enterprise_name"] == "Acme"
    assert digest["job_title"] == "Backend Engineer"


def test_level_aliases_collapse() -> None:
    assert normalize_digest(payload(level="pleno"), POSTING)["level"] == "mid_level"
    assert normalize_digest(payload(level="Mid-Level"), POSTING)["level"] == "mid_level"


def test_empty_and_duplicate_skills_are_removed() -> None:
    digest = normalize_digest(
        payload(hard_skills=["Python", " python ", "", "PostgreSQL"]), POSTING
    )

    assert digest["hard_skills"] == ["Python", "PostgreSQL"]


def test_an_unsupported_skill_is_dropped() -> None:
    digest = normalize_digest(payload(hard_skills=["Python", "COBOL"]), POSTING)

    assert digest["hard_skills"] == ["Python"]


def test_a_documented_alias_counts_as_support() -> None:
    posting = "We use postgres and k8s."

    digest = normalize_digest(payload(hard_skills=["PostgreSQL", "Kubernetes"]), posting)

    assert digest["hard_skills"] == ["PostgreSQL", "Kubernetes"]


def test_unknown_fields_are_discarded() -> None:
    digest = normalize_digest({**payload(), "salary": "100k"}, POSTING)

    assert set(digest) == {
        "enterprise_name",
        "date",
        "job_title",
        "level",
        "resume",
        "hard_skills",
        "soft_skills",
    }
