"""Reads the renderer's result and turns it into reviewable layout facts.

The renderer keeps its contract: it returns the page count, the scale it settled on, and
the bullet cap it applied. Nothing here renders or re-parses a PDF.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from cvtailor.core.selection import Selection


@dataclass(frozen=True)
class LayoutWarning:
    code: str
    detail: str
    removed_bullet_ids: tuple[str, ...] = ()
    font_scale: float | None = None


@dataclass(frozen=True)
class LayoutReport:
    pages: int
    overflow: bool
    warnings: list[LayoutWarning] = field(default_factory=list)
    section_counts: dict[str, int] = field(default_factory=dict)


def evaluate(
    render_result: dict[str, Any], selection: Selection, master: dict[str, Any]
) -> LayoutReport:
    pages = int(render_result["pages"])
    scale = float(render_result["font_scale"])
    cap = render_result.get("bullet_cap")
    warnings: list[LayoutWarning] = []
    if scale < 1.0:
        warnings.append(
            LayoutWarning(
                code="font_scaled",
                detail=f"The layout was scaled to {scale:.2f} to fit one page.",
                font_scale=scale,
            )
        )
    removed = _removed_ids(selection, master, cap)
    if removed:
        warnings.append(
            LayoutWarning(
                code="bullets_trimmed",
                detail=f"{len(removed)} bullet(s) were dropped to fit one page.",
                removed_bullet_ids=tuple(removed),
            )
        )
    return LayoutReport(
        pages=pages,
        overflow=pages > 1,
        warnings=warnings,
        section_counts=_section_counts(selection, master),
    )


def _removed_ids(
    selection: Selection, master: dict[str, Any], cap: int | None
) -> list[str]:
    if cap is None:
        return []
    removed: list[str] = []
    removed.extend(_trimmed(selection.experience, _role_orders(master), cap))
    removed.extend(_trimmed(selection.research, _research_orders(master), cap))
    return removed


def _role_orders(master: dict[str, Any]) -> dict[str, list[str]]:
    return {
        role["id"]: [bullet["id"] for bullet in role["bullets"]]
        for entry in master["experience"]
        for role in entry["roles"]
    }


def _research_orders(master: dict[str, Any]) -> dict[str, list[str]]:
    return {
        research["id"]: [bullet["id"] for bullet in research["bullets"]]
        for research in master["research"]
    }


def _trimmed(
    chosen: dict[str, list[str]], master_orders: dict[str, list[str]], cap: int
) -> list[str]:
    removed: list[str] = []
    for item_id, master_order in master_orders.items():
        order = chosen.get(item_id) or master_order
        removed.extend(order[cap:])
    return removed


def _section_counts(selection: Selection, master: dict[str, Any]) -> dict[str, int]:
    role_orders = _role_orders(master)
    research_orders = _research_orders(master)
    return {
        "summaries": len(selection.summary_ids),
        "experience_bullets": _selected_count(selection.experience, role_orders),
        "research_bullets": _selected_count(selection.research, research_orders),
        "projects": len(selection.project_ids),
        "skills": len(master["skills"]),
    }


def _selected_count(
    chosen: dict[str, list[str]], master_orders: dict[str, list[str]]
) -> int:
    return sum(
        len(chosen.get(item_id) or master_order)
        for item_id, master_order in master_orders.items()
    )
