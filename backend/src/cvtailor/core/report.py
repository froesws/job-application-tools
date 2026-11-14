"""The run report: the material a person reviews before sending the CV.

It carries the digest, the selection counts, the models and retries, the fallback state,
and every layout warning. The posting text never appears here, and none of this is written
into the PDF.
"""

from __future__ import annotations

from typing import Any

from cvtailor.core.layout import LayoutReport


def render_report(
    *,
    digest: dict[str, Any],
    section_counts: dict[str, int],
    layout: LayoutReport,
    models: dict[str, dict[str, Any]],
    retries: dict[str, int],
    fallback_used: bool,
    profile: str,
) -> str:
    lines = [
        f"# CV report — {digest['enterprise_name']} — {digest['job_title']}",
        "",
        f"Profile: {profile}",
        f"Pages: {layout.pages}",
        "",
        "## Digest",
        "",
        f"- Enterprise: {digest['enterprise_name']}",
        f"- Date: {digest['date']}",
        f"- Title: {digest['job_title']}",
        f"- Level: {digest['level']}",
        f"- Resume: {digest['resume']}",
        "",
        "Hard skills: " + ", ".join(digest["hard_skills"]),
        "",
        "Soft skills: " + ", ".join(digest["soft_skills"] or ["none"]),
        "",
        "## Selection",
        "",
    ]
    lines.extend(f"- {name}: {count}" for name, count in section_counts.items())
    lines.extend(["", "## Models", "", f"Fallback used: {'yes' if fallback_used else 'no'}"])
    for step, record in models.items():
        state = "admitted" if record.get("admitted") else "model_unadmitted"
        lines.append(f"- {step}: {record.get('id')} ({state}), retries: {retries.get(step, 0)}")
    lines.extend(["", "## Layout", ""])
    if layout.warnings:
        for warning in layout.warnings:
            suffix = (
                f" removed: {', '.join(warning.removed_bullet_ids)}"
                if warning.removed_bullet_ids
                else ""
            )
            lines.append(f"- {warning.code}: {warning.detail}{suffix}")
    else:
        lines.append("- no layout warnings")
    return "\n".join(lines) + "\n"
