"""The application service both adapters call.

It owns input validation, dependency resolution, and the client for each step. The
pipeline owns the steps themselves; the adapters own presentation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from cvtailor.core.errors import CONFIGURATION_ERROR, INVALID_POSTING, TailorError
from cvtailor.core.selection import OutputLanguage
from cvtailor.llm.client import LLMClient
from cvtailor.llm.config import LLMConfig, load
from cvtailor.llm.demo import demo_client
from cvtailor.pipeline import RunResult, run_tailor
from cvtailor.storage.paths import Paths, from_env
from cvtailor.storage.profiles import load_master

POSTING_MAX_CHARS = 100_000


class TailorService:
    def __init__(self, *, paths: Paths | None = None, config: LLMConfig | None = None) -> None:
        self.paths = paths or from_env()
        self.config = config or load()

    def tailor(
        self,
        *,
        posting: str,
        profile: str,
        language: OutputLanguage = "pt-BR",
        now: datetime | None = None,
    ) -> RunResult:
        _require_valid_posting(posting)
        master = load_master(self.paths, profile)
        models = {
            "analyze": _entry_label(self.config.analyze),
            "tailor": _entry_label(self.config.tailor),
        }
        client = self._client(master, language)
        return run_tailor(
            paths=self.paths,
            master=master,
            profile=profile,
            posting=posting,
            language=language,
            client=client,
            models=models,
            validation_retries=self.config.validation_retries,
            now=now,
        )

    def _client(self, master: dict[str, Any], language: OutputLanguage) -> LLMClient:
        providers = {entry.provider for entry in self.config.analyze + self.config.tailor}
        if providers == {"fake"}:
            return demo_client(master, language)
        raise TailorError(
            CONFIGURATION_ERROR,
            "Only the fake provider is wired so far; the OpenAI-compatible adapter lands in this feature's S3.",
        )


def _entry_label(chain: list[Any]) -> str:
    if not chain:
        raise TailorError(CONFIGURATION_ERROR, "No model chain is configured.")
    entry = chain[0]
    return f"{entry.provider}:{entry.model}"


def _require_valid_posting(posting: str) -> None:
    if not posting.strip():
        raise TailorError(INVALID_POSTING, "The posting is empty.")
    if len(posting) > POSTING_MAX_CHARS:
        raise TailorError(
            INVALID_POSTING,
            f"The posting exceeds {POSTING_MAX_CHARS} characters.",
        )
