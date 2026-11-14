"""The scripted provider used by tests, demos, and CI.

It answers from a queue and records every call, so a test can assert both the result and
what the pipeline asked for. Running out of answers is a test error, not a model error.
"""

from __future__ import annotations

from typing import Any


class FakeClient:
    def __init__(self, answers: list[str | Exception] | None = None) -> None:
        self.answers: list[str | Exception] = list(answers or [])
        self.calls: list[dict[str, Any]] = []

    def complete(self, prompt: str, *, model: str) -> str:
        self.calls.append({"prompt": prompt, "model": model})
        if not self.answers:
            raise AssertionError("FakeClient ran out of scripted answers")
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer
