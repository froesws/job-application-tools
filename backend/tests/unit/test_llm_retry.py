"""Transient failures retry with backoff; everything else surfaces immediately."""

from __future__ import annotations

import pytest
from cvtailor.llm.client import LLMError, TransientLLMError
from cvtailor.llm.retry import RetryingClient


class Flaky:
    def __init__(self, failures: int, error: type[Exception] = TransientLLMError) -> None:
        self.failures = failures
        self.error = error
        self.calls = 0

    def complete(self, prompt: str, *, model: str) -> str:
        self.calls += 1
        if self.failures:
            self.failures -= 1
            raise self.error("boom")
        return "ok"


def test_a_transient_failure_is_retried() -> None:
    inner = Flaky(failures=2)

    assert RetryingClient(inner, attempts=3, backoff_s=0).complete("p", model="m") == "ok"
    assert inner.calls == 3


def test_exhausting_the_attempts_raises_the_transient_error() -> None:
    inner = Flaky(failures=5)

    with pytest.raises(TransientLLMError):
        RetryingClient(inner, attempts=2, backoff_s=0).complete("p", model="m")

    assert inner.calls == 2


def test_a_permanent_failure_is_not_retried() -> None:
    inner = Flaky(failures=1, error=LLMError)

    with pytest.raises(LLMError):
        RetryingClient(inner, attempts=3, backoff_s=0).complete("p", model="m")

    assert inner.calls == 1


def test_a_spent_budget_stops_before_the_next_attempt() -> None:
    inner = Flaky(failures=5)

    with pytest.raises(TransientLLMError):
        RetryingClient(inner, attempts=5, backoff_s=1, budget_s=0).complete("p", model="m")

    assert inner.calls == 1
