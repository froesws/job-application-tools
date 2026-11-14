"""The section call proposes items; code decides what is verified and what is not."""

from __future__ import annotations

from typing import Any

from cvtailor.agents.ingest import build_items, ingest_prompt, section_problems
from cvtailor.core.extraction import Block
from cvtailor.core.ingestion import UNVERIFIED

BLOCKS = [
    Block(index=0, source="cv.pdf", location="page 1", text="Led a Python migration for 3 teams."),
]


def proposal(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "kind": "bullet",
        "parent": "role1",
        "fields": {"en": "Led a Python migration for 3 teams.", "pt": "Liderou uma migracao Python para 3 times."},
        "quote": "Led a Python migration for 3 teams.",
        "source_language": "en",
    }
    base.update(overrides)
    return base


def test_the_prompt_delimits_the_cv_text() -> None:
    prompt = ingest_prompt("experience", BLOCKS, "en-US")

    assert "<<<CV>>>" in prompt
    assert "<<<END CV>>>" in prompt
    assert "ignore" in prompt.lower()


def test_the_shape_check_reports_missing_parts() -> None:
    problems = section_problems({"items": [{"kind": "bullet"}]})

    assert "item 0 needs a quote" in problems
    assert "item 0 needs en and pt fields" in problems
    assert "item 0 needs source_language en or pt" in problems


def test_a_verified_quote_becomes_pending_with_both_variants() -> None:
    item = build_items("experience", [proposal()], BLOCKS)[0]

    assert item.status == "pending"
    assert item.verification["verified"] is True
    assert item.fields["pt"].startswith("Liderou")
    assert item.translated_variant == "pt"
    assert item.source_text == item.fields["en"]


def test_an_invented_quote_is_unverified() -> None:
    item = build_items("experience", [proposal(quote="Invented claim.")], BLOCKS)[0]

    assert item.status == UNVERIFIED
    assert item.verification["reason"] == "not_found"


def test_a_changed_number_is_a_warning() -> None:
    item = build_items(
        "experience",
        [proposal(fields={"en": "Led 3 teams.", "pt": "Liderou 5 times."}, quote="Led 3 teams.")],
        [Block(index=0, source="cv.pdf", location="page 1", text="Led 3 teams.")],
    )[0]

    assert "number_changed" in item.warnings
