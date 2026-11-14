"""Pre-ranking: the deterministic half of the selection.

Every item is scored by how much of the posting it mentions. The result is visible in the
analysis artifact and is what the fallback uses when every model fails. No model runs in
this module.
"""

from __future__ import annotations

from typing import Any

from cvtailor.core.aliases import canonical
from cvtailor.core.keywords import score, tokens


def pre_rank(master: dict[str, Any], digest: dict[str, Any]) -> dict[str, dict[str, float]]:
    posting = _posting_tokens(digest)
    return {
        "roles": {
            role["id"]: max(score(posting, role.get("en", "")), score(posting, role.get("pt", "")))
            for role in master["role_options"]
        },
        "summaries": {
            block["id"]: max(score(posting, block.get("en", "")), score(posting, block.get("pt", "")))
            for block in master["summary_blocks"]
        },
        "bullets": _bullet_scores(master, posting),
        "skills": _skill_scores(master, posting),
        "projects": {
            project["id"]: max(score(posting, project.get("en", "")), score(posting, project.get("pt", "")))
            for project in master["projects"]
        },
        "research": {
            research["id"]: max(
                score(posting, research.get("header_en", "")),
                score(posting, research.get("header_pt", "")),
            )
            for research in master["research"]
        },
    }


def _posting_tokens(digest: dict[str, Any]) -> set[str]:
    text = " ".join(
        [
            str(digest.get("job_title", "")),
            str(digest.get("resume", "")),
            " ".join(digest.get("hard_skills", []) or []),
            " ".join(digest.get("soft_skills", []) or []),
        ]
    )
    return tokens(text)


def _bullet_scores(master: dict[str, Any], posting: set[str]) -> dict[str, float]:
    return {
        bullet["id"]: score(posting, bullet.get("en", "") + " " + bullet.get("pt", ""))
        for entry in master["experience"]
        for role in entry["roles"]
        for bullet in role["bullets"]
    }


def _skill_scores(master: dict[str, Any], posting: set[str]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for group in master["skills"]:
        for item in list(group["core"]) + list(group["extra"]):
            text = item if isinstance(item, str) else " ".join(item.values())
            name = canonical(item if isinstance(item, str) else item["en"])
            scores[name] = max(scores.get(name, 0.0), score(posting, text))
    return scores
