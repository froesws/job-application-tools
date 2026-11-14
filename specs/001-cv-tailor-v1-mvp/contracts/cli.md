# CLI Contract: CV Tailor v1 MVP

The CLI is a thin adapter over the same `TailorService` the HTTP API uses. It owns
argument parsing, terminal output, and exit codes; it owns no pipeline logic.

**Entry point**: `python -m cvtailor.cli` (the Makefile sets
`PYTHONPATH=backend/src`). Commands and flags are stable; `tasks.md` may add none
without changing this file.

## Commands

### `tailor`

```text
tailor --profile SLUG --posting FILE | --stdin
       [--language pt-BR|en-US]
       [--non-interactive] [--json]
       [--open]
```

- `--profile SLUG` is required. The slug must name a directory with a `master.json`.
- `--posting FILE` reads the posting from a file; `--stdin` reads it from standard
  input. Exactly one is required.
- `--language` defaults to `pt-BR`.
- `--non-interactive` suppresses all prompts and disables the review loop.
- `--json` prints one JSON object to stdout and nothing else.
- `--open` opens the PDF in the operating system viewer after a successful run
  (ignored with `--non-interactive`).

Without `--non-interactive`, the command enters the review loop after the run: it
prints the digest summary, profile, selected counts, gaps, coverage, page count, and
artifact paths; then accepts `open`, `edit`, `rerender`, `show`, and `quit`.

`edit` writes the selection to a temporary file, opens `$EDITOR`, and on save
validates and re-renders through the render path with no model call. An invalid
edited selection prints the validation errors and keeps the original run intact.

Exit codes: `0` success, `2` usage error, `3` invalid posting or invalid selection,
`4` blocklist hit, `5` digest failure or fallback exhausted, `6` page overflow,
`7` model unavailable, `8` configuration error, `9` unknown profile.

### `render`

```text
render --profile SLUG --origin RUN_ID --selection FILE [--out DIR] [--json]
```

Validates and renders an existing selection with no model call. `--origin` is
required: every render derives from a run and copies its digest and analysis.
`--out` overrides the run root (default `data/runs`).

Exit codes: same as `tailor`, plus `1` for an unknown origin run.

### `runs list`

```text
runs list [--json]
```

Prints one line per run: id, created date, profile, enterprise, job title, language,
page count, and whether the run was a fallback. `--json` prints the same array as
`GET /api/runs`.

### `runs show`

```text
runs show RUN_ID [--json] [--open]
```

Prints the profile, digest, selection counts, gaps, coverage, red flags, layout
warnings, models with admission state, retries, and artifact paths. `--json` prints
the same object as `GET /api/runs/{id}`. `--open` opens the PDF in the operating
system viewer.

Exit codes: `0` success, `1` run not found, `2` usage error.

### `review`

```text
review RUN_ID [--open]
```

Reopens a previous run in the interactive review loop: same output as `runs show`
plus the `open`, `edit`, `rerender`, and `quit` actions. The profile comes from the
run metadata; `rerender` writes a derived run and never modifies the origin.

## Profiles

There is no `profiles create` command in version 1. A profile is created by making
the directory and adding a `master.json`:

```bash
mkdir -p profile/software-engineer
cp profile/master.example.json profile/software-engineer/master.json
```

`profile/blocklist.txt` does not exist as a global file: each profile may carry its
own `profile/<slug>/blocklist.txt`, and a missing file means nothing is blocked.

## Secrets

There is no `--api-key`, `--base-url`, or any credential flag. Passing one is a
usage error (`2`). Configuration comes from the environment or the git-ignored
`.env` at the repository root.

## Non-interactive output

With `--json`, stdout carries exactly one JSON object and nothing else; diagnostics
go to stderr. The object holds `run_id`, `profile`, `pages`, `fallback_used`,
`selection_path`, `pdf_path`, `report_path`, `digest`, `gaps`, `coverage`,
`layout_warnings`, and `models` with admission state. Paths are absolute because the
caller owns the filesystem.

Without `--json`, human output is English and follows the review loop's summary
format. Nothing in either mode prints the posting text or a credential.

## Artifacts

Both adapters write the same run layout under `data/runs/<id>/`. A CLI run is
reopenable in the web UI and vice versa; the UI reads it through `GET /api/runs`.
