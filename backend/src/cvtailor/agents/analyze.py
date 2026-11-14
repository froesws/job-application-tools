"""The analyze step: posting in, a shape-valid digest out.

Normalization and skill verification belong to the domain core; this step only asks the
model and refuses an answer that does not have the contract's fields.
"""

from __future__ import annotations

from typing import Any

from cvtailor.agents.prompts import DIGEST_FIELDS, analyze_prompt
from cvtailor.llm.client import LLMClient, complete_validated

LEVELS = ("trainee", "junior", "mid_level", "senior")
_TEXT_FIELDS = ("enterprise_name", "date", "job_title", "resume")
_LIST_FIELDS = ("hard_skills", "soft_skills")


def digest_problems(payload: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    for field in DIGEST_FIELDS:
        if field not in payload:
            problems.append(f"missing field: {field}")
    for field in _TEXT_FIELDS:
        value = payload.get(field)
        if isinstance(value, str) and not value.strip():
            problems.append(f"{field} must not be empty")
    for field in _LIST_FIELDS:
        value = payload.get(field)
        if field in payload and not isinstance(value, list):
            problems.append(f"{field} must be a list")
    level = payload.get("level")
    if level is not None and level not in LEVELS:
        problems.append(f"level must be {', '.join(LEVELS[:-1])}, or {LEVELS[-1]}")
    return problems


def run_analyze(
    client: LLMClient, *, model_id: str, posting: str, attempts: int
) -> tuple[dict[str, Any], int]:
    return complete_validated(
        client,
        analyze_prompt(posting),
        model_id=model_id,
        attempts=attempts,
        validate=digest_problems,
    )
