# CV Tailor

Turns a pasted job posting into a one-page CV built only from facts the candidate already
approved, plus a report that says what matched, what was missing, and which model decided.

The tool is local and single-user: the backend binds to `127.0.0.1`, the browser never
holds an API key, and the job posting is never returned by the API.

## Requirements

- Python 3.14 with `uv`
- Node 26 and npm 11 for the frontend
- A CV export in PDF or DOCX, or a hand-written `profile/<slug>/master.json`

## Install

```bash
make install
cp .env.example .env            # fill the provider keys and chains you use
cp profile/master.example.json profile/my-profile/master.json
```

`profile/` and `data/` are git-ignored; only the example files are committed.

## Use the terminal

```bash
PYTHONPATH=backend/src uv run python -m cvtailor.cli tailor \
  --profile my-profile --posting posting.txt --json

PYTHONPATH=backend/src uv run python -m cvtailor.cli runs list
PYTHONPATH=backend/src uv run python -m cvtailor.cli render \
  --profile my-profile --origin <run-id> --selection selection.json
```

With `LLM_PROVIDER=fake`, the demo provider answers from the profile and produces a real
run without a key or a network call.

Exit codes: `0` success, `2` usage, `3` invalid posting or selection, `4` blocklist hit,
`5` digest failure or fallback exhausted, `6` page overflow, `7` model unavailable,
`8` configuration error, `9` unknown profile.

## Use the API

```bash
PYTHONPATH=backend/src uv run uvicorn cvtailor.api.app:app --host 127.0.0.1 --port 8000
```

`GET /api/profiles`, `POST /api/jobs/analyze`, `POST /api/tailor`, `POST /api/render`,
`GET /api/runs`, `GET /api/runs/{id}`, `GET /api/runs/{id}/cv.pdf`,
`GET /api/runs/{id}/report.md`, `GET /api/settings`. The checked-in schema is
`backend/openapi.json`.

## Checks

```bash
make check
```

Runs ruff, mypy, pytest, the committed-data guard, and the OpenAPI drift check. The suite
covers the renderer directly, the API at its seam with a scripted model, and the CLI at its
process boundary.

## Documentation

- `specs/` — per-feature specification, plan, data model, contracts, tasks.
- `.specify/memory/constitution.md` — the governing principles.
- `docs/planning-artifacts.md` — which planning artifact governs what.
- `docs/decisions.md` — short notes on choices that are easy to re-litigate.
