"""The blocklist stops a render and names the item, never the matched term."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cvtailor.core.blocklist import check, load
from cvtailor.core.selection import Selection


def selection(**overrides: Any) -> Selection:
    payload: dict[str, Any] = {
        "language": "en-US",
        "role_id": "sweng",
        "summary_ids": ["s1"],
        "experience": {"role1": ["b1", "b2"]},
        "project_ids": ["p1"],
    }
    payload.update(overrides)
    return Selection(**payload)


def test_missing_file_is_an_empty_blocklist(tmp_path: Path) -> None:
    assert load(tmp_path / "missing.txt") == []


def test_comments_and_blank_lines_are_ignored(tmp_path: Path) -> None:
    path = tmp_path / "blocklist.txt"
    path.write_text("# clients\n\nAcme  \n  Globex\n", encoding="utf-8")

    assert load(path) == ["Acme", "Globex"]


def test_a_matching_bullet_blocks_and_is_named(master: dict[str, Any]) -> None:
    master["experience"][0]["roles"][0]["bullets"][0]["en"] = "Built Acme's billing."

    hits = check(["Acme"], master, selection())

    assert hits == ["b1"]


def test_matching_is_case_insensitive(master: dict[str, Any]) -> None:
    master["experience"][0]["roles"][0]["bullets"][1]["en"] = "Shipped for GLOBEX."

    assert check(["globex"], master, selection()) == ["b2"]


def test_a_summary_hit_is_named_by_its_id(master: dict[str, Any]) -> None:
    master["summary_blocks"][0]["en"] = "Engineer who worked at Acme."

    assert check(["Acme"], master, selection()) == ["s1"]


def test_a_project_hit_is_named_by_its_id(master: dict[str, Any]) -> None:
    master["projects"][0]["en"] = "Acme Migration"

    assert check(["Acme"], master, selection()) == ["p1"]


def test_only_the_selected_language_is_checked(master: dict[str, Any]) -> None:
    master["experience"][0]["roles"][0]["bullets"][0]["pt"] = "Trabalhou na Acme."

    assert check(["Acme"], master, selection(language="en-US")) == []
    assert check(["Acme"], master, selection(language="pt-BR")) == ["b1"]


def test_no_terms_means_no_hits(master: dict[str, Any]) -> None:
    assert check([], master, selection()) == []
