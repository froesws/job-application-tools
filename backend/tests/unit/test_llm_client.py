"""Extracting JSON from messy model output, and retrying with the errors fed back."""

from __future__ import annotations

import pytest
from cvtailor.llm.client import InvalidOutput, complete_validated, extract_json


class Scripted:
    def __init__(self, answers: list[str]) -> None:
        self.answers = list(answers)
        self.prompts: list[str] = []

    def complete(self, prompt: str, *, model: str) -> str:
        self.prompts.append(prompt)
        return self.answers.pop(0)


def test_extract_json_reads_a_plain_object() -> None:
    assert extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_survives_a_fenced_block() -> None:
    assert extract_json('Here you go:\n```json\n{"a": 1}\n```\nDone') == {"a": 1}


def test_extract_json_survives_surrounding_prose() -> None:
    assert extract_json('Result: {"a": {"b": 2}} trailing') == {"a": {"b": 2}}


def test_extract_json_rejects_text_without_an_object() -> None:
    with pytest.raises(InvalidOutput):
        extract_json("no json here")


def test_a_valid_first_answer_needs_no_retry() -> None:
    model = Scripted(['{"ok": true}'])

    payload, retries = complete_validated(
        model, "prompt", model_id="m", attempts=2, validate=lambda _: []
    )

    assert payload == {"ok": True}
    assert retries == 0


def test_an_invalid_answer_is_retried_with_the_errors_in_the_prompt() -> None:
    model = Scripted(['{"id": "bad"}', '{"id": "good"}'])

    payload, retries = complete_validated(
        model,
        "prompt",
        model_id="m",
        attempts=2,
        validate=lambda payload: [] if payload["id"] == "good" else ["bad id"],
    )

    assert payload == {"id": "good"}
    assert retries == 1
    assert "bad id" in model.prompts[1]


def test_exhausting_the_attempts_raises_with_every_error() -> None:
    model = Scripted(['{"id": "bad"}', '{"id": "bad"}'])

    with pytest.raises(InvalidOutput) as caught:
        complete_validated(
            model,
            "prompt",
            model_id="m",
            attempts=2,
            validate=lambda _: ["still bad"],
        )

    assert caught.value.errors == ["still bad"]
