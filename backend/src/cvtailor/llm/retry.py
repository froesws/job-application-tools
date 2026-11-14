"""Transient retries with exponential backoff, bounded by a run budget."""

from __future__ import annotations

import time
from collections.abc import Callable

from cvtailor.llm.client import LLMClient, TransientLLMError


class RetryingClient:
    def __init__(
        self,
        inner: LLMClient,
        *,
        attempts: int = 3,
        backoff_s: float = 0.5,
        budget_s: float | None = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._inner = inner
        self._attempts = max(1, attempts)
        self._backoff_s = backoff_s
        self._budget_s = budget_s
        self._sleep = sleep
        self._clock = clock

    def complete(self, prompt: str, *, model: str) -> str:
        started = self._clock()
        for attempt in range(self._attempts):
            try:
                return self._inner.complete(prompt, model=model)
            except TransientLLMError:
                delay = self._backoff_s * (2**attempt)
                spent = self._clock() - started
                out_of_attempts = attempt + 1 >= self._attempts
                out_of_budget = self._budget_s is not None and spent + delay > self._budget_s
                if out_of_attempts or out_of_budget:
                    raise
                if delay:
                    self._sleep(delay)
        raise TransientLLMError("Retry loop ended without an answer")
