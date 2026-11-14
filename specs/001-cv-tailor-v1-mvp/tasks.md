---
description: "Task list for 001-cv-tailor-v1-mvp"
---

# Tasks: CV Tailor v1 MVP

**Input**: Design documents from `/specs/001-cv-tailor-v1-mvp/`

**Prerequisites**: plan.md, spec.md (v2), research.md, data-model.md, contracts/api.md, contracts/cli.md, quickstart.md, `.specify/memory/constitution.md` (v2.1.0)

**Tests**: Required. The spec's Testing Decisions and constitution v2.1.0 make tests mandatory, including failure paths.

**Organization**: Task phases follow the plan's delivery slices (S1–S6), because each
slice is the smallest independently testable increment and carries a "Done when"
condition. The spec's 80 user stories are grouped into nine story labels (US1–US9);
each task carries the label of the story group it serves.

| Story | Spec stories | Coverage |
| --- | --- | --- |
| US1 | Analyze a posting (1–10) | digest, detection, normalization |
| US2 | Tailor a selection (11–24) | pre-rank, model picks, retries, fallback |
| US3 | Render the CV (25–34) | one page, warnings, blocklist, PDF |
| US4 | Review the result (35–42) | report, gaps, coverage, red flags |
| US5 | Adjust and re-render (43–51) | derived runs, no model call |
| US6 | Manage runs (52–55) | listing, reopening, artifacts |
| US7 | Use the command line (56–64) | CLI adapter |
| US8 | Configure and operate (65–72) | chains, timeouts, security, OpenAPI |
| US9 | Profiles and corpus (73–80) | profile listing, per-profile blocklist, corpus |

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: which story group the task serves
- Every task names the exact file path

## Path Conventions

- Backend: `backend/src/cvtailor/`, tests in `backend/tests/`
- Frontend: `frontend/src/`, tests in `frontend/tests/`
- Data: `profile/<slug>/`, `data/runs/<id>/`, `data/corpus.jsonl`
- `PYTHONPATH=backend/src` is set by the Makefile; pytest uses `pythonpath` in `pyproject.toml`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependencies, test runner, environment, and the gates the backend can run today.

- [ ] T001 Add runtime dependencies with `uv add fastapi uvicorn pydantic` in `pyproject.toml`
- [ ] T002 [P] Add development dependencies with `uv add --dev pytest httpx mypy` in `pyproject.toml`
- [ ] T003 [P] Configure pytest with `testpaths = ["backend/tests"]` and `pythonpath = ["backend/src"]` in `pyproject.toml`
- [ ] T004 [P] Configure mypy for `backend/src` with `ignore_missing_imports` for `reportlab` in `pyproject.toml`
- [ ] T005 [P] Create `.env.example` documenting `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY`, `ANALYZE_CHAIN`, `TAILOR_CHAIN`, `CALL_TIMEOUT_S`, `RUN_BUDGET_S`, `FRONTEND_ORIGIN` with no values
- [ ] T006 [P] Extend `.gitignore` with `profile/*/master.json` and `profile/*/master.json.bak.*`
- [ ] T007 Rewrite the `check-committed-data` target in `Makefile` to fail when any `profile/*/master.json` is tracked
- [ ] T008 [P] Create `backend/tests/conftest.py` with a temporary profile/data root fixture and a scripted fake `LLMClient` fixture

**Checkpoint**: `make check` runs pytest instead of skipping it.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Pure core, storage, and the fake model every slice needs.

**⚠️ CRITICAL**: no slice can start until this phase completes.

