# Implementation Plan: CV Tailor v1 MVP

**Branch**: `001-cv-tailor-v1-mvp` | **Date**: 2026-11-14 | **Spec**: [spec.md](./spec.md) (v2)

**Input**: Feature specification from `/specs/001-cv-tailor-v1-mvp/spec.md`

## Summary

Build a local, single-user application that turns a pasted job posting into a
reviewable CV package for one of the user's named profiles: a validated job digest,
a selection drawn only from that profile's ids, a deterministic fallback when every
model fails, a one-page PDF from the existing renderer, and a separate report. Every
successful analysis also appends a record to a market corpus. One application
service serves both the HTTP API and the CLI. Models run marked `model_unadmitted`
until the evaluation follow-up lands; ingestion of existing CVs is a separate spec.

Delivery is vertical: each slice ends in something executable, and the first slice
already produces a complete run.

## Technical Context

**Language/Version**: Python 3.14.4 (backend, `.venv`); TypeScript with React 19
(frontend); Node 26.13 and npm 11.20 for frontend tooling.

**Primary Dependencies**: FastAPI 0.163.0, uvicorn 0.54.0, Pydantic 2.14.3,
ReportLab (installed). Frontend: React 19, Vite, Material UI 9 + Emotion, React
Router, TanStack Query, `openapi-typescript` for generated types. Development:
pytest 9.2.0, ruff 0.17.5, mypy 2.4.1, httpx 0.28.1, Vitest, Testing Library.
Versions confirmed with `uv pip install --dry-run` against CPython 3.14 on
2026-11-14; `uv add` is the authority.

**Storage**: Filesystem only. `profile/<slug>/master.json` and
`profile/<slug>/blocklist.txt` per profile, `data/runs/<id>/` per run, and
`data/corpus.jsonl` appended once per unique posting. No database.

**Testing**: pytest for the backend, driven at the HTTP API seam with a scripted
fake `LLMClient`; the renderer is tested directly as a pure function. Vitest with
Testing Library for the frontend, with the generated client mocked.

**Target Platform**: The user's local machine (Linux today; macOS and Windows font
paths already handled by the renderer). Backend binds to `127.0.0.1`; the frontend
runs in a modern browser.

**Project Type**: Web application (HTTP API + SPA) with a CLI adapter over the same
application service.

**Performance Goals**: A one-page PDF per run; render completes in under 2 seconds;
60-second timeout per model call; 300-second budget per run.

**Constraints**: One page is non-negotiable; a profile's blocklist hit blocks the
render; the posting text and the API key never appear in a response, a log, or the
browser; the posting text never enters the corpus; the backend accepts only the
frontend development origin; posting text is capped at 100,000 characters; the
deterministic fallback must produce a valid CV without any model call.

**Scale/Scope**: One user, a handful of profiles, ten API routes, one SPA with three
routes, tens of runs, one corpus line per unique posting.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
Evaluated against constitution v2.1.0.

| Gate | How the plan satisfies it | Verdict |
| --- | --- | --- |
| I. Master profile is the single source of facts | Selection carries ids only, resolved against the chosen profile's master; the validator rejects unknown ids and skills absent from that master; no model-generated text reaches the PDF | PASS |
| II. Code owns validation and deterministic decisions | `core/` holds language detection, pre-rank, keyword coverage, gaps, red flags, blocklist check, page-fit check, and the deterministic fallback as pure functions | PASS |
| III. Untrusted input, isolated secrets | Delimited prompts with an ignore-instructions rule; keys in `.env` read by the backend only; settings return booleans; localhost plus one allowed origin; posting cap; posting text never stored in the corpus; per-profile blocklist on every render | PASS |
| IV. Human review before artifacts leave | PDF preview, page count, warnings, models with admission state, gaps, and a checklist; report downloads separately; `/api/render` re-renders without a model call; every run records the profile used and can be reopened (re-render requires its ids to still exist, as v2.1.0 states) | PASS |
| V. Provider-agnostic LLM layer with graceful degradation | One dependency-free `LLMClient`; one OpenAI-compatible adapter plus a provider registry; `provider:model` chain entries in configuration; transient retries; bounded validation retries with errors fed back; deterministic fallback; unadmitted models marked on every surface | PASS |
| VI. Fixed pipeline and deliberate scope | Fixed step order behind `AgentStep`; no agent framework; new dependencies justified in Complexity Tracking | PASS |
| Renderer is the only PDF path | `core/render_pdf.py` is called with a validated selection and the profile's master; overflow and trimming are detected around it | PASS |
| Core stays pure | `core/` imports no FastAPI, LLM client, storage, or service module; a test asserts the import graph | PASS |
| Service sits above the layers | `cvtailor/service.py` and `cvtailor/pipeline.py` are package-root modules; no seventh layer | PASS |
| OpenAPI is the contract | Pydantic models generate `backend/openapi.json`, checked in; CI fails on drift | PASS |
| Frontend stack matches the constitution | React 19, TypeScript, Vite, Material UI 9, React Router, TanStack Query, generated types, Vitest, Testing Library | PASS |
| Corpus privacy | `data/corpus.jsonl` holds the digest, a posting hash, date, and detected language; never the posting text | PASS |
| No unresolved clarification | The unknowns are resolved in [research.md](./research.md) | PASS |

