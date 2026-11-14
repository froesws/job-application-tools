"""A provider name resolves to its endpoint and the variable holding its key."""

from __future__ import annotations

import pytest
from cvtailor.llm.registry import resolve


def test_openai_resolves_to_its_endpoint_and_key_variable() -> None:
    provider = resolve("openai")

    assert provider.base_url == "https://api.openai.com/v1"
    assert provider.key_env == "OPENAI_API_KEY"


def test_every_documented_provider_is_present() -> None:
    for name in ("openai", "openrouter", "gemini", "deepseek"):
        assert resolve(name).base_url.startswith("https://")


def test_an_unknown_provider_is_refused() -> None:
    with pytest.raises(ValueError):
        resolve("nope")