- [ ] T009 [P] [US5] Implement the selection model and the `pt-BR`/`en-US` to `pt`/`en` mapping in `backend/src/cvtailor/core/selection.py`
- [ ] T010 [P] [US2] Implement profile-scoped selection validation in `backend/src/cvtailor/core/validation.py`: unknown role, unknown summary, 1–4 summaries, 1–7 distinct bullets per role, lead-block-first, unknown skill, unknown project
- [ ] T011 [P] [US3] Implement per-profile blocklist loading and case-insensitive substring matching in `backend/src/cvtailor/core/blocklist.py`; a missing file is an empty list
- [ ] T012 [P] [US3] Implement page-fit evaluation in `backend/src/cvtailor/core/layout.py`: `pages > 1` becomes `page_overflow` with section counts; `bullet_cap` produces `bullets_trimmed` naming the dropped ids; `font_scale < 1.0` produces `font_scaled`
- [ ] T013 [P] [US9] Implement root resolution for `profile/`, `data/runs/`, `data/corpus.jsonl` in `backend/src/cvtailor/storage/paths.py`, overridable by environment for tests
- [ ] T014 [P] [US9] Implement profile listing in slug order, master loading, and save with a timestamped backup in `backend/src/cvtailor/storage/profiles.py`
- [ ] T015 [P] [US6] Implement run creation in `backend/src/cvtailor/storage/runs.py`: `YYYYMMDDTHHMMSSZ-xxxx` ids, `.tmp-<id>` then rename, listing that skips `.tmp-*`, and run reading
- [ ] T016 [P] [US1] Implement the append-only corpus in `backend/src/cvtailor/storage/corpus.py`, idempotent on `sha256` of the normalized posting text
- [ ] T017 [P] [US8] Implement the dependency-free `LLMClient` protocol, JSON extraction from noisy output, and bounded retries in `backend/src/cvtailor/llm/client.py`
- [ ] T018 [P] [US8] Implement the scripted fake provider in `backend/src/cvtailor/llm/fake.py`, selected by `LLM_PROVIDER=fake`
- [ ] T019 [P] [US8] Implement `provider:model` chain and limit resolution in `backend/src/cvtailor/llm/config.py`
- [ ] T020 [P] [US1] Write delimited prompt templates with the ignore-embedded-instructions rule in `backend/src/cvtailor/agents/prompts.py`
- [ ] T021 [US1] Implement the analyze step in `backend/src/cvtailor/agents/analyze.py`, returning a digest constrained to the contract fields
- [ ] T022 [P] [US2] Add unit tests for selection, validation, blocklist, and layout in `backend/tests/unit/test_selection.py`, `test_validation.py`, `test_blocklist.py`, `test_layout.py`
- [ ] T023 [P] [US9] Add storage tests with temporary roots in `backend/tests/unit/test_storage_profiles.py`, `test_storage_runs.py`, `test_storage_corpus.py`
- [ ] T024 [P] [US8] Add LLM layer tests against the fake provider in `backend/tests/unit/test_llm_client.py`

**Checkpoint**: core and storage are green in isolation; no network, no real keys.

---

## Phase 3: Slice S1 — Complete run with the fake provider (US1, US3, US4, US5, US7, US9)

**Goal**: `tailor --profile <slug>` produces a full run directory and a one-page PDF with no network.

**Independent Test**: quickstart steps 4–8 pass with `LLM_PROVIDER=fake`.

- [ ] T025 [US1] Implement the application service in `backend/src/cvtailor/service.py` (analyze, validate, blocklist, render, report, persist)
- [ ] T026 [US1] Implement ordered step execution and run assembly in `backend/src/cvtailor/pipeline.py`, writing artifacts into the run directory
- [ ] T027 [US4] Implement the minimal report in `backend/src/cvtailor/core/report.py`: digest, section counts, models, layout warnings
- [ ] T028 [US7] Implement the `tailor` command with `--profile`, `--posting`/`--stdin`, `--non-interactive`, `--json` in `backend/src/cvtailor/cli.py`
- [ ] T029 [US1] Add an integration test for a full fake-provider run in `backend/tests/integration/test_tailor_fake.py`: seven artifacts, one-page PDF, profile recorded in `run.json`
- [ ] T030 [P] [US3] Add tests for `blocklist_hit`, missing blocklist, `page_overflow`, and `profile_not_found` in `backend/tests/integration/test_render_failures.py`
- [ ] T031 [P] [US9] Add a corpus test: one line per unique posting, none on repeat, no posting text in the record, in `backend/tests/integration/test_corpus.py`
- [ ] T032 [US7] Verify exit codes `3`, `4`, `6`, `9` from `contracts/cli.md` in `backend/tests/integration/test_cli_exit_codes.py`

