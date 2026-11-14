"""Quote verification: the only path by which extracted text becomes a draft item.

The normalizer runs on the extracted text and on the quote, so the comparison is like with
like. It is case-sensitive on purpose: case folding would let a rewritten sentence pass.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from cvtailor.core.extraction import Block

_PUNCTUATION = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2013": "-",
    "\u2014": "-",
    "\u00a0": " ",
}
_HYPHEN_BREAK = re.compile(r"-\s*\n\s*(?=[a-z\u00e0-\u00ff])")


@dataclass(frozen=True)
class Verification:
    verified: bool
    block_index: int | None = None
    offset: int | None = None
    reason: str | None = None


def normalize(text: str) -> str:
    unified = unicodedata.normalize("NFC", text)
    for source, target in _PUNCTUATION.items():
        unified = unified.replace(source, target)
    unified = _HYPHEN_BREAK.sub("", unified)
    return re.sub(r"\s+", " ", unified).strip()


def verify(quote: str, blocks: list[Block]) -> Verification:
    normalized_quote = normalize(quote)
    if not normalized_quote:
        return Verification(verified=False, reason="empty_quote")
    if not blocks:
        return Verification(verified=False, reason="no_blocks")
    for block in blocks:
        offset = normalize(block.text).find(normalized_quote)
        if offset != -1:
            return Verification(verified=True, block_index=block.index, offset=offset)
    return Verification(verified=False, reason="not_found")
