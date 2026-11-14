"""Detection counts function words; a tie reports the product default."""

from __future__ import annotations

from cvtailor.core.language import detect


def test_a_portuguese_posting_is_detected() -> None:
    assert detect("Estamos contratando para a vaga de engenheiro com experiência em Python.") == "pt-BR"


def test_an_english_posting_is_detected() -> None:
    assert detect("We are hiring an engineer with experience in Python and the cloud.") == "en-US"


def test_an_empty_text_is_the_default() -> None:
    assert detect("   ") == "pt-BR"


def test_a_tie_is_the_default() -> None:
    assert detect("the de") == "pt-BR"
