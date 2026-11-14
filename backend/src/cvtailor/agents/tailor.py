"""The tailor step: candidates in, a validated selection out.

The model may only return ids. This module checks the shape, then hands the answer to the
domain validator, which owns the real rules. Anything the model returns that is not an id
list is rejected before it can influence a render.
"""

from __future__ import annotations

from typing import Any

from cvtailor.agents.prompts import tailor_prompt
from cvtailor.core.selection import OutputLanguage, Selection
from cvtailor.core.validation import validate_selection
from cvtailor.llm.client import LLMClient, complete_validated


def selection_problems(
    payload: dict[str, Any], master: dict[str, Any], language: OutputLanguage
) -> list[str]:
    shape = _shape_problems(payload)
    if shape:
        return shape
    problems = validate_selection(master, parsed_selection(payload, language))
    return [problem.message for problem in problems]


def parsed_selection(payload: dict[str, Any], language: OutputLanguage) -> Selection:
    return Selection(
        language=language,
        role_id=payload.get("role_id", ""),
        summary_ids=_strings(payload.get("summary_ids")),
        skill_priority=_strings(payload.get("skill_priority")),
        experience=_id_lists(payload.get("experience")),
        research_ids=payload.get("research_ids"),
        research=_id_lists(payload.get("research")),
        project_ids=_strings(payload.get("project_ids")),
    )


def run_tailor(
    client: LLMClient,
    *,
    model_id: str,
    master: dict[str, Any],
    digest: dict[str, Any],
    candidates: dict[str, Any],
    language: OutputLanguage,
    attempts: int,
) -> tuple[Selection, int]:
    payload, retries = complete_validated(
        client,
        tailor_prompt(digest, candidates),
        model_id=model_id,
        attempts=attempts,
        validate=lambda answer: selection_problems(answer, master, language),
    )
    return parsed_selection(payload, language), retries


def _shape_problems(payload: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if not isinstance(payload.get("role_id"), str):
        problems.append("role_id must be a string")
    if not isinstance(payload.get("summary_ids"), list):
        problems.append("summary_ids must be a list")
    for field in ("skill_priority", "project_ids", "research_ids"):
        if field in payload and not isinstance(payload[field], list):
            problems.append(f"{field} must be a list")
    for field in ("experience", "research"):
        if field in payload and not isinstance(payload[field], dict):
            problems.append(f"{field} must be an object of id lists")
    return problems


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _id_lists(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {}
    return {str(key): _strings(items) for key, items in value.items()}
