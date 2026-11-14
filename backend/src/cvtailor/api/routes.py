"""The HTTP routes. Every one delegates to the service; none owns pipeline logic."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, Response, UploadFile
from fastapi.responses import FileResponse

from cvtailor.api.schemas import AnalyzeRequest, RenderRequest, TailorRequest
from cvtailor.core.errors import RUN_NOT_FOUND, TailorError
from cvtailor.llm.registry import resolve
from cvtailor.service import TailorService
from cvtailor.storage.paths import from_env
from cvtailor.storage.profiles import list_profiles, load_master
from cvtailor.storage.runs import run_dir

router = APIRouter(prefix="/api")


@router.post("/jobs/analyze")
def analyze(request: AnalyzeRequest) -> dict[str, Any]:
    return TailorService().analyze(posting=request.posting)


@router.post("/ingestions", status_code=202)
async def create_ingestion(
    profile: str = Form(...),
    create_if_missing: bool = Form(False),
    files: list[UploadFile] = File(...),  # noqa: B008
) -> dict[str, Any]:
    payloads = [(file.filename or "file", await file.read()) for file in files]
    draft = TailorService().create_draft(
        profile=profile, files=payloads, create_if_missing=create_if_missing
    )
    return _draft_payload(draft)


@router.get("/ingestions/{draft_id}")
def read_ingestion(draft_id: str) -> dict[str, Any]:
    service = TailorService()
    draft = service.read_draft(draft_id)
    payload = _draft_payload(draft)
    from cvtailor.storage.drafts import load_blocks

    payload["blocks"] = [
        {"index": block.index, "location": block.location, "text": block.text}
        for block in load_blocks(service.paths, draft_id)
    ]
    return payload


@router.delete("/ingestions/{draft_id}", status_code=204)
def discard_ingestion(draft_id: str) -> Response:
    TailorService().discard_draft(draft_id)
    return Response(status_code=204)


@router.get("/profiles")
def profiles() -> dict[str, Any]:
    paths = from_env()
    return {
        "profiles": [
            {"slug": summary.slug, "has_blocklist": summary.has_blocklist}
            for summary in list_profiles(paths)
        ]
    }


@router.get("/profiles/{slug}")
def profile(slug: str) -> dict[str, Any]:
    return load_master(from_env(), slug)


@router.post("/tailor", status_code=201)
def tailor(request: TailorRequest) -> dict[str, Any]:
    result = TailorService().tailor(
        posting=request.posting, profile=request.profile, language=request.language
    )
    return _summary(result.run_dir)


@router.post("/render", status_code=201)
def render(request: RenderRequest) -> dict[str, Any]:
    result = TailorService().render(
        profile=request.profile,
        origin_run_id=request.origin_run_id,
        selection=request.selection,
    )
    return _summary(result.run_dir)


@router.get("/runs")
def runs() -> dict[str, Any]:
    service = TailorService()
    return {"runs": [_summary(service.artifact(run_id, "run.json").parent) for run_id in service.list_runs()]}


@router.get("/runs/{run_id}")
def run_detail(run_id: str) -> dict[str, Any]:
    service = TailorService()
    record = service.run_record(run_id)
    directory = run_dir(from_env(), run_id)
    digest = _read_json(directory / "digest.json")
    selection = _read_json(directory / "selection.json")
    analysis = _read_json(directory / "analysis.json")
    return {
        "summary": _record_summary(record),
        "digest": digest,
        "selection": selection,
        "analysis": analysis,
        "review": record.get("review", {}),
        "models": record.get("models", {}),
        "retries": record.get("retries", {}),
        "artifacts": {
            "cv": "cv.pdf" if (directory / "cv.pdf").is_file() else None,
            "report": "report.md" if (directory / "report.md").is_file() else None,
        },
    }


@router.get("/runs/{run_id}/cv.pdf")
def cv_pdf(run_id: str) -> Response:
    return _artifact(run_id, "cv.pdf", "application/pdf")


@router.get("/runs/{run_id}/report.md")
def report_md(run_id: str) -> Response:
    return _artifact(run_id, "report.md", "text/markdown; charset=utf-8")


@router.get("/settings")
def settings() -> dict[str, Any]:
    service = TailorService()
    chains = {
        "analyze": [_chain_entry(entry.provider, entry.model) for entry in service.config.analyze],
        "tailor": [_chain_entry(entry.provider, entry.model) for entry in service.config.tailor],
    }
    key_set = any(_has_key(entry.provider) for entry in service.config.analyze + service.config.tailor)
    return {
        "api_key_set": key_set,
        "chains": chains,
        "limits": {
            "posting_max_chars": 100_000,
            "call_timeout_s": service.config.call_timeout_s,
            "run_budget_s": service.config.run_budget_s,
        },
        "version": "0.1.0",
    }


def _draft_payload(draft: Any) -> dict[str, Any]:
    from cvtailor.core.ingestion import counts, readiness

    return {
        **draft.to_dict(),
        "counts": counts(draft),
        "readiness": readiness(draft),
    }


def _summary(directory: Path) -> dict[str, Any]:
    return _record_summary(_read_json(directory / "run.json"))


def _record_summary(record: dict[str, Any]) -> dict[str, Any]:
    review = record.get("review", {})
    return {
        "id": record["id"],
        "created_at": record["created_at"],
        "profile": record["profile"],
        "mode": record["mode"],
        "origin_run_id": record.get("origin_run_id"),
        "requested_language": record["requested_language"],
        "coverage": review.get("coverage"),
        "fallback_used": record.get("fallback_used", False),
        "pages": 1 if (run_dir(from_env(), record["id"]) / "cv.pdf").is_file() else 0,
    }


def _artifact(run_id: str, name: str, media_type: str) -> Response:
    path = run_dir(from_env(), run_id) / name
    if not path.is_file():
        raise TailorError(RUN_NOT_FOUND, f"Unknown artifact for run: {run_id}")
    return FileResponse(path, media_type=media_type, filename=f"{run_id}-{name}")


def _read_json(path: Path) -> Any:
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def _chain_entry(provider: str, model: str) -> dict[str, Any]:
    return {"provider": provider, "model": model, "state": "unadmitted", "reason": None}


def _has_key(provider: str) -> bool:
    if provider == "fake":
        return True
    try:
        return bool(os.environ.get(resolve(provider).key_env))
    except ValueError:
        return False
