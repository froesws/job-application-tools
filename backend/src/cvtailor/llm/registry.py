"""The provider registry.

Adding a provider is one entry: where it lives and which environment variable holds its
key. Model ids stay in configuration, so adding a model is zero code.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderConfig:
    base_url: str
    key_env: str


REGISTRY: dict[str, ProviderConfig] = {
    "openai": ProviderConfig("https://api.openai.com/v1", "OPENAI_API_KEY"),
    "openrouter": ProviderConfig("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
    "gemini": ProviderConfig(
        "https://generativelanguage.googleapis.com/v1beta/openai", "GEMINI_API_KEY"
    ),
    "deepseek": ProviderConfig("https://api.deepseek.com/v1", "DEEPSEEK_API_KEY"),
}


def resolve(provider: str) -> ProviderConfig:
    try:
        return REGISTRY[provider]
    except KeyError as error:
        raise ValueError(f"Unknown provider: {provider}") from error