**Checkpoint**: run quickstart 4–8. Commit.

---

## Phase 4: Slice S2 — Pre-rank and deterministic fallback (US2, US1)

**Goal**: selection comes from scoring when the model is wrong or absent.

**Independent Test**: a fake returning unknown ids still yields a valid one-page selection marked `fallback_used`.

- [ ] T033 [P] [US2] Implement tokenization and overlap scoring in `backend/src/cvtailor/core/keywords.py`
- [ ] T034 [P] [US2] Implement the curated alias table in `backend/src/cvtailor/core/aliases.py`
- [ ] T035 [P] [US1] Implement PT/EN function-word detection with a `pt-BR` tie-break in `backend/src/cvtailor/core/language.py`
- [ ] T036 [P] [US1] Implement digest normalization and skill verification in `backend/src/cvtailor/core/digest.py`: trim, drop empty, dedupe, level aliases, unsupported skills dropped, unknown fields discarded
- [ ] T037 [US2] Implement pre-rank scores for roles, summaries, bullets, skills, projects, and research in `backend/src/cvtailor/core/gaps.py`
- [ ] T038 [US2] Implement the deterministic fallback in `backend/src/cvtailor/core/fallback.py`: role by title overlap, lead block first, bullets by coverage, skills by overlap
- [ ] T039 [P] [US2] Add unit tests for keywords, aliases, language, digest, and fallback in `backend/tests/unit/test_keywords.py`, `test_digest.py`, `test_fallback.py`
- [ ] T040 [US2] Add an integration test where every model returns unknown ids and the fallback still renders, in `backend/tests/integration/test_fallback.py`

**Checkpoint**: the constitution's graceful-degradation rule is proved with no provider.

---

## Phase 5: Slice S3 — Real LLM layer (US8)

**Goal**: a configured `provider:model` chain runs against a real endpoint and marks unadmitted models.

**Independent Test**: with a chain in `.env`, `tailor` reaches a provider; a dead provider falls through; `model_unadmitted` appears.

- [ ] T041 [US8] Implement the stdlib `urllib` OpenAI-compatible adapter in `backend/src/cvtailor/llm/openai_compatible.py`
- [ ] T042 [US8] Implement the provider registry (base URL default and key variable per provider) in `backend/src/cvtailor/llm/registry.py`
- [ ] T043 [US8] Implement transient retries with backoff, per-call timeout, and the run budget in `backend/src/cvtailor/llm/client.py`
- [ ] T044 [US8] Record `admitted: false` per model in run metadata and surface `model_unadmitted` in the CLI summary in `backend/src/cvtailor/pipeline.py` and `backend/src/cvtailor/cli.py`
- [ ] T045 [P] [US8] Add adapter tests against a local stub HTTP server, never a real key, in `backend/tests/unit/test_openai_compatible.py`

**Checkpoint**: every run is marked unadmitted until the evaluation follow-up.

---

## Phase 6: Slice S4 — Report, gaps, and the rest of the CLI (US4, US5, US6, US7)

**Goal**: the report is complete and the CLI covers review without a browser.

**Independent Test**: `report.md` carries every required section; `render --origin` derives a run with no model call.

