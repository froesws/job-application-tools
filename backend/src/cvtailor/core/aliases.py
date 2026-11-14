"""The documented skill alias table.

The digest verifier and the market reader both use it, so "same skill" has one definition
across the product. Keep it small and reviewable; an alias that is not here is not merged.
"""

from __future__ import annotations

ALIASES: dict[str, str] = {
    "c sharp": "c#",
    "csharp": "c#",
    "dotnet": ".net",
    "gcp": "google cloud",
    "golang": "go",
    "js": "javascript",
    "k8s": "kubernetes",
    "ml": "machine learning",
    "node": "node.js",
    "nodejs": "node.js",
    "postgres": "postgresql",
    "py": "python",
    "ts": "typescript",
}


def canonical(skill: str) -> str:
    normalized = skill.strip().lower()
    return ALIASES.get(normalized, normalized)
