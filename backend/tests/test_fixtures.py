"""The shared fixtures are valid: the profile renders and the selection validates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cvtailor.core.render_pdf import load_master, render_pdf, validate_selection


def test_fixture_profile_renders_one_page(
    profile_root: Path, renderer_selection: dict[str, Any], tmp_path: Path
) -> None:
    master = load_master(profile_root / "software-engineer" / "master.json")

    assert validate_selection(master, renderer_selection) == []

    result = render_pdf(master, renderer_selection, tmp_path / "cv.pdf")

    assert result["pages"] == 1
    assert (tmp_path / "cv.pdf").stat().st_size > 0


def test_scripted_llm_returns_answers_in_order(fake_llm) -> None:
    fake_llm.answers.append("first")

    assert fake_llm.complete("prompt", model="m") == "first"
    assert fake_llm.calls == [{"prompt": "prompt", "model": "m"}]
