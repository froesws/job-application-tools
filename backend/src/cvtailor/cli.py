"""Command-line adapter over the application service.

It owns argument parsing, terminal output, and exit codes. It owns no pipeline logic.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

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
from cvtailor.pipeline import RunResult
from cvtailor.service import TailorService

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_INVALID = 3
EXIT_BLOCKLIST = 4
EXIT_DIGEST = 5
EXIT_OVERFLOW = 6
EXIT_MODEL = 7
EXIT_CONFIG = 8
EXIT_PROFILE = 9

_EXIT_CODES = {
    INVALID_POSTING: EXIT_INVALID,
    INVALID_SELECTION: EXIT_INVALID,
    BLOCKLIST_HIT: EXIT_BLOCKLIST,
    DIGEST_FAILURE: EXIT_DIGEST,
    FALLBACK_EXHAUSTED: EXIT_DIGEST,
    PAGE_OVERFLOW: EXIT_OVERFLOW,
    MODEL_UNAVAILABLE: EXIT_MODEL,
    CONFIGURATION_ERROR: EXIT_CONFIG,
    PROFILE_NOT_FOUND: EXIT_PROFILE,
    RUN_NOT_FOUND: 1,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cvtailor", description="Tailor a CV to a posting.")
    commands = parser.add_subparsers(dest="command", required=True)
    tailor = commands.add_parser("tailor", help="Generate a CV from a posting.")
    tailor.add_argument("--profile", required=True)
    tailor.add_argument("--posting", type=Path)
    tailor.add_argument("--stdin", action="store_true")
    tailor.add_argument("--language", choices=("pt-BR", "en-US"), default="pt-BR")
    tailor.add_argument("--non-interactive", action="store_true")
    tailor.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        posting = _read_posting(args)
    except OSError as error:
        return _fail(EXIT_USAGE, "usage_error", f"Cannot read the posting: {error}", json_mode=args.json)
    try:
        result = TailorService().tailor(
            posting=posting, profile=args.profile, language=args.language
        )
    except TailorError as error:
        return _fail(
            _EXIT_CODES.get(error.code, EXIT_CONFIG),
            error.code,
            error.message,
            json_mode=args.json,
            item_ids=error.item_ids,
        )
    _print_result(result, json_mode=args.json)
    return EXIT_OK


def _read_posting(args: argparse.Namespace) -> str:
    if args.stdin:
        return sys.stdin.read()
    if args.posting is None:
        raise OSError("provide --posting or --stdin")
    return args.posting.read_text(encoding="utf-8")


def _print_result(result: RunResult, *, json_mode: bool) -> None:
    payload: dict[str, object] = {
        "run_id": result.run_id,
        "profile": _profile_of(result),
        "pages": result.pages,
        "fallback_used": False,
        "pdf_path": str(result.run_dir / "cv.pdf"),
        "report_path": str(result.run_dir / "report.md"),
        "layout_warnings": [
            {"code": warning.code, "detail": warning.detail} for warning in result.layout.warnings
        ],
        "models": result.models,
    }
    if json_mode:
        print(json.dumps(payload, ensure_ascii=False))
        return
    print(f"Run {result.run_id}: {result.pages} page(s)")
    print(f"PDF: {payload['pdf_path']}")
    print(f"Report: {payload['report_path']}")


def _profile_of(result: RunResult) -> str:
    record = json.loads((result.run_dir / "run.json").read_text(encoding="utf-8"))
    return str(record["profile"])


def _fail(
    exit_code: int,
    code: str,
    message: str,
    *,
    json_mode: bool,
    item_ids: list[str] | None = None,
) -> int:
    payload: dict[str, object] = {"code": code, "message": message}
    if item_ids:
        payload["item_ids"] = item_ids
    if json_mode:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"error {code}: {message}", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
