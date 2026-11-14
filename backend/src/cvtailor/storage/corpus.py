"""The market corpus: one append-only JSONL record per unique posting.

The normalized hash is the identity. It never stores the posting text, and a repeat
analysis appends nothing.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from cvtailor.storage.paths import Paths


def normalize_posting(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def posting_hash(text: str) -> str:
    return hashlib.sha256(normalize_posting(text).encode("utf-8")).hexdigest()


def append_if_new(
    paths: Paths,
    *,
    digest: dict[str, Any],
    posting: str,
    date: str,
    detected_language: str,
) -> bool:
    """Append the digest once per normalized posting. Returns whether it appended."""
    digest_hash = posting_hash(posting)
    if any(record.get("hash") == digest_hash for record in read_all(paths)):
        return False
    record = {
        "hash": digest_hash,
        "date": date,
        "detected_language": detected_language,
        "digest": digest,
    }
    paths.data_root.mkdir(parents=True, exist_ok=True)
    with paths.corpus_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return True


def read_all(paths: Paths) -> list[dict[str, Any]]:
    if not paths.corpus_path.is_file():
        return []
    records: list[dict[str, Any]] = []
    for line in paths.corpus_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        records.append(json.loads(line))
    return records
