"""Tokenizing and overlap scoring are deterministic and case-insensitive."""

from __future__ import annotations

from cvtailor.core.keywords import score, tokens


def test_tokens_drop_punctuation_and_case() -> None:
    assert tokens("Python, PostgreSQL!") == {"python", "postgresql"}


def test_tokens_keep_technology_shapes() -> None:
    assert tokens("C# and .NET and Node.js") == {"c#", ".net", "node.js"}


def test_tokens_of_an_empty_text_are_empty() -> None:
    assert tokens("   \n ") == set()


def test_a_full_overlap_scores_one() -> None:
    posting = tokens("Python PostgreSQL")

    assert score(posting, "Python and PostgreSQL") == 1.0


def test_a_partial_overlap_scores_the_share() -> None:
    posting = tokens("Python PostgreSQL Kubernetes")

    assert score(posting, "Python service") == 1 / 3


def test_no_overlap_scores_zero() -> None:
    assert score(tokens("Python"), "Java") == 0.0


def test_an_empty_posting_scores_zero() -> None:
    assert score(set(), "Python") == 0.0
