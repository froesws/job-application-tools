"""Write the generated OpenAPI schema to backend/openapi.json."""

from __future__ import annotations

import json
from pathlib import Path

from cvtailor.api.app import create_app


def main() -> None:
    schema = create_app().openapi()
    target = Path(__file__).resolve().parents[3] / "openapi.json"
    target.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
