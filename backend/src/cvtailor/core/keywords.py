"""Tokenizing and overlap scoring for pre-ranking.

Deterministic and dependency-free: the same posting and the same text always produce the
same score, which is what makes the fallback explainable.
"""

from __future__ import annotations

import re

_TOKEN = re.compile(r"[a-z0-9#+.]+")

_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "be",
    "by",
    "com",
    "da",
    "de",
    "do",
    "e",
    "em",
    "for",
    "in",
    "is",
    "of",
    "on",
    "or",
    "os",
    "para",
    "por",
    "the",
    "to",
    "um",
    "uma",
    "with",
}


def tokens(text: str) -> set[str]:
    return {token for token in _TOKEN.findall(text.lower()) if token not in _STOPWORDS}


def score(posting: set[str], text: str) -> float:
    """The share of posting tokens that the text mentions."""
    if not posting:
        return 0.0
    return len(posting & tokens(text)) / len(posting)
