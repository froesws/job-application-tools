"""The fixed tailor pipeline: analyze, choose, validate, check, render, report.

Every step runs in order and the run directory is assembled in staging before it is
renamed, so an interrupted run leaves nothing readable. The blocklist and the page-fit
check are gates: a hit raises before the run is committed.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cvtailor.agents.analyze import run_analyze
from cvtailor.agents.tailor import run_tailor as run_tailor_step
from cvtailor.core.blocklist import check as blocklist_check
from cvtailor.core.blocklist import load as blocklist_load
from cvtailor.core.errors import (
    BLOCKLIST_HIT,
    PAGE_OVERFLOW,
    TailorError,
)
from cvtailor.core.fallback import fallback_selection
from cvtailor.core.gaps import pre_rank
from cvtailor.core.language import detect
from cvtailor.core.layout import LayoutReport
from cvtailor.core.layout import evaluate as evaluate_layout
from cvtailor.core.render_pdf import render_pdf
from cvtailor.core.report import render_report
from cvtailor.core.selection import OutputLanguage, to_renderer
from cvtailor.llm.client import InvalidOutput, LLMClient
from cvtailor.storage.corpus import append_if_new
from cvtailor.storage.paths import Paths
from cvtailor.storage.profiles import BLOCKLIST, profile_dir
from cvtailor.storage.runs import commit_run, create_staging, new_run_id

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class RunResult:
    run_id: str
    run_dir: Path
    pages: int
    layout: LayoutReport
    models: dict[str, dict[str, Any]]
    retries: dict[str, int]
    fallback_used: bool


def run_tailor(
    *,
    paths: Paths,
    master: dict[str, Any],
    profile: str,
    posting: str,
    language: OutputLanguage,
    client: LLMClient,
    models: dict[str, str],
    validation_retries: int,
    now: datetime | None = None,
) -> RunResult:
    moment = now or datetime.now(UTC)
    digest, analyze_retries = run_analyze(
        client, model_id=models["analyze"], posting=posting, attempts=validation_retries
    )
    append_if_new(
        paths,
        digest=digest,
        posting=posting,
        date=moment.date().isoformat(),
        detected_language=language,
    )
    fallback_used = False
    try:
        selection, tailor_retries = run_tailor_step(
            client,
            model_id=models["tailor"],
            master=master,
            digest=digest,
            candidates=catalog(master),
            language=language,
            attempts=validation_retries,
        )
    except InvalidOutput:
        selection = fallback_selection(master, digest, language)
        tailor_retries = validation_retries
        fallback_used = True
    _check_blocklist(paths, profile, master, selection)
    run_id = new_run_id(moment)
    staging = create_staging(paths, run_id)
    try:
        render_result = render_pdf(master, to_renderer(selection), staging / "cv.pdf")
        layout = evaluate_layout(render_result, selection, master)
        if layout.overflow:
            raise _overflow(layout)
        _write_artifacts(
            staging=staging,
            run_id=run_id,
            profile=profile,
            posting=posting,
            language=language,
            digest=digest,
            selection=selection,
            layout=layout,
            models=models,
            retries={"analyze": analyze_retries, "tailor": tailor_retries},
            fallback_used=fallback_used,
            detected_language=detect(posting),
            pre_rank=pre_rank(master, digest),
            moment=moment,
        )
        final = commit_run(staging, paths, run_id)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return RunResult(
        run_id=run_id,
        run_dir=final,
        pages=layout.pages,
        layout=layout,
        models={step: {"id": model, "admitted": False} for step, model in models.items()},
        retries={"analyze": analyze_retries, "tailor": tailor_retries},
        fallback_used=fallback_used,
    )


def catalog(master: dict[str, Any]) -> dict[str, Any]:
    """Everything the model may choose from. Ids only."""
    return {
        "roles": [role["id"] for role in master["role_options"]],
        "summaries": [
            {"id": block["id"], "lead": bool(block.get("lead"))}
            for block in master["summary_blocks"]
        ],
        "bullets": {
            role["id"]: [bullet["id"] for bullet in role["bullets"]]
            for entry in master["experience"]
            for role in entry["roles"]
        },
        "skills": sorted(
            {
                (item if isinstance(item, str) else item["en"])
                for group in master["skills"]
                for item in list(group["core"]) + list(group["extra"])
            }
        ),
        "projects": [project["id"] for project in master["projects"]],
        "research": [research["id"] for research in master["research"]],
    }


def _check_blocklist(
    paths: Paths, profile: str, master: dict[str, Any], selection: Any
) -> None:
    terms = blocklist_load(profile_dir(paths, profile) / BLOCKLIST)
    hits = blocklist_check(terms, master, selection)
    if hits:
        raise TailorError(
            BLOCKLIST_HIT,
            "The selection contains a blocklisted item.",
            item_ids=hits,
        )


def _overflow(layout: LayoutReport) -> TailorError:
    detail = ", ".join(f"{name}: {count}" for name, count in layout.section_counts.items())
    return TailorError(
        PAGE_OVERFLOW,
        f"The CV still exceeds one page after every auto-fit attempt ({detail}).",
        problems=[],
    )


def _write_artifacts(
    *,
    staging: Path,
    run_id: str,
    profile: str,
    posting: str,
    language: OutputLanguage,
    digest: dict[str, Any],
    selection: Any,
    layout: LayoutReport,
    models: dict[str, str],
    retries: dict[str, int],
    fallback_used: bool,
    detected_language: str,
    pre_rank: dict[str, dict[str, float]],
    moment: datetime,
) -> None:
    model_records: dict[str, dict[str, Any]] = {
        step: {"id": model, "admitted": False} for step, model in models.items()
    }
    record = {
        "schema_version": SCHEMA_VERSION,
        "id": run_id,
        "created_at": moment.isoformat(),
        "profile": profile,
        "origin_run_id": None,
        "mode": "tailor",
        "requested_language": language,
        "render_language": "pt" if language == "pt-BR" else "en",
        "digest_hash": _digest_hash(digest),
        "models": model_records,
        "retries": retries,
        "fallback_used": fallback_used,
        "paths": {},
    }
    _write_json(staging / "digest.json", digest)
    _write_json(
        staging / "analysis.json",
        {
            "detected_language": detected_language,
            "must_have_skills": [],
            "nice_to_have_skills": [],
            "keywords": [],
            "pre_rank": pre_rank,
        },
    )
    _write_json(staging / "selection.json", selection.model_dump())
    _write_json(staging / "run.json", record)
    (staging / "report.md").write_text(
        render_report(
            digest=digest,
            section_counts=layout.section_counts,
            layout=layout,
            models=model_records,
            retries=retries,
            fallback_used=fallback_used,
            profile=profile,
        ),
        encoding="utf-8",
    )
    (staging / "posting.txt").write_text(posting, encoding="utf-8")


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _digest_hash(digest: dict[str, Any]) -> str:
    canonical = json.dumps(digest, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
