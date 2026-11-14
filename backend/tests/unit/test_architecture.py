"""The domain core imports nothing from the outside world."""

from __future__ import annotations

import ast
from pathlib import Path

CORE = Path(__file__).resolve().parents[2] / "src" / "cvtailor" / "core"
FORBIDDEN = ("fastapi", "starlette", "cvtailor.api", "cvtailor.llm", "cvtailor.storage", "cvtailor.service", "cvtailor.pipeline", "urllib")


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.add(node.module)
    return modules


def test_core_imports_no_web_model_storage_or_service_module() -> None:
    offenders = {
        path.name: sorted(name for name in imported_modules(path) if name.startswith(FORBIDDEN))
        for path in CORE.glob("*.py")
    }

    assert {name: hits for name, hits in offenders.items() if hits} == {}
