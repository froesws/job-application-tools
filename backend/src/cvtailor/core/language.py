"""Posting language detection, in code and without a model.

It counts Portuguese and English function words. Detection is informational: the output
language is a run parameter and never switches silently.
"""

from __future__ import annotations

import re

from cvtailor.core.selection import OutputLanguage

_PORTUGUESE = {"a", "as", "com", "da", "das", "de", "do", "dos", "e", "em", "na", "não", "o", "os", "para", "por", "que", "um", "uma"}
_ENGLISH = {"a", "and", "are", "as", "at", "be", "for", "from", "have", "in", "is", "not", "of", "on", "that", "the", "this", "to", "we", "will", "with", "you"}


def detect(text: str) -> OutputLanguage:
    words = re.findall(r"[^\W\d_]+", text.lower())
    if not words:
        return "pt-BR"
    portuguese = sum(1 for word in words if word in _PORTUGUESE)
    english = sum(1 for word in words if word in _ENGLISH)
    return "en-US" if english > portuguese else "pt-BR"
