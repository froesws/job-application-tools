"""Chains and limits come from the environment, and the fake provider overrides both."""

from __future__ import annotations

import pytest
from cvtailor.llm.config import ChainEntry, load, parse_chain


def test_a_chain_is_an_ordered_list_of_provider_and_model() -> None:
    entries = parse_chain("openai:gpt-4.1-mini,gemini:gemini-2.5-flash")

    assert entries == [
        ChainEntry(provider="openai", model="gpt-4.1-mini"),
        ChainEntry(provider="gemini", model="gemini-2.5-flash"),
    ]


def test_an_entry_without_a_model_is_rejected() -> None:
    with pytest.raises(ValueError):
        parse_chain("openai")


def test_an_empty_chain_is_empty() -> None:
    assert parse_chain("") == []


def test_limits_and_logging_come_from_the_environment() -> None:
    config = load(
        {
            "ANALYZE_CHAIN": "openai:gpt",
            "TAILOR_CHAIN": "gemini:flash",
            "CALL_TIMEOUT_S": "30",
            "RUN_BUDGET_S": "120",
            "VALIDATION_RETRIES": "1",
            "VOTE_RUNS": "3",
            "PROMPT_LOGGING": "true",
        }
    )

    assert config.analyze == [ChainEntry("openai", "gpt")]
    assert config.tailor == [ChainEntry("gemini", "flash")]
    assert config.call_timeout_s == 30
    assert config.run_budget_s == 120
    assert config.validation_retries == 1
    assert config.vote_runs == 3
    assert config.prompt_logging is True


def test_defaults_match_the_constitution() -> None:
    config = load({})

    assert config.call_timeout_s == 60
    assert config.run_budget_s == 300
    assert config.validation_retries == 2
    assert config.vote_runs == 1
    assert config.prompt_logging is False
    assert config.analyze == []


def test_the_fake_provider_replaces_both_chains() -> None:
    config = load({"LLM_PROVIDER": "fake", "ANALYZE_CHAIN": "openai:gpt"})

    assert config.analyze == [ChainEntry("fake", "scripted")]
    assert config.tailor == [ChainEntry("fake", "scripted")]
