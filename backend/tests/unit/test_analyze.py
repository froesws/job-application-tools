"""The analyze step asks once, validates the shape, and retries with the errors."""

from __future__ import annotations

import json

from cvtailor.agents.analyze import digest_problems, run_analyze
from cvtailor.llm.fake import FakeClient

VALID = {
    "enterprise_name": "Acme",
    "date": "2026-11-14",
    "job_title": "Backend Engineer",
    "level": "mid_level",
    "resume": "Builds services.",
    "hard_skills": ["Python"],
    "soft_skills": ["Ownership"],
}


def test_a_valid_digest_has_no_problems() -> None:
    assert digest_problems(VALID) == []


def test_a_missing_field_is_reported() -> None:
    broken = {key: value for key, value in VALID.items() if key != "job_title"}

    assert digest_problems(broken) == ["missing field: job_title"]


def test_an_unknown_level_is_reported() -> None:
    assert digest_problems({**VALID, "level": "pleno"}) == [
        "level must be trainee, junior, mid_level, or senior"
    ]


def test_an_empty_required_text_is_reported() -> None:
    assert digest_problems({**VALID, "resume": "  "}) == ["resume must not be empty"]


def test_run_analyze_returns_the_parsed_digest() -> None:
    client = FakeClient([json.dumps(VALID)])

    payload, retries = run_analyze(client, model_id="fake", posting="a posting", attempts=2)

    assert payload == VALID
    assert retries == 0
    assert "a posting" in client.calls[0]["prompt"]


def test_run_analyze_retries_with_the_problems_in_the_prompt() -> None:
    broken = {**VALID, "level": "pleno"}
    client = FakeClient([json.dumps(broken), json.dumps(VALID)])

    payload, retries = run_analyze(client, model_id="fake", posting="a posting", attempts=2)

    assert payload["level"] == "mid_level"
    assert retries == 1
    assert "level must be" in client.calls[1]["prompt"]
