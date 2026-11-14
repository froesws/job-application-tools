"""A quote verifies only when the normalized text really contains it."""

from __future__ import annotations

from cvtailor.core.extraction import Block
from cvtailor.core.quotes import normalize, verify


def block(text: str, index: int = 0) -> Block:
    return Block(index=index, source="cv.pdf", location=f"page {index + 1}", text=text)


def test_whitespace_is_collapsed() -> None:
    assert normalize("Built\n  a   service") == "Built a service"


def test_curly_quotes_and_dashes_unify() -> None:
    assert normalize("\u201cLed\u201d \u2014 the team") == '"Led" - the team'


def test_a_hyphenated_line_break_joins_the_word() -> None:
    assert normalize("desen-\nvolvimento") == "desenvolvimento"


def test_unicode_is_normalized_to_nfc() -> None:
    assert normalize("cafe\u0301") == "caf\u00e9"


def test_an_exact_quote_verifies_with_its_block_and_offset() -> None:
    result = verify("Built a Python service.", [block("Work. Built a Python service. More.")])

    assert result.verified is True
    assert result.block_index == 0
    assert result.offset == 6


def test_a_quote_spanning_a_line_break_verifies() -> None:
    result = verify("desenvolvimento de software", [block("Experi\u00eancia em desen-\nvolvimento de software.")])

    assert result.verified is True


def test_comparison_is_case_sensitive() -> None:
    result = verify("python", [block("Python")])

    assert result.verified is False
    assert result.reason == "not_found"


def test_an_absent_quote_is_not_found() -> None:
    result = verify("Invented claim.", [block("Something else.")])

    assert result.verified is False


def test_an_empty_quote_is_refused() -> None:
    assert verify("   ", [block("text")]).reason == "empty_quote"


def test_no_blocks_means_no_verification() -> None:
    assert verify("text", []).reason == "no_blocks"
