"""The deterministic fallback: a valid CV when every model fails.

It uses only the pre-rank scores, so it is reproducible and explainable. If the result
cannot satisfy the validator, it raises rather than rendering something invalid.
"""

from __future__ import annotations

from typing import Any

from cvtailor.core.errors import FALLBACK_EXHAUSTED, TailorError
from cvtailor.core.gaps import pre_rank
from cvtailor.core.selection import OutputLanguage, Selection
from cvtailor.core.validation import validate_selection

MAX_BULLETS = 3
MAX_SUMMARIES = 2
MAX_SKILLS = 3
MAX_PROJECTS = 3


def fallback_selection(
    master: dict[str, Any], digest: dict[str, Any], language: OutputLanguage
) -> Selection:
    scores = pre_rank(master, digest)
    selection = Selection(
        language=language,
        role_id=_best_role(master, scores["roles"]),
        summary_ids=_summaries(master, scores["summaries"]),
        experience=_experience(master, scores["bullets"]),
        skill_priority=_skills(scores["skills"]),
        project_ids=_projects(scores["projects"]),
        research_ids=[],
        research={},
    )
    if validate_selection(master, selection):
        raise TailorError(
            FALLBACK_EXHAUSTED,
            "The deterministic fallback could not satisfy the validator.",
        )
    return selection


def _best_role(master: dict[str, Any], scores: dict[str, float]) -> str:
    order = [role["id"] for role in master["role_options"]]
    return max(order, key=lambda role_id: (scores.get(role_id, 0.0), -order.index(role_id)))


def _summaries(master: dict[str, Any], scores: dict[str, float]) -> list[str]:
    blocks = master["summary_blocks"]
    lead = next((block["id"] for block in blocks if block.get("lead")), None)
    if lead is None:
        return []
    others = sorted(
        (block["id"] for block in blocks if block["id"] != lead),
        key=lambda block_id: -scores.get(block_id, 0.0),
    )
    return [lead, *[block_id for block_id in others if scores.get(block_id, 0.0) > 0]][:MAX_SUMMARIES]


def _experience(master: dict[str, Any], scores: dict[str, float]) -> dict[str, list[str]]:
    chosen: dict[str, list[str]] = {}
    for entry in master["experience"]:
        for role in entry["roles"]:
            ids = [bullet["id"] for bullet in role["bullets"]]
            ranked = sorted(ids, key=lambda bullet_id: (-scores.get(bullet_id, 0.0), ids.index(bullet_id)))
            chosen[role["id"]] = ranked[:MAX_BULLETS] or ids[:1]
    return chosen


def _skills(scores: dict[str, float]) -> list[str]:
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return [name for name, value in ranked if value > 0][:MAX_SKILLS]


def _projects(scores: dict[str, float]) -> list[str]:
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return [project_id for project_id, value in ranked if value > 0][:MAX_PROJECTS]
