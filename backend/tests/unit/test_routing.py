"""A model label routes to the provider client, which sees only the model id."""

from __future__ import annotations

import pytest
from cvtailor.llm.client import LLMError
from cvtailor.llm.routing import RoutedClient


class Recorder:
    def __init__(self) -> None:
        self.seen: list[str] = []

    def complete(self, prompt: str, *, model: str) -> str:
        self.seen.append(model)
        return f"{model}:ok"


def test_the_prefix_selects_the_client_and_is_not_forwarded() -> None:
    openai = Recorder()
    gemini = Recorder()
    client = RoutedClient({"openai": openai, "gemini": gemini})

    assert client.complete("p", model="gemini:flash-2") == "flash-2:ok"
    assert gemini.seen == ["flash-2"]
    assert openai.seen == []


def test_an_unknown_provider_is_a_typed_failure() -> None:
    client = RoutedClient({"openai": Recorder()})

    with pytest.raises(LLMError):
        client.complete("p", model="nope:model")
