"""Dispatch a model label to the client for its provider.

Pipeline steps carry labels such as ``openai:gpt-4.1-mini``. The provider client should
see only the model id, never the prefix.
"""

from __future__ import annotations

from cvtailor.llm.client import LLMClient, LLMError


class RoutedClient:
    def __init__(self, routes: dict[str, LLMClient]) -> None:
        self._routes = routes

    def complete(self, prompt: str, *, model: str) -> str:
        provider, _, bare = model.partition(":")
        client = self._routes.get(provider)
        if client is None:
            raise LLMError(f"No client configured for provider: {provider}")
        return client.complete(prompt, model=bare or model)