No gate fails.

**Post-design re-check** (after Phase 0 and Phase 1): still PASS.

- `data-model.md` adds `Profile` and `CorpusEntry` without letting either carry
  model-authored CV text.
- `contracts/api.md` requires a profile on tailor and render, requires an origin run
  on render, and keeps the posting and key out of every response.
- `contracts/cli.md` has no credential flag and requires `--profile` and `--origin`.
- `quickstart.md` validates the fallback, the derived run, the corpus, the failure
  codes, and the drift check.

## Project Structure

### Documentation (this feature)

```text
specs/001-cv-tailor-v1-mvp/
├── plan.md              # This file
├── research.md          # Phase 0 decisions
├── data-model.md        # Phase 1 entities and rules
├── quickstart.md        # Phase 1 validation scenarios
├── contracts/
│   ├── api.md           # HTTP contract
│   └── cli.md           # CLI contract
├── spec.md
└── tasks.md             # Phase 2 output, not created here
```

### Source Code (repository root)

```text
backend/
├── src/cvtailor/
│   ├── service.py            # TailorService shared by HTTP and CLI
│   ├── pipeline.py           # ordered AgentStep execution, run assembly
│   ├── cli.py                # argparse adapter over TailorService
│   ├── api/
│   │   ├── app.py            # FastAPI factory, CORS, localhost binding
│   │   ├── routes.py         # the ten endpoints
│   │   ├── schemas.py        # Pydantic request/response models
│   │   ├── errors.py         # {code, message} serialization, status mapping
│   │   └── openapi_dump.py   # writes backend/openapi.json
│   ├── core/
│   │   ├── render_pdf.py     # existing renderer, contract unchanged
│   │   ├── selection.py      # selection model, language mapping
│   │   ├── validation.py     # selection and digest validation
│   │   ├── language.py       # posting language detection
│   │   ├── keywords.py       # normalization, tokenizing, pre-rank scores
│   │   ├── aliases.py        # documented skill alias table
│   │   ├── gaps.py           # coverage, gaps, red flags, checklist
│   │   ├── fallback.py       # deterministic selection from pre-rank scores
│   │   ├── digest.py         # digest normalization and skill verification
│   │   ├── layout.py         # page-fit check and trimming warnings
│   │   ├── report.py         # report.md rendering
│   │   └── blocklist.py      # per-profile blocklist loading and matching
│   ├── llm/
│   │   ├── client.py         # LLMClient protocol, retries, JSON extraction
│   │   ├── openai_compatible.py  # stdlib urllib adapter
│   │   ├── registry.py       # provider -> base URL + key variable
│   │   ├── fake.py           # scripted provider for tests and demos
│   │   └── config.py         # chains, timeouts, budgets from environment
│   ├── agents/
│   │   ├── prompts.py        # delimited prompt templates
│   │   ├── analyze.py        # posting to digest step
│   │   └── tailor.py         # pre-ranked candidates to selection step
│   ├── storage/
│   │   ├── paths.py          # profile, data, run, corpus roots
│   │   ├── profiles.py       # list, load, save with timestamped backup
│   │   ├── runs.py           # atomic run writes, listing, reading
│   │   └── corpus.py         # append-only corpus, idempotent by hash
│   └── settings/
│       └── env.py            # .env loading, key-set booleans, limits
├── tests/
│   ├── unit/                 # core pure functions, renderer
│   ├── contract/             # API request/response contract
│   ├── integration/          # fake LLM end to end through the API
│   └── fixtures/             # masters, postings, selections, blocklists
└── openapi.json              # generated, checked in

frontend/
├── src/
│   ├── api/
│   │   ├── schema.d.ts       # generated from backend/openapi.json
│   │   └── client.ts         # typed fetch wrapper
│   ├── components/
│   ├── viewmodels/
│   ├── pages/                # tailoring, history, settings
│   └── main.tsx
└── tests/

profile/
├── master.example.json       # committed
├── blocklist.example.txt     # committed
└── <slug>/                   # git-ignored
    ├── master.json
    ├── master.json.bak.<ts>
    └── blocklist.txt
```

