"""The ingestion draft: what the model read, before anything reaches the master.

A draft is a JSON document plus the extracted blocks. Nothing here writes to the profile;
only an explicit save does, and only after every item was decided.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SECTIONS = (
    "person",
    "summaries",
    "skills",
    "experience",
    "research",
    "projects",
    "education",
    "certifications",
)

PENDING = "pending"
APPROVED = "approved"
REJECTED = "rejected"
UNVERIFIED = "unverified"
DUPLICATE = "duplicate"
USER_EDITED = "user_edited"

PROCESSING = "processing"
COMPLETE = "complete"
FAILED = "failed"
STALLED = "stalled"


@dataclass
class SectionStatus:
    state: str = PENDING
    reason: str | None = None
    attempts: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {"state": self.state, "reason": self.reason, "attempts": self.attempts}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SectionStatus:
        return cls(state=payload["state"], reason=payload.get("reason"), attempts=payload.get("attempts", 0))


@dataclass
class DraftItem:
    id: str
    kind: str
    section: str
    fields: dict[str, Any]
    parent: str | None = None
    quote: str | None = None
    source_language: str | None = None
    translated_variant: str | None = None
    source_text: str | None = None
    verification: dict[str, Any] | None = None
    warnings: list[str] = field(default_factory=list)
    duplicate: bool = False
    status: str = PENDING

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "section": self.section,
            "parent": self.parent,
            "fields": self.fields,
            "quote": self.quote,
            "source_language": self.source_language,
            "translated_variant": self.translated_variant,
            "source_text": self.source_text,
            "verification": self.verification,
            "warnings": list(self.warnings),
            "duplicate": self.duplicate,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> DraftItem:
        return cls(**payload)


@dataclass
class Draft:
    id: str
    created_at: str
    updated_at: str
    profile: str
    create_if_missing: bool
    state: str
    sources: list[dict[str, Any]]
    sections: dict[str, SectionStatus]
    items: list[DraftItem]
    extraction: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "profile": self.profile,
            "create_if_missing": self.create_if_missing,
            "state": self.state,
            "sources": self.sources,
            "sections": {name: status.to_dict() for name, status in self.sections.items()},
            "items": [item.to_dict() for item in self.items],
            "extraction": self.extraction,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Draft:
        return cls(
            id=payload["id"],
            created_at=payload["created_at"],
            updated_at=payload["updated_at"],
            profile=payload["profile"],
            create_if_missing=payload.get("create_if_missing", False),
            state=payload["state"],
            sources=list(payload.get("sources", [])),
            sections={name: SectionStatus.from_dict(status) for name, status in payload["sections"].items()},
            items=[DraftItem.from_dict(item) for item in payload.get("items", [])],
            extraction=dict(payload.get("extraction", {})),
        )


def new_draft_sections() -> dict[str, SectionStatus]:
    return {name: SectionStatus() for name in SECTIONS}


def counts(draft: Draft) -> dict[str, int]:
    totals = {PENDING: 0, APPROVED: 0, REJECTED: 0, UNVERIFIED: 0, DUPLICATE: 0, USER_EDITED: 0}
    for item in draft.items:
        totals[item.status] = totals.get(item.status, 0) + 1
    return totals


def readiness(draft: Draft) -> dict[str, Any]:
    approved = [item for item in draft.items if item.status in (APPROVED, USER_EDITED)]
    missing: list[str] = []
    if not any(item.section == "person" for item in approved):
        missing.append("a person item")
    if not any(item.kind == "summary_block" and item.fields.get("lead") for item in approved):
        missing.append("a summary block with lead")
    if not any(item.kind == "role" or item.section == "experience" for item in approved):
        missing.append("an experience role with bullets")
    return {"ready": not missing, "missing": missing}
