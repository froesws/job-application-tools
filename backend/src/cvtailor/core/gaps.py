"""Pre-ranking: the deterministic half of the selection.

Every item is scored by how much of the posting it mentions. The result is visible in the
analysis artifact and is what the fallback uses when every model fails. No model runs in
this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cvtailor.core.aliases import canonical
from cvtailor.core.keywords import score, tokens
from cvtailor.core.layout import LayoutReport
from cvtailor.core.selection import Selection


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


@dataclass(frozen=True)
class GapReport:
    gaps: list[dict[str, str]]
    coverage: float
    red_flags: list[dict[str, str]]
    section_counts: dict[str, int]
    checklist: list[str]


CHECKLIST = [
    "Confirm the enterprise name and job title.",
    "Check the page count and any layout warning.",
    "Read the gaps before applying.",
    "Confirm no client or product name appears in the CV.",
]


def build_gap_report(
    master: dict[str, Any],
    digest: dict[str, Any],
    selection: Selection,
    layout: LayoutReport,
    *,
    models_admitted: bool,
) -> GapReport:
    covered = _covered_skills(master, selection, digest)
    skills = digest.get("hard_skills", [])
    gaps = [
        {"skill": skill, "severity": "must_have"}
        for skill in skills
        if canonical(skill) not in covered
    ]
    coverage = 1.0 if not skills else (len(skills) - len(gaps)) / len(skills)
    flags: list[dict[str, str]] = []
    if gaps:
        flags.append({"code": "uncovered_must_have", "message": "Some hard skills are not in the CV."})
    if any(warning.code == "bullets_trimmed" for warning in layout.warnings):
        flags.append({"code": "auto_fit_trimmed", "message": "The layout dropped bullets to fit."})
    if not models_admitted:
        flags.append({"code": "model_unadmitted", "message": "The model was never evaluated."})
    return GapReport(
        gaps=gaps,
        coverage=coverage,
        red_flags=flags,
        section_counts=layout.section_counts,
        checklist=list(CHECKLIST),
    )


def _covered_skills(
    master: dict[str, Any], selection: Selection, digest: dict[str, Any]
) -> set[str]:
    texts: list[str] = []
    blocks = {block["id"]: block for block in master["summary_blocks"]}
    texts.extend(blocks[block_id]["en"] for block_id in selection.summary_ids if block_id in blocks)
    for entry in master["experience"]:
        for role in entry["roles"]:
            order = selection.experience.get(role["id"]) or [bullet["id"] for bullet in role["bullets"]]
            by_id = {bullet["id"]: bullet for bullet in role["bullets"]}
            texts.extend(by_id[bullet_id]["en"] for bullet_id in order if bullet_id in by_id)
    projects = {project["id"]: project for project in master["projects"]}
    texts.extend(projects[project_id]["en"] for project_id in selection.project_ids if project_id in projects)
    for group in master["skills"]:
        for item in list(group["core"]) + list(group["extra"]):
            texts.append(item if isinstance(item, str) else item["en"])
    covered = {canonical(token) for text in texts for token in tokens(text)}
    return covered