**Structure Decision**: Two top-level projects, `backend/` and `frontend/`, rooted
at the repository as the constitution fixes. The six backend layers stay as
enumerated; the shared application service and the CLI adapter sit at the package
root as `service.py`, `pipeline.py`, and `cli.py`, above the layers rather than
inside one. Tests live in `backend/tests/` so `make test-backend` needs no path
arguments. Profiles are directories under `profile/`; committed examples stay as
flat files so the selector only lists real profiles.

### Delivery Order

Each slice ends in a commit and has an explicit "Done when" condition, as the
constitution requires.

**S1 — Run end to end with the fake provider.**
Scope: `core/selection`, `core/validation`, `core/layout`, `core/blocklist`,
minimal `core/report`, `storage/{paths,profiles,runs,corpus}`,
`llm/{client,fake,config}`, `agents/{prompts,analyze}`, `service.py`,
`pipeline.py`, `cli.py` with `tailor`; `.gitignore` rules for
`profile/*/master.json` and `profile/*/master.json.bak.*`; `.env.example`; the
committed-data check rewritten to reject any tracked `profile/*/master.json`.
Done when: `tailor --profile <slug> --posting <fixture> --non-interactive` with
`LLM_PROVIDER=fake` writes `run.json`, `digest.json`, `analysis.json`,
`selection.json`, `cv.pdf`, `report.md`, and `posting.txt`; the PDF is one page; a
blocklist term blocks the render with `blocklist_hit`; a missing blocklist renders;
content that cannot fit fails with `page_overflow`; an unknown profile fails with
`profile_not_found`; `data/corpus.jsonl` gains exactly one line and a repeat adds
none; `make check` runs pytest instead of skipping it.

**S2 — Pre-rank, fallback, and digest hardening.**
Scope: `core/{keywords,aliases,language,digest,fallback}`, pre-rank half of
`core/gaps`.
Done when: a fake returning unknown ids still yields a valid one-page selection
built from pre-rank, recorded as `fallback_used`; language detection ties resolve
to `pt-BR`; aliases map `js` to `javascript`; unsupported, empty, and duplicate
digest skills are dropped; every pure function has tests for its failure path.

**S3 — Real LLM layer.**
Scope: `llm/openai_compatible`, `llm/registry`, retries with backoff, call timeout,
run budget, admission flag.
Done when: with `provider:model` chains in `.env`, analyze and tailor run against a
real provider; a dead provider falls through to the next chain entry; transient
429/5xx responses are retried; exceeding the run budget yields `model_unavailable`;
every run and CLI output marks the model `model_unadmitted`.

**S4 — Report, gaps, and the rest of the CLI.**
Scope: full `core/gaps`, full `core/report`, `cli.py` with `render`, `runs`,
`review`.
Done when: `report.md` carries digest, section counts, gaps, coverage, red flags,
models with admission state, retries, fallback status, layout warnings, and the
checklist; `render --profile --origin` creates a derived run with no model call and
leaves the base run untouched; `runs list`, `runs show`, and `review` work with the
documented exit codes.

**S5 — HTTP API and contract drift.**
Scope: `api/{app,routes,schemas,errors,openapi_dump}`, CORS, localhost binding.
Done when: contract tests at the API seam pass with the fake across all ten routes;
`backend/openapi.json` is checked in; `make check-openapi` passes and fails on
drift; no response contains posting text or the key; settings report key presence
and admission state only.

**The frontend is not a slice of this plan.** The shell, the five routes, the generated
client, and the frontend gates are specified in `specs/005-frontend`, which owns every
screen. This plan closes when S1 through S5 are done, the API contract is checked in, and
quickstart scenarios 1–10 pass from the CLI and `curl`.

## Complexity Tracking

| Item | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| `mypy` and `httpx` as development dependencies | The constitution requires a type check before merge, and FastAPI's test client needs `httpx`. | Skipping the type check leaves a required gate unimplemented; hand-rolling an HTTP test client reimplements Starlette's. |
| Frontend adds TanStack Query and React Router | The constitution mandates both. | `.opencode/rules/rules.md` forbids TanStack Query and must be amended in the same change that adds the frontend; the constitution supersedes the rules. The frontend itself is delivered by `specs/005-frontend`. |
| `service.py` and `pipeline.py` at the package root | The CLI and the HTTP API must share one pipeline that calls both `core/` and `llm/`. | Putting it in `core/` violates the purity rule; in `api/` it couples the CLI to the web layer; in `agents/` it overloads the prompt-builder layer. |
