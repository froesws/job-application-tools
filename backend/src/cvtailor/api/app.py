"""The FastAPI application: localhost only, one allowed origin, typed errors."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cvtailor.api.errors import tailor_error_handler
from cvtailor.api.routes import router
from cvtailor.core.errors import TailorError


def create_app() -> FastAPI:
    app = FastAPI(title="CV Tailor", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")],
        allow_methods=["GET", "POST"],
        allow_headers=["content-type"],
    )
    app.add_exception_handler(TailorError, tailor_error_handler)  # type: ignore[arg-type]
    app.include_router(router)
    return app


app = create_app()
