"""Per-step chains and limits, read from the environment.

A chain entry is ``provider:model``. Model ids are configuration, so switching providers
never touches code. The fake provider overrides both chains, which is how tests and demos
run without a key.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ChainEntry:
    provider: str
    model: str


@dataclass(frozen=True)
class LLMConfig:
    analyze: list[ChainEntry] = field(default_factory=list)
    tailor: list[ChainEntry] = field(default_factory=list)
    call_timeout_s: int = 60
    run_budget_s: int = 300
    validation_retries: int = 2
    vote_runs: int = 1
    prompt_logging: bool = False


FAKE = [ChainEntry(provider="fake", model="scripted")]


def parse_chain(value: str) -> list[ChainEntry]:
    entries: list[ChainEntry] = []
    for raw in value.split(","):
        item = raw.strip()
        if not item:
            continue
        provider, _, model = item.partition(":")
        if not provider or not model:
            raise ValueError(f"Chain entry must be provider:model, got {item!r}")
        entries.append(ChainEntry(provider=provider, model=model))
    return entries


def load(env: Mapping[str, str] | None = None) -> LLMConfig:
    source = os.environ if env is None else env
    if source.get("LLM_PROVIDER") == "fake":
        analyze = list(FAKE)
        tailor = list(FAKE)
    else:
        analyze = parse_chain(source.get("ANALYZE_CHAIN", ""))
        tailor = parse_chain(source.get("TAILOR_CHAIN", ""))
    return LLMConfig(
        analyze=analyze,
        tailor=tailor,
        call_timeout_s=int(source.get("CALL_TIMEOUT_S", "60")),
        run_budget_s=int(source.get("RUN_BUDGET_S", "300")),
        validation_retries=int(source.get("VALIDATION_RETRIES", "2")),
        vote_runs=int(source.get("VOTE_RUNS", "1")),
        prompt_logging=source.get("PROMPT_LOGGING", "false").lower() == "true",
    )
