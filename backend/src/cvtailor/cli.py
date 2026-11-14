"""Command-line adapter over the application service.

It owns argument parsing, terminal output, and exit codes. It owns no pipeline logic.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Any

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
from cvtailor.core.selection import Selection
from cvtailor.pipeline import RunResult
from cvtailor.service import TailorService
from cvtailor.storage.paths import from_env
from cvtailor.storage.runs import list_runs, read_run, run_dir

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

    render = commands.add_parser("render", help="Re-render a selection against its origin.")
    render.add_argument("--profile", required=True)
    render.add_argument("--origin", required=True)
    render.add_argument("--selection", type=Path, required=True)
    render.add_argument("--json", action="store_true")

    runs = commands.add_parser("runs", help="Inspect previous runs.")
    runs_commands = runs.add_subparsers(dest="runs_command", required=True)
    listing = runs_commands.add_parser("list", help="List runs.")
    listing.add_argument("--json", action="store_true")
    show = runs_commands.add_parser("show", help="Show one run.")
    show.add_argument("run_id")
    show.add_argument("--json", action="store_true")

    review = commands.add_parser("review", help="Review a run in the terminal.")
    review.add_argument("run_id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {
        "tailor": _tailor,
        "render": _render,
        "runs": _runs,
        "review": _review,
    }
    try:
        return handlers[args.command](args)
    except OSError as error:
        return _fail(EXIT_USAGE, "usage_error", f"Cannot read the input: {error}", json_mode=getattr(args, "json", False))
    except TailorError as error:
        return _fail(
            _EXIT_CODES.get(error.code, EXIT_CONFIG),
            error.code,
            error.message,
            json_mode=getattr(args, "json", False),
            item_ids=error.item_ids,
        )


def _tailor(args: argparse.Namespace) -> int:
    posting = sys.stdin.read() if args.stdin else _required_file(args.posting).read_text(encoding="utf-8")
    result = TailorService().tailor(posting=posting, profile=args.profile, language=args.language)
    _print_result(result, json_mode=args.json)
    return EXIT_OK


def _render(args: argparse.Namespace) -> int:
    payload = json.loads(_required_file(args.selection).read_text(encoding="utf-8"))
    selection = Selection(**payload)
    result = TailorService().render(
        profile=args.profile, origin_run_id=args.origin, selection=selection
    )
    _print_result(result, json_mode=args.json)
    return EXIT_OK


def _runs(args: argparse.Namespace) -> int:
    paths = from_env()
    if args.runs_command == "list":
        run_ids = list_runs(paths)
        if args.json:
            print(json.dumps([read_run(paths, run_id) for run_id in run_ids], ensure_ascii=False))
            return EXIT_OK
        for run_id in run_ids:
            record = read_run(paths, run_id)
            print(f"{run_id}  {record['profile']}  {record['mode']}  {record['requested_language']}")
        return EXIT_OK
    record = read_run(paths, args.run_id)
    if args.json:
        print(json.dumps(record, ensure_ascii=False))
        return EXIT_OK
    print(f"Run {record['id']} ({record['mode']}) — profile {record['profile']}")
    print(f"Language: {record['requested_language']} · pages: {record.get('review', {}).get('section_counts', {})}")
    print(f"Coverage: {record.get('review', {}).get('coverage', 0):.0%}")
    for flag in record.get("review", {}).get("red_flags", []):
        print(f"- {flag['code']}: {flag['message']}")
    print(f"Report: {run_dir(paths, args.run_id) / 'report.md'}")
    return EXIT_OK


def _review(args: argparse.Namespace) -> int:
    paths = from_env()
    service = TailorService()
    record = read_run(paths, args.run_id)
    directory = run_dir(paths, args.run_id)
    origin = args.run_id
    print(f"Run {args.run_id} — profile {record['profile']}")
    print(f"PDF: {directory / 'cv.pdf'}")
    print(f"Report: {directory / 'report.md'}")
    while True:
        try:
            command = input("review> ").strip()
        except EOFError:
            return EXIT_OK
        if command in ("quit", "q", ""):
            return EXIT_OK
        if command == "open":
            webbrowser.open((directory / "cv.pdf").as_uri())
        elif command == "edit":
            origin = _edit_selection(service, paths, origin, record["profile"])
        elif command == "show":
            print(json.dumps(record.get("review", {}), ensure_ascii=False, indent=2))
        else:
            print("commands: open, edit, show, rerender, quit")


def _edit_selection(
    service: TailorService, paths: Any, origin: str, profile: str
) -> str:
    source = run_dir(paths, origin) / "selection.json"
    temporary = source.with_suffix(".edit.json")
    temporary.write_bytes(source.read_bytes())
    editor = os.environ.get("EDITOR", "vi")
    subprocess.run([editor, str(temporary)], check=False)
    payload = json.loads(temporary.read_text(encoding="utf-8"))
    result = service.render(
        profile=profile, origin_run_id=origin, selection=Selection(**payload)
    )
    print(f"Derived run {result.run_id}")
    return result.run_id


def _required_file(path: Path | None) -> Path:
    if path is None:
        raise OSError("provide --posting or --stdin")
    return path


def _print_result(result: RunResult, *, json_mode: bool) -> None:
    record = json.loads((result.run_dir / "run.json").read_text(encoding="utf-8"))
    payload: dict[str, Any] = {
        "run_id": result.run_id,
        "profile": record["profile"],
        "pages": result.pages,
        "fallback_used": result.fallback_used,
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


def _fail(
    exit_code: int,
    code: str,
    message: str,
    *,
    json_mode: bool,
    item_ids: list[str] | None = None,
) -> int:
    payload: dict[str, Any] = {"code": code, "message": message}
    if item_ids:
        payload["item_ids"] = item_ids
    if json_mode:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"error {code}: {message}", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
