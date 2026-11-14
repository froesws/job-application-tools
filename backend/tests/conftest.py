"""Shared fixtures for the backend suite.

The profile fixture is deliberately small but valid: it satisfies every rule the
renderer enforces, so any test that renders it gets a real one-page PDF.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

MASTER_MINIMAL: dict[str, Any] = {
    "person": {
        "name": "Test Person",
        "phone_intl": "+55 11 99999-0000",
        "phone_local": "(11) 99999-0000",
        "email": "test@example.com",
        "location_en": "Sao Paulo - Brazil",
        "location_pt": "Sao Paulo - Brasil",
        "links": [{"label": "GitHub", "url": "https://github.com/test"}],
    },
    "role_options": [
        {"id": "sweng", "en": "Software Engineer", "pt": "Engenheiro de Software"}
    ],
    "summary_blocks": [
        {
            "id": "s1",
            "lead": True,
            "en": "Engineer focused on Python.",
            "pt": "Engenheiro focado em Python.",
        },
        {
            "id": "s2",
            "en": "Works on data platforms.",
            "pt": "Trabalha com plataformas de dados.",
        },
    ],
    "skills": [
        {
            "label_en": "Languages",
            "label_pt": "Linguagens",
            "core": ["Python", {"en": "TypeScript", "pt": "TypeScript"}],
            "extra": ["Rust"],
        }
    ],
    "experience": [
        {
            "header_en": "Acme",
            "header_pt": "Acme",
            "date_en": "2020-2024",
            "date_pt": "2020-2024",
            "roles": [
                {
                    "id": "role1",
                    "title_en": "Engineer",
                    "title_pt": "Engenheiro",
                    "date_en": "2020-2024",
                    "date_pt": "2020-2024",
                    "intro_en": "Built services.",
                    "intro_pt": "Construiu servicos.",
                    "bullets": [
                        {
                            "id": "b1",
                            "en": "Built a Python service.",
                            "pt": "Construiu um servico Python.",
                        },
                        {
                            "id": "b2",
                            "en": "Led a migration.",
                            "pt": "Liderou uma migracao.",
                        },
                    ],
                }
            ],
        }
    ],
    "research": [],
    "projects": [{"id": "p1", "en": "Project A", "pt": "Projeto A"}],
    "education": [
        {
            "header_en": "BSc CS",
            "header_pt": "Bacharelado em Ciencia da Computacao",
            "date": "2018",
            "desc_en": "Computer Science",
            "desc_pt": "Ciencia da Computacao",
        }
    ],
    "certs": {"en": "Cert A", "pt": "Cert A"},
}


class ScriptedLLM:
    """A stand-in for the model layer: returns queued answers and records calls."""

    def __init__(self, answers: list[str | Exception] | None = None) -> None:
        self.answers = list(answers or [])
        self.calls: list[dict[str, str]] = []

    def complete(self, prompt: str, *, model: str) -> str:
        self.calls.append({"prompt": prompt, "model": model})
        if not self.answers:
            raise AssertionError("ScriptedLLM ran out of answers")
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


@pytest.fixture()
def fake_llm() -> ScriptedLLM:
    return ScriptedLLM()


@pytest.fixture()
def profile_root(tmp_path: Path) -> Path:
    """A profile root holding one usable profile."""
    root = tmp_path / "profile"
    slug_dir = root / "software-engineer"
    slug_dir.mkdir(parents=True)
    (slug_dir / "master.json").write_text(json.dumps(MASTER_MINIMAL), encoding="utf-8")
    return root


@pytest.fixture()
def data_root(tmp_path: Path) -> Path:
    root = tmp_path / "data"
    root.mkdir()
    return root


@pytest.fixture()
def sample_posting() -> str:
    return (
        "We are hiring a Backend Engineer. Requirements: Python, PostgreSQL, "
        "and experience with distributed systems. Nice to have: Rust."
    )


@pytest.fixture()
def sample_selection() -> dict[str, Any]:
    """The API shape, with the output language as the API spells it."""
    return {
        "language": "en-US",
        "role_id": "sweng",
        "summary_ids": ["s1"],
        "skill_priority": ["Python"],
        "experience": {"role1": ["b1", "b2"]},
        "research_ids": [],
        "research": {},
        "project_ids": ["p1"],
    }


@pytest.fixture()
def renderer_selection() -> dict[str, Any]:
    """The same picks in the renderer's vocabulary."""
    return {
        "language": "en",
        "role_id": "sweng",
        "summary_ids": ["s1"],
        "skill_priority": ["Python"],
        "experience": {"role1": ["b1", "b2"]},
        "research_ids": [],
        "research": {},
        "project_ids": ["p1"],
    }


@pytest.fixture()
def env(
    monkeypatch: pytest.MonkeyPatch, profile_root: Path, data_root: Path
) -> Iterator[None]:
    """Point the application at temporary roots."""
    monkeypatch.setenv("CVTAILOR_PROFILE_ROOT", str(profile_root))
    monkeypatch.setenv("CVTAILOR_DATA_ROOT", str(data_root))
    yield
