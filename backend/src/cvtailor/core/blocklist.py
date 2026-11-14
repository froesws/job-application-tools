"""The per-profile blocklist.

A hit names the item id, never the matched term, so the error message cannot leak the
name the user was hiding.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cvtailor.core.selection import Selection, render_language


def load(path: Path) -> list[str]:
    """Read one term per line; comments and blank lines are ignored."""
    if not path.is_file():
        return []
    terms: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        terms.append(stripped)
    return terms


def check(terms: list[str], master: dict[str, Any], selection: Selection) -> list[str]:
    """Return the ids of selected items whose rendered text contains a term."""
    if not terms:
        return []
    language = render_language(selection.language)
    lowered = [term.lower() for term in terms]
    hits: list[str] = []
    for item_id, text in _rendered_items(master, selection, language):
        if any(term in text.lower() for term in lowered):
            hits.append(item_id)
    return hits


def _rendered_items(
    master: dict[str, Any], selection: Selection, language: str
) -> list[tuple[str, str]]:
    """Every text the CV would print, paired with the id that identifies it."""
    items: list[tuple[str, str]] = []
    items.extend(_role_items(master, selection, language))
    items.extend(_summary_items(master, selection, language))
    items.extend(_experience_items(master, selection, language))
    items.extend(_research_items(master, selection, language))
    items.extend(_project_items(master, selection, language))
    items.extend(_skill_items(master, language))
    items.extend(
        _positional("education", [(entry.get(f"header_{language}", ""), entry.get(f"desc_{language}", "")) for entry in master["education"]])
    )
    items.append(("certs", master["certs"][language]))
    return items


def _role_items(
    master: dict[str, Any], selection: Selection, language: str
) -> list[tuple[str, str]]:
    role = next(
        option for option in master["role_options"] if option["id"] == selection.role_id
    )
    return [(selection.role_id, role[language])]


def _summary_items(
    master: dict[str, Any], selection: Selection, language: str
) -> list[tuple[str, str]]:
    blocks = {block["id"]: block for block in master["summary_blocks"]}
    return [(block_id, blocks[block_id][language]) for block_id in selection.summary_ids]


def _experience_items(
    master: dict[str, Any], selection: Selection, language: str
) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for entry in master["experience"]:
        for role in entry["roles"]:
            bullets = {bullet["id"]: bullet for bullet in role["bullets"]}
            order = selection.experience.get(role["id"]) or list(bullets)
            items.extend((bullet_id, bullets[bullet_id][language]) for bullet_id in order)
    return items


def _research_items(
    master: dict[str, Any], selection: Selection, language: str
) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for research in master["research"]:
        if selection.research_ids is not None and research["id"] not in selection.research_ids:
            continue
        bullets = {bullet["id"]: bullet for bullet in research["bullets"]}
        order = selection.research.get(research["id"]) or list(bullets)
        items.extend((bullet_id, bullets[bullet_id][language]) for bullet_id in order)
    return items


def _project_items(
    master: dict[str, Any], selection: Selection, language: str
) -> list[tuple[str, str]]:
    projects = {project["id"]: project for project in master["projects"]}
    return [(project_id, projects[project_id][language]) for project_id in selection.project_ids]


def _skill_items(master: dict[str, Any], language: str) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for index, group in enumerate(master["skills"]):
        texts = [
            _text(item, language)
            for item in list(group["core"]) + list(group["extra"])
        ]
        texts.append(group[f"label_{language}"])
        items.append((f"skills[{index}]", " ".join(texts)))
    return items


def _positional(prefix: str, texts: list[tuple[str, ...]]) -> list[tuple[str, str]]:
    return [
        (f"{prefix}[{index}]", " ".join(part for part in parts if part))
        for index, parts in enumerate(texts)
    ]


def _text(item: str | dict[str, str], language: str) -> str:
    return item if isinstance(item, str) else item[language]
