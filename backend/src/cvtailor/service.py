"""The application service both adapters call.

It owns input validation, dependency resolution, and the client for each step. The
pipeline owns the steps themselves; the adapters own presentation.
"""

from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from typing import Any

from cvtailor.agents.analyze import run_analyze
from cvtailor.agents.ingest import build_items, run_section
from cvtailor.core.errors import (
    CONFIGURATION_ERROR,
    EXTRACTION_LIMIT_EXCEEDED,
    FILE_TOO_LARGE,
    INVALID_POSTING,
    NO_TEXT_LAYER,
    TOO_MANY_FILES,
    TailorError,
)
from cvtailor.core.extraction import Block, extract, has_text_layer, text_length
from cvtailor.core.ingestion import Draft, SectionStatus, new_draft_sections
from cvtailor.core.language import detect
from cvtailor.core.selection import OutputLanguage, Selection
from cvtailor.llm.client import InvalidOutput, LLMClient
from cvtailor.llm.config import LLMConfig, load
from cvtailor.llm.demo import demo_analyze_client, demo_client, demo_ingest_client
from cvtailor.llm.openai_compatible import OpenAICompatibleClient
from cvtailor.llm.registry import resolve
from cvtailor.llm.retry import RetryingClient
from cvtailor.llm.routing import RoutedClient
from cvtailor.pipeline import RunResult, render_run, run_tailor
from cvtailor.storage.corpus import append_if_new
from cvtailor.storage.drafts import (
    delete_draft,
    load_draft,
    save_blocks,
    save_draft,
    sweep,
)
from cvtailor.storage.paths import Paths, from_env
from cvtailor.storage.profiles import load_master
from cvtailor.storage.runs import list_runs, new_run_id, read_run, run_dir

