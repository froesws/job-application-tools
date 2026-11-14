# Phase 0 Research: CV Tailor v1 MVP

Every unknown from the plan's Technical Context is resolved below. Each entry
records what changes in the code, not just a preference.

## 1. Runtime dependency versions on Python 3.14

**Decision**: Add `fastapi`, `uvicorn`, `pydantic`, `httpx`, `pytest`, `mypy`, and
`ruff` with `uv add`; the dry run on 2026-11-14 resolves to FastAPI 0.163.0,
uvicorn 0.54.0, Pydantic 2.14.3, httpx 0.28.1, pytest 9.2.0, mypy 2.4.1.

**Rationale**: `uv add` fails loudly when a wheel does not exist for CPython 3.14,
which is the real constraint. Pinning exact versions in the plan would rot before
implementation.

**Alternatives considered**: Hardcoding version pins here (rejected: not verified
by the lockfile); using `fastapi[standard]` (rejected: pulls `jinja2`, `email-validator`,
and a CLI we do not use).

## 2. Model call timeout and per-run budget

**Decision**: 60 seconds per model call, 300 seconds per run, both read from the
environment with those defaults. Exceeding either raises `model_unavailable`.

**Rationale**: Free providers answer slowly but predictably; 60 seconds covers a
cold start, and 300 seconds fits two validation retries across the two model steps
(analyze, tailor) plus one majority-voting repeat.

**Alternatives considered**: 30 seconds per call (cuts off free tiers mid-answer);
600 seconds per run (the user waits ten minutes for a failed run).

## 3. Posting text cap

**Decision**: 100,000 characters. Longer input fails with `invalid_posting` before
any model call.

**Rationale**: Real postings run 3,000 to 12,000 characters. The cap bounds prompt
size, token cost, and request memory without rejecting any realistic paste.

**Alternatives considered**: 20,000 characters (rejects postings with long benefit
sections); no cap (a pasted transcript can cost a full context window).

## 4. Blocklist file and matching

**Decision**: `profile/<slug>/blocklist.txt`, one term per line, `#` starts a
comment, case-insensitive substring match across every selected string. The
committed example is `profile/blocklist.example.txt`. A hit names the item id, never
the matched text. A missing file is an empty list, silently.

**Rationale**: Plain text the user can edit without tooling; substring matching
catches a client name embedded in a longer bullet. Naming the id keeps the client
name out of the error response, which is the point of the blocklist. The blocklist is
per profile because a name hidden for one career target may be acceptable for
another; the silent-empty rule is the accepted trade-off, so a new profile never
blocks the first render.

**Alternatives considered**: A global file (rejected: it forces the same redaction on
every profile); JSON list (harder to hand-edit); fail-closed on a missing file
(rejected: adds a setup step that blocks the first run).

## 5. Run id format

**Decision**: `YYYYMMDDTHHMMSSZ` in UTC, plus a four-character lowercase hex suffix
from `secrets.token_hex(2)`, for example `20261114T143012Z-9f3a`.

**Rationale**: The timestamp prefix keeps directory names sortable; the suffix
keeps two runs created in the same second distinct, which happens on manual
re-render.

**Alternatives considered**: ULID (needs a dependency); bare timestamps with a
collision counter (requires a directory scan before every write).

## 6. Checked-in OpenAPI schema and drift check

**Decision**: `backend/openapi.json`, written by
`python -m cvtailor.api.openapi_dump`. `make check-openapi` regenerates to a
temporary file and fails on a textual difference. The target joins `make check` in
the change that introduces the API.

**Rationale**: The backend owns the contract; the frontend consumes it. A
generated file inside `specs/` would mix documentation with build output.

**Alternatives considered**: `specs/001-cv-tailor-v1-mvp/contracts/openapi.json`
(rejected: generated artifacts do not belong in specs); no checked-in schema
(rejected: the constitution requires drift detection).

## 7. CLI framework

**Decision**: `argparse` from the standard library, matching the renderer's
existing `__main__` block. Entry point is `python -m cvtailor.cli`.

**Rationale**: No new dependency, no CLI framework to learn, and the command set is
small and fixed. `argparse` already covers subcommands, stdin, and exit codes.

**Alternatives considered**: `typer` (adds click and rich); `click` (adds a
dependency for behavior `argparse` already provides).

## 8. Frontend typed client

**Decision**: `openapi-typescript` as a dev dependency generates
`frontend/src/api/schema.d.ts`; `frontend/src/api/client.ts` is a small typed
wrapper over `fetch` that every viewmodel calls. Components never call `fetch`.

**Rationale**: The generated types keep the client honest against the OpenAPI
schema, while the wrapper stays readable and free of code generation magic. The
project rules already require a typed client layer.

