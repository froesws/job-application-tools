"""The model boundary: one interface, JSON extraction, and bounded validation retries.

The interface stays dependency-free. Providers implement ``complete``; everything above
this module speaks in validated objects.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, Protocol


class LLMError(Exception):
    """Anything the model layer refuses to pass upward."""


class InvalidOutput(LLMError):
    """The answer could not be parsed or failed validation after every attempt."""

    def __init__(self, message: str, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []


class LLMClient(Protocol):
    def complete(self, prompt: str, *, model: str) -> str:
        """Return the model's raw answer for one prompt."""


Validator = Callable[[dict[str, Any]], list[str]]


def extract_json(text: str) -> dict[str, Any]:
    """Return the first JSON object in the text, tolerating fences and prose."""
    start = text.find("{")
    while start != -1:
        try:
            payload, _ = json.JSONDecoder().raw_decode(text[start:])
        except json.JSONDecodeError:
            start = text.find("{", start + 1)
            continue
        if isinstance(payload, dict):
            return payload
        start = text.find("{", start + 1)
    raise InvalidOutput("The model did not return a JSON object")


def complete_validated(
    client: LLMClient,
    prompt: str,
    *,
    model_id: str,
    attempts: int,
    validate: Validator,
) -> tuple[dict[str, Any], int]:
    """Ask up to ``attempts`` times, feeding the validation errors into the next prompt."""
    errors: list[str] = []
    for retry in range(attempts):
        answer = client.complete(_with_feedback(prompt, errors), model=model_id)
        try:
            payload = extract_json(answer)
        except InvalidOutput as exc:
            errors = [str(exc)]
            continue
        problems = validate(payload)
        if not problems:
            return payload, retry
        errors = problems
    raise InvalidOutput("The model never produced a valid answer", errors)


def _with_feedback(prompt: str, errors: list[str]) -> str:
    if not errors:
        return prompt
    listed = "\n".join(f"- {error}" for error in errors)
    return f"{prompt}\n\nThe previous answer was rejected:\n{listed}\nFix these problems."
