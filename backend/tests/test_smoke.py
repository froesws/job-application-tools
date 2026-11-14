"""Proves the test runner resolves the backend package without packaging it."""

from __future__ import annotations


def test_cvtailor_package_is_importable() -> None:
    import cvtailor

    assert cvtailor.__name__ == "cvtailor"