**Alternatives considered**: `orval` (generates TanStack Query hooks too, but adds
a large generator and a second source of truth for query keys); hand-written types
(rejected: drifts from the schema, and the constitution requires generation).

## 9. Page overflow and trimming warnings without touching the renderer

**Decision**: `render_pdf` stays as it is. `core/layout.py` reads its result:
`pages > 1` becomes a `page_overflow` error carrying the section counts, and
`font_scale < 1.0` or `bullet_cap is not None` becomes a layout warning that names
the dropped bullet ids computed from the selection order and the applied cap.

**Rationale**: The constitution freezes the renderer's contract, and the function
already returns `pages`, `font_scale`, and `bullet_cap` — everything the warnings
need. Computing the cut from the selection is exact because the renderer applies
the cap to the requested order.

**Alternatives considered**: Changing `render_pdf` to return removed bullets
(rejected: changes a frozen contract and duplicates logic); re-parsing the PDF
(rejected: fragile and slow).

## 10. Output language mapping

**Decision**: The API accepts `pt-BR` and `en-US`. `core/selection.py` maps them to
the renderer's `pt` and `en` codes; the run stores both the requested language and
the render language used.

**Rationale**: The renderer's vocabulary predates the API and must not change. One
mapping function prevents `pt-BR` leaking into renderer calls.

**Alternatives considered**: Renaming the renderer's language keys (rejected:
breaks the frozen contract and every existing selection).

## 11. Skill alias table

**Decision**: `core/aliases.py` holds a curated `alias -> canonical` dict
(`js`, `ts`, `postgres`, `k8s`, `gcp`, `ml`, and similar). A digest skill is kept
when its normalized form, or a canonical form it aliases, appears as a token in the
posting text.

**Rationale**: The constitution requires every digest skill to be checked against
the posting or a documented alias. A small table in code is reviewable and needs no
data file.

**Alternatives considered**: Model-decided matching (violates Principle II); a
huge synonym database (unneeded for one user and one domain).

## 12. Posting language detection

**Decision**: `core/language.py` counts Portuguese and English function words
(`de`, `para`, `com`, `que`, `não` against `the`, `and`, `with`, `for`, `that`).
The higher count wins; a tie reports `pt-BR`. Detection is informational and never
changes the output language.

**Rationale**: Pure Python, no model, explainable in the digest. The tie rule matches
the product default.

**Alternatives considered**: A language-detection library (new dependency, model
download); the model's opinion (violates Principle II).

## 13. Majority voting

**Decision**: `TAILOR_VOTE_RUNS` is `1` by default and `3` when enabled. Each id is
kept when at least two of three runs select it; a per-id tie is broken by the
pre-rank score, then by master order.

**Rationale**: Majority voting is per-step configuration per the constitution, and
a deterministic tie-break keeps the result reproducible when a provider samples.

**Alternatives considered**: Requiring three of three (drops valid items whenever
one model call fails); averaging ranks (no stable meaning across models).

## 14. LLM transport stays dependency-free

**Decision**: `llm/openai_compatible.py` posts JSON to `<base_url>/chat/completions`
with `urllib.request` and reads `choices[0].message.content`. The client is
synchronous; FastAPI endpoints are declared with `def` so Starlette runs them in
its thread pool.

**Rationale**: The constitution requires `LLMClient` to stay dependency-free, which
rules out the `openai` SDK and an async HTTP client. Synchronous calls in the
thread pool keep the code readable without an event-loop bridge.

**Alternatives considered**: The `openai` SDK (heavy, version-churning); `httpx`
for provider calls (violates the dependency-free rule); `async def` endpoints
(needs an async client or `to_thread` wrappers for no gain at this scale).

## 15. Import path for a non-package project

**Decision**: Keep `[tool.uv] package = false`. Add
`[tool.pytest.ini_options] pythonpath = ["backend/src"]` and
`testpaths = ["backend/tests"]`. The CLI runs as
`PYTHONPATH=backend/src uv run python -m cvtailor.cli`.

**Rationale**: No packaging work, no editable install, and both entry points work
from the repository root. The Makefile carries the one environment variable.

**Alternatives considered**: Converting to an installable package (rejected for v1:
extra metadata and a build step for a tool that runs from the repo); a `conftest.py`
path hack (rejected: hidden behavior that `pythonpath` states explicitly).

## 16. Static type checking

**Decision**: `mypy` with `ignore_missing_imports` for `reportlab`, checking
`backend/src`. `make typecheck` runs it, and gains `tsc --noEmit` in the change
that adds the frontend.

**Rationale**: The constitution requires a type check before merge. mypy needs no
Node runtime and no extra toolchain.

**Alternatives considered**: `pyright` (equivalent, but pulls a Node package);
no Python type check (leaves a required gate unimplemented).

