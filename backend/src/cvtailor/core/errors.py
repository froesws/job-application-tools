"""Typed errors shared by the pipeline, the CLI, and the HTTP API.

Every failure carries a stable code from the contract in the feature's data model.
Messages never contain the posting text, an API key, or a blocklisted term.
"""

from __future__ import annotations

from dataclasses import dataclass

INVALID_POSTING = "invalid_posting"
INVALID_SELECTION = "invalid_selection"
BLOCKLIST_HIT = "blocklist_hit"
PROFILE_NOT_FOUND = "profile_not_found"
RUN_NOT_FOUND = "run_not_found"
DIGEST_FAILURE = "digest_failure"
PAGE_OVERFLOW = "page_overflow"
FALLBACK_EXHAUSTED = "fallback_exhausted"
MODEL_UNAVAILABLE = "model_unavailable"
CONFIGURATION_ERROR = "configuration_error"
DRAFT_NOT_FOUND = "draft_not_found"
UNSUPPORTED_FILE = "unsupported_file"
UNREADABLE_FILE = "unreadable_file"
NO_TEXT_LAYER = "no_text_layer"
FILE_TOO_LARGE = "file_too_large"
TOO_MANY_FILES = "too_many_files"
EXTRACTION_LIMIT_EXCEEDED = "extraction_limit_exceeded"


@dataclass(frozen=True)
class Problem:
    """A single validation finding, addressable by the item it concerns."""

    code: str
    message: str
    item_id: str | None = None


class TailorError(Exception):
    """A failure with a stable code.

    ``item_ids`` names the offending items without revealing their content, which is
    what the blocklist contract requires.
    """

    def __init__(
        self,
        code: str,
        message: str,
        *,
        item_ids: list[str] | None = None,
        problems: list[Problem] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.item_ids = item_ids or []
        self.problems = problems or []
