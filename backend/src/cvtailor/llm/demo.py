"""A self-consistent demo provider.

It answers with a digest and a selection that the current profile already satisfies, so
``LLM_PROVIDER=fake`` produces a real run without a key or a network. It is a demo path,
not a model: the answers are derived from the master, not written for a posting.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from cvtailor.core.selection import OutputLanguage
from cvtailor.llm.fake import FakeClient


def demo_client(master: dict[str, Any], language: OutputLanguage) -> FakeClient:
    return FakeClient([json.dumps(_digest()), json.dumps(_selection(master))])


def _digest() -> dict[str, Any]:
    return {
        "enterprise_name": "Demo Company",
        "date": datetime.now(UTC).date().isoformat(),
        "job_title": "Backend Engineer",
        "level": "mid_level",
        "resume": "Demo posting used to exercise the pipeline.",
        "hard_skills": ["Python"],
        "soft_skills": ["Ownership"],
    }


def _selection(master: dict[str, Any]) -> dict[str, Any]:
    role = master["role_options"][0]["id"]
    lead = next(block["id"] for block in master["summary_blocks"] if block.get("lead"))
    first_role = master["experience"][0]["roles"][0]
    bullets = [bullet["id"] for bullet in first_role["bullets"]][:2]
    skills = [
        item if isinstance(item, str) else item["en"]
        for item in master["skills"][0]["core"]
    ][:1]
    projects = [project["id"] for project in master["projects"]][:1]
    return {
        "role_id": role,
        "summary_ids": [lead],
        "experience": {first_role["id"]: bullets},
        "skill_priority": skills,
        "project_ids": projects,
        "research": {},
        "research_ids": [],
    }