POSTING_MAX_CHARS = 100_000
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_FILES = 5
MAX_EXTRACTED_CHARS = 200_000


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

    def create_draft(
        self,
        *,
        profile: str,
        files: list[tuple[str, bytes]],
        create_if_missing: bool = False,
        now: datetime | None = None,
    ) -> Draft:
        sweep(self.paths)
        if not files:
            raise TailorError(INVALID_POSTING, "Upload at least one file.")
        if len(files) > MAX_FILES:
            raise TailorError(TOO_MANY_FILES, f"At most {MAX_FILES} files per draft.")
        moment = now or datetime.now(UTC)
        blocks: list[Block] = []
        sources: list[dict[str, Any]] = []
        skipped: list[dict[str, str]] = []
        for name, data in files:
            if len(data) > MAX_FILE_BYTES:
                raise TailorError(FILE_TOO_LARGE, f"{name} exceeds the size limit.")
            extracted = extract(name, data)
            if not has_text_layer(extracted):
                skipped.append({"name": name, "reason": NO_TEXT_LAYER})
                continue
            for block in extracted:
                blocks.append(
                    Block(
                        index=len(blocks),
                        source=name,
                        location=block.location,
                        text=block.text,
                    )
                )
            sources.append(
                {
                    "name": name,
                    "bytes": len(data),
                    "hash": hashlib.sha256(data).hexdigest(),
                    "format": name.rsplit(".", 1)[-1].lower(),
                }
            )
        if not blocks:
            raise TailorError(NO_TEXT_LAYER, "No uploaded file has a text layer.")
        if text_length(blocks) > MAX_EXTRACTED_CHARS:
            raise TailorError(EXTRACTION_LIMIT_EXCEEDED, "The extracted text exceeds the limit.")
        draft = Draft(
            id=new_run_id(moment),
            created_at=moment.isoformat(),
            updated_at=moment.isoformat(),
            profile=profile,
            create_if_missing=create_if_missing,
            state="processing",
            sources=sources,
            sections=new_draft_sections(),
            items=[],
            extraction={
                "blocks": len(blocks),
                "characters": text_length(blocks),
                "files_read": len(sources),
                "files_skipped": skipped,
            },
        )
        _apply_section(self, draft, blocks)
        save_blocks(self.paths, draft.id, blocks)
        save_draft(self.paths, draft)
        return draft

    def _ingest_client(self, blocks: list[Block]) -> LLMClient:
        providers = {entry.provider for entry in self.config.analyze}
        if providers == {"fake"}:
            return demo_ingest_client(blocks)
        return self._routed(providers)

    def read_draft(self, draft_id: str) -> Draft:
        return load_draft(self.paths, draft_id)

    def discard_draft(self, draft_id: str) -> None:
        delete_draft(self.paths, draft_id)

    def analyze(self, *, posting: str, now: datetime | None = None) -> dict[str, Any]:
        _require_valid_posting(posting)
        client = self._analyze_client()
        model = _entry_label(self.config.analyze)
        digest, retries = run_analyze(
            client, model_id=model, posting=posting, attempts=self.config.validation_retries
        )
        appended = append_if_new(
            self.paths,
            digest=digest,
            posting=posting,
            date=(now or datetime.now(UTC)).date().isoformat(),
            detected_language=detect(posting),
        )
        return {
            "digest": digest,
            "detected_language": detect(posting),
            "corpus_appended": appended,
            "models": {"analyze": {"id": model, "admitted": False}},
            "retries": {"analyze": retries},
        }

    def render(
        self,
        *,
        profile: str,
        origin_run_id: str,
        selection: Selection,
    ) -> RunResult:
        master = load_master(self.paths, profile)
        return render_run(
            paths=self.paths,
            master=master,
            profile=profile,
            origin_run_id=origin_run_id,
            selection=selection,
        )

    def list_runs(self) -> list[str]:
        return list_runs(self.paths)

    def run_record(self, run_id: str) -> dict[str, Any]:
        return read_run(self.paths, run_id)

    def artifact(self, run_id: str, name: str):
        return run_dir(self.paths, run_id) / name

    def _analyze_client(self) -> LLMClient:
        providers = {entry.provider for entry in self.config.analyze}
        if providers == {"fake"}:
            return demo_analyze_client()
        return self._routed(providers)

    def _client(self, master: dict[str, Any], language: OutputLanguage) -> LLMClient:
        providers = {entry.provider for entry in self.config.analyze + self.config.tailor}
        if providers == {"fake"}:
            return demo_client(master, language)
        return self._routed(providers)

    def _routed(self, providers: set[str]) -> LLMClient:
        routes: dict[str, LLMClient] = {}
        for provider in sorted(providers):
            resolved = resolve(provider)
            key = os.environ.get(resolved.key_env, "")
            if not key:
                raise TailorError(
                    CONFIGURATION_ERROR, f"{resolved.key_env} is not set for {provider}."
                )
            routes[provider] = RetryingClient(
                OpenAICompatibleClient(
                    provider=provider,
                    key=key,
                    base_url=resolved.base_url,
                    timeout_s=self.config.call_timeout_s,
                ),
                attempts=3,
                backoff_s=1.0,
                budget_s=self.config.run_budget_s,
            )
        return RoutedClient(routes)


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


def _apply_section(service: TailorService, draft: Draft, blocks: list[Block]) -> None:
    """Run the experience section and record its result on the draft."""
    text = " ".join(block.text for block in blocks)
    model = _entry_label(service.config.analyze)
    try:
        proposals, retries = run_section(
            service._ingest_client(blocks),
            model_id=model,
            section="experience",
            blocks=blocks,
            language=detect(text),
            attempts=service.config.validation_retries,
        )
    except InvalidOutput:
        draft.sections["experience"] = SectionStatus(
            state="failed", reason="invalid_output", attempts=service.config.validation_retries
        )
        draft.state = "failed"
        return
    draft.items = build_items("experience", proposals, blocks)
    draft.sections["experience"] = SectionStatus(state="ok", attempts=retries + 1)
    draft.state = "complete"
