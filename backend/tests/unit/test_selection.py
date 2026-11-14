"""The selection model speaks the API's languages and the renderer's, and nothing else."""

from __future__ import annotations

import pytest
from cvtailor.core.selection import (
    Selection,
    from_renderer,
    other_language,
    render_language,
    to_renderer,
)
from pydantic import ValidationError


def test_render_language_maps_the_api_vocabulary_to_the_renderer() -> None:
    assert render_language("pt-BR") == "pt"
    assert render_language("en-US") == "en"


def test_other_language_returns_the_opposite() -> None:
    assert other_language("pt-BR") == "en-US"
    assert other_language("en-US") == "pt-BR"


def test_to_renderer_translates_every_field() -> None:
    selection = Selection(
        language="pt-BR",
        role_id="sweng",
        summary_ids=["s1"],
        skill_priority=["Python"],
        experience={"role1": ["b1"]},
        research={"r1": ["b1"]},
        project_ids=["p1"],
    )

    payload = to_renderer(selection)

    assert payload["language"] == "pt"
    assert payload["experience"] == {"role1": ["b1"]}
    assert payload["research"] == {"r1": ["b1"]}
    assert "research_ids" not in payload


def test_to_renderer_keeps_an_explicit_research_selection() -> None:
    selection = Selection(
        language="en-US",
        role_id="sweng",
        summary_ids=["s1"],
        research_ids=["r1"],
    )

    payload = to_renderer(selection)

    assert payload["research_ids"] == ["r1"]
    assert payload["language"] == "en"


def test_from_renderer_round_trips() -> None:
    selection = Selection(
        language="en-US",
        role_id="sweng",
        summary_ids=["s1"],
        skill_priority=["Python"],
        experience={"role1": ["b1", "b2"]},
        research_ids=[],
        research={},
        project_ids=["p1"],
    )

    restored = from_renderer(to_renderer(selection), "en-US")

    assert restored == selection


def test_unknown_language_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Selection(language="fr-FR", role_id="sweng", summary_ids=["s1"])


def test_optional_collections_default_to_empty() -> None:
    selection = Selection(language="pt-BR", role_id="sweng", summary_ids=["s1"])

    assert selection.skill_priority == []
    assert selection.experience == {}
    assert selection.project_ids == []
    assert selection.research_ids is None