- [ ] T046 [US4] Complete gap computation in `backend/src/cvtailor/core/gaps.py`: gaps, coverage 0–1, red flags (`level_mismatch`, `uncovered_must_have`, `blocklist_adjacent`, `auto_fit_trimmed`, `model_unadmitted`), section counts, checklist
- [ ] T047 [US4] Complete `backend/src/cvtailor/core/report.py` with digest, counts, gaps, coverage, red flags, models, retries, fallback status, layout warnings, checklist
- [ ] T048 [US7] Implement `render --profile --origin --selection` in `backend/src/cvtailor/cli.py`, copying digest and analysis and never touching the origin
- [ ] T049 [US7] Implement `runs list`, `runs show`, and the `review` loop with `open`, `edit`, `rerender`, and `quit` in `backend/src/cvtailor/cli.py`
- [ ] T050 [US4] Add report-content tests in `backend/tests/integration/test_report.py`
- [ ] T051 [P] [US5] Add derived-run tests: origin untouched, `origin_run_id` set, no model call, in `backend/tests/integration/test_derived_run.py`

**Checkpoint**: quickstart 6–7 pass; the CLI is a complete product.

---

## Phase 7: Slice S5 — HTTP API and contract drift (US1, US4, US6, US8, US9)

**Goal**: the same service over HTTP with a checked-in contract.

**Independent Test**: contract tests pass for all ten routes; `make check-openapi` detects drift.

- [ ] T052 [US1] Implement request and response models in `backend/src/cvtailor/api/schemas.py`
- [ ] T053 [US1] Implement `{code, message}` serialization and status mapping in `backend/src/cvtailor/api/errors.py`
- [ ] T054 [US9] Implement the app factory with localhost binding and a single allowed CORS origin in `backend/src/cvtailor/api/app.py`
- [ ] T055 [US1] Implement the ten routes from `contracts/api.md` in `backend/src/cvtailor/api/routes.py`
- [ ] T056 [US8] Implement `python -m cvtailor.api.openapi_dump` writing `backend/openapi.json` in `backend/src/cvtailor/api/openapi_dump.py`
- [ ] T057 [US8] Add a `check-openapi` target comparing a regenerated schema to `backend/openapi.json` and wire it into `Makefile`
- [ ] T058 [US1] Add contract tests for all ten routes in `backend/tests/contract/test_api_contract.py`
- [ ] T059 [P] [US8] Add redaction tests: no posting text and no key in any response, and `/api/settings` returns booleans and admission state only, in `backend/tests/contract/test_redaction.py`
- [ ] T060 [P] [US9] Add profiles-endpoint tests: slug order, `has_blocklist`, `profile_not_found`, in `backend/tests/contract/test_profiles.py`

**Checkpoint**: quickstart 9–10 pass.

---

## Phase 8: Slice S6 — Frontend (US3, US4, US5, US6, US8)

**Blocked by**: `specs/002-profile-ingestion` — the first screen is uploading a CV, and the
ingestion UI arrives with that spec's API.

**Goal**: review and re-render in a browser.

**Independent Test**: a CLI-created run opens, re-renders without a model call, and the build passes.

- [ ] T061 [US8] Scaffold the frontend with Vite, React 19, TypeScript, Material UI 9, React Router, and TanStack Query in `frontend/package.json` and `frontend/vite.config.ts`
- [ ] T062 [US8] Generate `frontend/src/api/schema.d.ts` from `backend/openapi.json` with `openapi-typescript`
- [ ] T063 [US8] Implement the typed client wrapper in `frontend/src/api/client.ts`; no `fetch` in components
- [ ] T064 [US9] Implement the profile selector in slug order in `frontend/src/components/ProfileSelector.tsx`
- [ ] T065 [US3] Implement the tailoring page with posting input, analysis, selection editor, warnings, and PDF preview in `frontend/src/pages/TailoringPage.tsx`
- [ ] T066 [US5] Implement selection edits that post to `/api/render` with the origin and no analysis call in `frontend/src/viewmodels/useSelectionEditor.ts`
- [ ] T067 [US6] Implement the run history page in `frontend/src/pages/HistoryPage.tsx`
- [ ] T068 [US8] Implement the settings page showing key presence and admission state only in `frontend/src/pages/SettingsPage.tsx`
- [ ] T069 [P] [US3] Add component tests for the tailoring flow and the render-only edit path in `frontend/tests/tailoring.test.tsx`
- [ ] T070 [P] [US6] Add component tests for history reopening and error states in `frontend/tests/history.test.tsx`
- [ ] T071 [US8] Add `typecheck`, `test`, and `build` targets to `Makefile` and include them in `check` in `Makefile`
- [ ] T072 [US8] Amend `.opencode/rules/rules.md` to permit TanStack Query and React Router, as the constitution mandates, in the same change

