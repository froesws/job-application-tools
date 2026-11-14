"""The selection model shared by the API, the pipeline, and the renderer.

The API speaks ``pt-BR`` and ``en-US``; the renderer speaks ``pt`` and ``en``. The
mapping lives here so no other module has to know both vocabularies.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

OutputLanguage = Literal["pt-BR", "en-US"]
RenderLanguage = Literal["pt", "en"]

_RENDER: dict[OutputLanguage, RenderLanguage] = {"pt-BR": "pt", "en-US": "en"}
_OTHER: dict[OutputLanguage, OutputLanguage] = {"pt-BR": "en-US", "en-US": "pt-BR"}


class Selection(BaseModel):
    """The user's picks, by id only. The renderer never sees text from here."""

    language: OutputLanguage
    role_id: str
    summary_ids: list[str]
    skill_priority: list[str] = Field(default_factory=list)
    experience: dict[str, list[str]] = Field(default_factory=dict)
    research_ids: list[str] | None = None
    research: dict[str, list[str]] = Field(default_factory=dict)
    project_ids: list[str] = Field(default_factory=list)


def render_language(language: OutputLanguage) -> RenderLanguage:
    return _RENDER[language]


def other_language(language: OutputLanguage) -> OutputLanguage:
    return _OTHER[language]


def to_renderer(selection: Selection) -> dict[str, Any]:
    """Return the dict shape ``render_pdf`` expects."""
    payload: dict[str, Any] = {
        "language": render_language(selection.language),
        "role_id": selection.role_id,
        "summary_ids": list(selection.summary_ids),
        "skill_priority": list(selection.skill_priority),
        "experience": {key: list(value) for key, value in selection.experience.items()},
        "research": {key: list(value) for key, value in selection.research.items()},
        "project_ids": list(selection.project_ids),
    }
    if selection.research_ids is not None:
        payload["research_ids"] = list(selection.research_ids)
    return payload


def from_renderer(payload: dict[str, Any], language: OutputLanguage) -> Selection:
    """Build a selection from the renderer's vocabulary."""
    research_ids = payload.get("research_ids")
    return Selection(
        language=language,
        role_id=payload["role_id"],
        summary_ids=list(payload.get("summary_ids", [])),
        skill_priority=list(payload.get("skill_priority", [])),
        experience={
            key: list(value) for key, value in payload.get("experience", {}).items()
        },
        research_ids=None if research_ids is None else list(research_ids),
        research={key: list(value) for key, value in payload.get("research", {}).items()},
        project_ids=list(payload.get("project_ids", [])),
    )
