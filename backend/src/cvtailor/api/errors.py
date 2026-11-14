"""Serialize the domain's typed errors as ``{code, message}`` with a stable status."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from cvtailor.core.errors import (
    BLOCKLIST_HIT,
    CONFIGURATION_ERROR,
    DIGEST_FAILURE,
    FALLBACK_EXHAUSTED,
    INVALID_POSTING,
    INVALID_SELECTION,
    MODEL_UNAVAILABLE,
    PAGE_OVERFLOW,
    PROFILE_NOT_FOUND,
    RUN_NOT_FOUND,
    TailorError,
)

STATUS: dict[str, int] = {
    INVALID_POSTING: 400,
    INVALID_SELECTION: 400,
    BLOCKLIST_HIT: 400,
    PROFILE_NOT_FOUND: 404,
    RUN_NOT_FOUND: 404,
    DIGEST_FAILURE: 422,
    PAGE_OVERFLOW: 422,
    FALLBACK_EXHAUSTED: 422,
    MODEL_UNAVAILABLE: 503,
    CONFIGURATION_ERROR: 500,
}


async def tailor_error_handler(_: Request, error: TailorError) -> JSONResponse:
    payload: dict[str, object] = {"code": error.code, "message": error.message}
    if error.item_ids:
        payload["item_ids"] = error.item_ids
    return JSONResponse(status_code=STATUS.get(error.code, 500), content=payload)