## 17. Atomic run writes

**Decision**: Each run is written to `data/runs/.tmp-<id>/`, then renamed to
`data/runs/<id>/` after the last artifact is flushed. Listing skips names starting
with `.tmp-`.

**Rationale**: The spec requires that an interrupted run leaves no readable half-run.
A single directory rename is atomic on the same filesystem.

**Alternatives considered**: A completion marker file inside the run (readable but
easy to miss); writing directly to the final path (leaves a half-run on crash).

## 18. Digest hash

**Decision**: `sha256` of the canonical JSON of the validated digest, recorded in
run metadata as `digest_hash`. Derived runs copy it from the base run.

**Rationale**: The spec requires run metadata to record a digest hash, and re-renders
must prove they reuse the same analysis.

**Alternatives considered**: Hashing the raw posting (leaks nothing but identifies
the posting, which is already stored); hashing the whole analysis (changes on notes
that do not affect the CV).

## 19. Profiles as directories

**Decision**: A profile is `profile/<slug>/{master.json,blocklist.txt}`. The slug is
both identity and display name; profiles are listed in slug order. The committed
example stays a flat file, `profile/master.example.json`, so the selector only sees
real directories.

**Rationale**: One source of truth per name. Renaming moves the directory, and every
run already records the slug it used. A flat example avoids a special case in both
the listing and the committed-data check.

**Alternatives considered**: A `name` field inside the master (two names that drift on
the first rename); human-readable directory names with spaces and accents (breaks on
case-insensitive filesystems and needs escaping in CLI and URLs).

## 20. Per-step provider and model

**Decision**: A chain entry is the string `provider:model`, for example
`openrouter:deepseek/deepseek-chat`. `llm/registry.py` maps a provider name to a
default base URL and the environment variable holding its key. Chains live in
`.env` as `ANALYZE_CHAIN` and `TAILOR_CHAIN`, comma-separated and tried in order.

**Rationale**: Switching a step from OpenAI to Gemini to DeepSeek becomes one line of
configuration, which is what the constitution requires. The registry keeps provider
details out of the call sites, so a new provider is one entry and a new model is
zero code.

**Alternatives considered**: One class per model id (duplicates transport and breaks
"replaceable without a code change"); provider-specific SDKs (extra dependencies and
violates the dependency-free rule).

## 21. Corpus append and idempotence

**Decision**: `data/corpus.jsonl`, one line per unique posting, keyed by
`sha256` of the normalized text (whitespace collapsed, lowercased). The line holds
the seven-field digest, the hash, the run date, and the detected language. A repeat
analysis appends nothing.

**Rationale**: The corpus is market data, so it must outlive run directories the user
cleans. Append-only JSONL needs no schema migration and can be read by any future
consumer. Normalizing before hashing makes the idempotence rule survive formatting
noise from copy and paste.

**Alternatives considered**: Deriving the corpus by scanning `data/runs/` (lost when
runs are deleted); SQLite (a database for tens of rows); storing the posting text
(privacy and size).

## 22. Unadmitted models

**Decision**: Every model record carries `admitted: boolean`, false until the
evaluation follow-up scores it. The mark appears in run metadata, the report as a
`model_unadmitted` red flag, the CLI summary, and `GET /api/settings`.

**Rationale**: The evaluation set needs the user's real master, which ingestion
delivers later. Blocking all real model use until then would freeze the product;
hiding the gap would let a weak model pass as evaluated. A visible flag keeps both
the product usable and the promise honest.

**Alternatives considered**: A hard gate until the eval set exists (blocks all real
use for weeks); no flag at all (the user cannot tell an evaluated model from a
guessed one).

## 23. No bare selection render

**Decision**: `POST /api/render` and `cli render` require an origin run. Every run
therefore has a digest and an analysis, copied from the origin.

**Rationale**: The constitution requires each run to persist a digest and an
analysis. A selection with no posting cannot satisfy the digest contract without
inventing fields. Deriving from an origin also gives manual edits a traceable source.

**Alternatives considered**: Synthesizing an empty digest (violates the digest
contract and pollutes the run list); dropping the run for bare renders (loses the
record of which selection produced a PDF).

## 24. Service modules at the package root

**Decision**: `cvtailor/service.py` and `cvtailor/pipeline.py` hold the shared
service. They are not a layer; `core` must not import them.

**Rationale**: The service calls both `core` and `llm`. Placing it in `core` breaks
purity, in `api` couples the CLI to the web layer, and in `agents` overloads the
prompt-builder layer. The constitution enumerates layers, not every module, and
`cli.py` already sits at the root.

**Alternatives considered**: A seventh `app/` layer (requires a constitutional
amendment for a composition root); injecting the client into `core` (still imports
the LLM protocol from `llm`).
