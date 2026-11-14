"""The fake provider returns what the test queued, and records what it was asked."""

from __future__ import annotations

import pytest
from cvtailor.llm.fake import FakeClient


def test_answers_come_out_in_order() -> None:
    client = FakeClient(["first", "second"])

    assert client.complete("p", model="m") == "first"
    assert client.complete("p", model="m") == "second"


def test_calls_are_recorded_for_assertions() -> None:
    client = FakeClient(["ok"])

    client.complete("prompt text", model="openai:gpt")

    assert client.calls == [{"prompt": "prompt text", "model": "openai:gpt"}]


def test_running_out_of_answers_is_a_loud_failure() -> None:
    client = FakeClient([])

    with pytest.raises(AssertionError):
        client.complete("p", model="m")


def test_a_queued_error_is_raised() -> None:
    client = FakeClient([RuntimeError("boom")])

    with pytest.raises(RuntimeError):
        client.complete("p", model="m")
