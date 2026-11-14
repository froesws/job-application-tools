# Quickstart Validation: CV Tailor v1 MVP

Validation scenarios that prove the feature works end to end. Run them in order;
each states what to observe. Contracts live in [contracts/](./contracts/), entity
shapes in [data-model.md](./data-model.md).

## Prerequisites

- `uv` 0.13 or newer and Python 3.14 (the repository `.venv`).
- Node 26 and npm 11 for the frontend.
- A font file set the renderer recognizes (Carlito or Calibri). Without one the
  renderer falls back to Helvetica; the PDF still renders, so this is a warning, not
  a blocker.

## 1. Install, configure, and create a profile

```bash
make install
cp .env.example .env          # fill base URLs, keys, and provider:model chains
mkdir -p profile/software-engineer
cp profile/master.example.json profile/software-engineer/master.json
cp profile/blocklist.example.txt profile/software-engineer/blocklist.txt
```

Observe: `uv sync` completes; `.env` and `profile/software-engineer/` exist locally;
`git status` shows none of them (all are ignored). `GET /api/profiles` will list only
`software-engineer` — the committed examples are flat files, not profiles.

## 2. Gates

```bash
make check
```

Observe: ruff passes, the backend test suite runs and passes, the committed-data
check passes, and the build step compiles `backend/src`. `make check` must no longer
print the "pytest not installed" skip.

## 3. Deterministic path, no model

```bash
make test-backend
```

Observe: the fallback tests produce a selection from pre-rank scores alone and render
a one-page PDF without any network call. This proves the constitution's
graceful-degradation rule independently of any provider.

## 4. CLI tailoring with the fake provider

```bash
LLM_PROVIDER=fake PYTHONPATH=backend/src \
  uv run python -m cvtailor.cli tailor --profile software-engineer \
  --posting backend/tests/fixtures/posting-backend.txt --non-interactive --json
```

Observe: one JSON object on stdout with `run_id`, `profile` equal to
`software-engineer`, `pages` equal to `1`, `fallback_used` false, and absolute
`pdf_path` and `report_path`. Then:

```bash
ls -l data/runs/<run_id>/
```

Observe: `run.json`, `digest.json`, `analysis.json`, `selection.json`, `cv.pdf`,
`report.md`, and `posting.txt` exist. `run.json` records the profile slug.

## 5. Corpus

```bash
wc -l data/corpus.jsonl
```

Run step 4 again with the same posting.

Observe: the line count does not change. Run it with a different posting and the
count grows by one. `tail -1 data/corpus.jsonl` shows the digest, the hash, the date,
and the detected language — but no posting text.

## 6. Report contents and redaction

Open `data/runs/<run_id>/report.md` and the JSON from step 4.

Observe: the report lists the digest, section counts, gaps, coverage, red flags,
models with `admitted: false`, retries, fallback status, layout warnings, and the
checklist. The JSON contains no posting text and no API key.

## 7. Re-render from an origin

```bash
PYTHONPATH=backend/src uv run python -m cvtailor.cli render \
  --profile software-engineer --origin <run_id> \
  --selection data/runs/<run_id>/selection.json --json
```

Observe: a new run id, `origin_run_id` equal to the origin, a fresh `cv.pdf`, and the
origin's files unchanged. Remove one bullet from the selection first and confirm the
new PDF drops it. No model call is made; `llm_log.jsonl` gains no entry.

## 8. Failure paths

- **Blocklist**: add a term that appears in a selected bullet to
  `profile/software-engineer/blocklist.txt`, then re-run step 7. Observe exit code
  `4`, no new run directory, and a message naming item ids rather than the term.
- **Blocklist absent**: delete the file and re-run step 7. Observe the render
  succeeds — a missing blocklist means nothing is blocked, by design.
- **Overflow**: render the worst-case fixture profile with every bullet of every role
  selected. Observe exit code `6` and a message with the section counts to cut.
- **Unknown profile**: run step 4 with `--profile missing`. Observe exit code `9`.
- **Invalid id**: edit `selection.json` to an id absent from the master. Observe exit
  code `3` and a validation message naming the id.

## 9. HTTP API

```bash
PYTHONPATH=backend/src uv run uvicorn cvtailor.api.app:app --host 127.0.0.1 --port 8000
```

In another shell:

```bash
curl -s http://127.0.0.1:8000/api/profiles
curl -s http://127.0.0.1:8000/api/settings
curl -s -X POST http://127.0.0.1:8000/api/jobs/analyze \
  -H 'content-type: application/json' \
  -d '{"posting":"Backend engineer with Python and PostgreSQL."}'
curl -s http://127.0.0.1:8000/api/runs | head -c 400
```

Observe: profiles come back in slug order; settings report `api_key_set` as a
boolean, the chains with `admitted: false`, and `admission.evaluated` false; analyze
returns the seven digest fields plus `corpus_appended`; the run list includes the
runs from steps 4 and 7 with their profile slugs. Then request `cv.pdf` and
`report.md` for a run and confirm the content types.

## 10. Contract drift

```bash
make check-openapi
```

Observe: the target regenerates `backend/openapi.json` to a temporary file and
reports no difference. Editing a schema field without regenerating makes the target
fail.

## 11. Frontend (after the ingestion spec)

```bash
cd frontend && npm install && npm run dev
```

Observe: the tailoring page shows the profile selector in slug order, accepts a
posting, shows the analysis, then the selection editor, warnings, gaps, page count,
and the PDF preview. Edits re-render through `POST /api/render` with the origin and
without a new analysis. The history page lists CLI-created runs and reopens one. The
settings page shows key presence and admission state only. The browser never receives
posting text after submission.

## 12. Real provider smoke

With a real key in `.env` and a chain configured:

```bash
PYTHONPATH=backend/src uv run python -m cvtailor.cli tailor \
  --profile software-engineer --posting backend/tests/fixtures/posting-backend.txt \
  --non-interactive
```

Observe: a one-page PDF whose selection targets the posting, and a report that names
the model with `admitted: false`. The `model_unadmitted` warning appears in the
report and in the CLI summary. This is expected until the evaluation follow-up
admits a model.

## Checklist

- [ ] `make check` green, with the test target actually running tests.
- [ ] Fallback produces a valid one-page CV with no model call.
- [ ] Tailor run writes all seven artifacts, records the profile, and renders one page.
- [ ] Corpus grows once per unique posting and holds no posting text.
- [ ] Report carries gaps, coverage, red flags, models with admission state, warnings,
      checklist.
- [ ] Re-render creates a derived run and leaves the origin intact.
- [ ] Blocklist, missing blocklist, overflow, unknown profile, and invalid-id paths
      behave as documented.
- [ ] No response, log, or artifact copy contains the posting or the key.
- [ ] API and CLI produce interchangeable runs, both listing profiles in slug order.
- [ ] `make check-openapi` detects drift.
