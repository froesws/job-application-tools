"""Digest normalization: one shape, one level vocabulary, verified skills.

It runs after the model answers and before the digest is stored. Skills the posting does
not support are dropped rather than corrected; the digest must never claim a requirement
the text does not contain.
"""

from __future__ import annotations

import re
from typing import Any

from cvtailor.core.aliases import canonical

LEVELS = ("trainee", "junior", "mid_level", "senior")
LEVEL_ALIASES: dict[str, str] = {
    "pleno": "mid_level",
    "mid level": "mid_level",
    "mid-level": "mid_level",
    "midlevel": "mid_level",
}

_FIELDS = (
    "enterprise_name",
    "date",
    "job_title",
    "level",
    "resume",
    "hard_skills",
    "soft_skills",
)


def normalize_digest(payload: dict[str, Any], posting: str) -> dict[str, Any]:
    return {
        "enterprise_name": _text(payload.get("enterprise_name")),
        "date": _text(payload.get("date")),
        "job_title": _text(payload.get("job_title")),
        "level": _level(payload.get("level")),
        "resume": _text(payload.get("resume")),
        "hard_skills": _skills(payload.get("hard_skills"), posting),
        "soft_skills": _skills(payload.get("soft_skills"), posting, verify=False),
    }


def accepted_levels() -> tuple[str, ...]:
    return LEVELS + tuple(LEVEL_ALIASES)


def _text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _level(value: Any) -> str:
    text = _text(value).lower()
    return LEVEL_ALIASES.get(text, text)


def _skills(value: Any, posting: str, *, verify: bool = True) -> list[str]:
    if not isinstance(value, list):
        return []
    seen: set[str] = set()
    kept: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        display = _text(item)
        if not display:
            continue
        key = canonical(display)
        if key in seen:
            continue
        if verify and not _supported(display, posting):
            continue
        seen.add(key)
        kept.append(display)
    return kept


def _supported(skill: str, posting: str) -> bool:
    haystack = posting.lower()
    if canonical(skill) in haystack or skill.strip().lower() in haystack:
        return True
    for token in re.findall(r"[^\W_]+", haystack):
        if canonical(token) == canonical(skill):
            return True
    return False
