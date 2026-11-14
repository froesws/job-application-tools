"""One canonical name per skill, so JS and JavaScript never split a count."""

from __future__ import annotations

from cvtailor.core.aliases import canonical


def test_known_aliases_map_to_their_canonical_form() -> None:
    assert canonical("JS") == "javascript"
    assert canonical("postgres") == "postgresql"
    assert canonical("k8s") == "kubernetes"


def test_case_and_spacing_do_not_matter() -> None:
    assert canonical("  Postgres  ") == "postgresql"


def test_an_unknown_skill_is_only_normalized() -> None:
    assert canonical("  Rust ") == "rust"


def test_the_canonical_form_is_idempotent() -> None:
    assert canonical(canonical("JS")) == "javascript"
