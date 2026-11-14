"""Request models. Response bodies are assembled by the routes from the run artifacts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from cvtailor.core.selection import Selection


class AnalyzeRequest(BaseModel):
    posting: str = Field(min_length=1)


class TailorRequest(BaseModel):
    posting: str = Field(min_length=1)
    profile: str
    language: Literal["pt-BR", "en-US"] = "pt-BR"


class RenderRequest(BaseModel):
    profile: str
    origin_run_id: str
    selection: Selection