**Checkpoint**: `npm run typecheck`, Vitest, and `npm run build` pass and join `make check`.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [ ] T073 [P] Add an import-graph test asserting `core` imports no FastAPI, LLM, storage, or service module in `backend/tests/unit/test_core_purity.py`
- [ ] T074 [P] Write decision notes for the profile layout, the corpus, and the admission rule in `docs/decisions.md`
- [ ] T075 Run the full `quickstart.md` checklist and record the result
- [ ] T076 Update `README.md` with install, profile setup, CLI usage, and the API start command

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Setup; blocks every slice.
- **S1 (Phase 3)**: depends on Foundational. Produces the first complete run.
- **S2 (Phase 4)**: depends on S1 — the fallback needs a pipeline that writes a run.
- **S3 (Phase 5)**: depends on S1; independent of S2.
- **S4 (Phase 6)**: depends on S1 and S2 — the report needs gaps.
- **S5 (Phase 7)**: depends on S4 — the contract exposes the full service.
- **S6 (Phase 8)**: depends on S5 **and on spec 002**.
- **Polish (Phase 9)**: depends on the closed slices it documents.

### Story Dependencies

- US1 and US9 appear early because profiles, digest, and corpus unblock everything.
- US2 (fallback) is independent of US8 (real providers); both depend on US1.
- US4 depends on US2 for gaps; US5 depends on US4 for the report.
- US6 and US7 are adapters over a service that must exist first.

### Within Each Slice

- Tests marked [P] can be written in parallel with each other.
- Models and pure functions before services.
- Services before CLI or API adapters.
- Each slice closes with its "Done when" from `plan.md` and a commit.

### Parallel Opportunities

- Setup: T002–T006 and T008 can run together.
- Foundational: T009–T021 touch different files and are largely parallel; T022–T024 follow their modules.
- S1: T030 and T031 can run in parallel once T025–T029 exist.
- S3: T045 is independent of T041–T044.
- S6: T069 and T070 are independent.

---

## Parallel Example: Foundational

```bash
# Core, storage, and LLM are separate files with no shared edits:
Task: "Implement selection model in backend/src/cvtailor/core/selection.py"
Task: "Implement per-profile blocklist in backend/src/cvtailor/core/blocklist.py"
Task: "Implement run storage in backend/src/cvtailor/storage/runs.py"
Task: "Implement the fake provider in backend/src/cvtailor/llm/fake.py"
```

---

## Implementation Strategy

### MVP First

The first shippable increment is **S1**: a complete run with the fake provider. It
proves storage, validation, blocklist, page-fit, report, and the CLI in one pass, and
every later slice extends it.

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (S1) and run quickstart 4–8.
3. Commit and stop for review.

### Incremental Delivery

S1 → S2 → S3 → S4 → S5, each closed by its "Done when" and a commit. S6 waits for
spec 002. No slice reopens a previous one; a need to do so is a discovery.

### Commit Discipline

Constitution v2.1.0 requires one commit per completed task. A task is not done until
it is committed, and each slice's final commit is the one that proves its "Done when".

---

## Notes

- [P] marks different files with no dependency on an incomplete task.
- [USx] maps the task to a story group in the table above.
- The spec's 80 stories are covered by slices; no story is left without a task.
- Tests are required by the spec; write them first inside each slice.
- Never print the posting or the key in CLI output, logs, or tests.
