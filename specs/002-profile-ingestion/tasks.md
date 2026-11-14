---
description: "Task list for 002-profile-ingestion"
---

# Tasks: Profile Ingestion

**Input**: Design documents from `/specs/002-profile-ingestion/`

**Prerequisites**: plan.md, spec.md (v2), research.md, data-model.md, contracts/api.md, contracts/cli.md, quickstart.md, `.specify/memory/constitution.md` (v2.2.0)

**Prerequisite feature**: `001-cv-tailor-v1-mvp` supplies the LLM layer, the profile
storage, the API app, and the CLI entry point. No task here re-implements them.

**Tests**: Required. The spec's Testing Decisions and constitution v2.2.0 make tests
mandatory, including failure paths.

**Organization**: Phases follow the plan's delivery slices (I1–I7), each with a "Done
when" condition and demonstrable on its own. The spec's 53 stories are grouped into
eight story labels; each task carries the label of the group it serves.

| Story | Spec stories | Coverage |
| --- | --- | --- |
| US1 | Upload and sources (1–8) | extraction, file limits, partial acceptance |
| US2 | Draft and quotes (9–16) | blocks, quotes, verification, draft display |
| US3 | Approval (17–25) | decisions, bulk approve, commit |
| US4 | Creating and updating a profile (26–32) | merge, ids, duplicates, ordering |
| US5 | Bilingual items (33–36) | both variants, translated marking |
| US6 | Privacy and safety (37–41) | no source file, no logs, expiry |
| US7 | Command line (42–45) | ingest, show, review |
| US8 | Failures (46–53) | model, text, limits, async state |

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: which story group the task serves
- Every task names an exact file path

## Path Conventions

- Backend: `backend/src/cvtailor/`, tests in `backend/tests/`
- Drafts: `data/ingestions/<id>/` (git-ignored)
- Profiles: `profile/<slug>/master.json`

---

## Phase 1: Setup

**Purpose**: Dependencies the extractor needs and fixtures every slice reuses.

- [ ] T001 Add `pypdf`, `python-docx`, and `python-multipart` with `uv add` in `pyproject.toml`
- [ ] T002 [P] Create ingestion fixtures — a text-layer PDF, a DOCX, a scanned PDF, a legacy `.doc`, and a bullet-only PDF — in `backend/tests/fixtures/ingestion/`
- [ ] T003 [P] Add a fixture that yields two temporary roots and a fake model into `backend/tests/conftest.py`

**Checkpoint**: `make check` still green with the new dependencies installed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extraction, normalization, draft storage, and the section prompts.

**⚠️ CRITICAL**: no slice starts until this phase completes.

- [ ] T004 [P] [US1] Implement PDF extraction to blocks with page indexes in `backend/src/cvtailor/core/extraction.py`; a file under 200 extractable characters is reported as having no text layer
- [ ] T005 [P] [US1] Implement DOCX extraction over paragraphs and table cells with paragraph indexes in `backend/src/cvtailor/core/extraction.py`
- [ ] T006 [P] [US2] Implement the normalizer in `backend/src/cvtailor/core/quotes.py`: Unicode NFC, hyphen-then-linebreak join, whitespace collapse, curly quote and dash unification, case-sensitive comparison
- [ ] T007 [P] [US2] Implement quote verification returning `verified`, `block_index`, `offset`, and a reason, in `backend/src/cvtailor/core/quotes.py`
- [ ] T008 [P] [US5] Implement the draft and item models in `backend/src/cvtailor/core/ingestion.py`: bilingual `fields`, `source_language`, `translated_variant`, `source_text`, `verification`, `duplicate`, `status`, and the `state` enum from the data model
- [ ] T009 [US6] Implement draft persistence in `backend/src/cvtailor/storage/drafts.py`: atomic write of `draft.json` and `blocks.json`, read, delete, and the seven-day sweep
- [ ] T010 [P] [US2] Add the ingestion prompt and the per-section schema constraint in `backend/src/cvtailor/agents/prompts.py`
- [ ] T011 [US2] Implement one section call returning items with quotes and translated variants in `backend/src/cvtailor/agents/ingest.py`
- [ ] T012 [P] [US1] Add unit tests for extraction, including the no-text-layer case and one corrupt file, in `backend/tests/unit/test_extraction.py`
- [ ] T013 [P] [US2] Add unit tests for normalization and verification in `backend/tests/unit/test_quotes.py`, covering exact match, whitespace, curly quotes, dashes, NFC, hyphenated line breaks, case sensitivity, and a non-contiguous quote
- [ ] T014 [P] [US6] Add storage tests for atomic write, read, delete, and sweep in `backend/tests/unit/test_drafts.py`

**Checkpoint**: extraction and verification are green in isolation, with no model and no server.

---

## Phase 3: Slice I1 — Upload a PDF and read its blocks (US1, US2, US6)

**Goal**: a create request returns a draft id at once, and the draft exposes extracted blocks.

**Independent Test**: quickstart steps 1–2 pass on a text-layer PDF.

- [ ] T015 [US1] Add the multipart create route returning `202` with `state: processing` in `backend/src/cvtailor/api/routes.py`
- [ ] T016 [US1] Enforce the limits in `backend/src/cvtailor/api/schemas.py`: 10 MB per file, 5 files, 200,000 characters total, and skip a file under 200 characters with a named warning
- [ ] T017 [US2] Add the draft read route returning items, blocks, section status, and readiness in `backend/src/cvtailor/api/routes.py`
- [ ] T018 [US6] Add the discard route returning `204` in `backend/src/cvtailor/api/routes.py`
- [ ] T019 [US7] Add `ingest show DRAFT_ID` in `backend/src/cvtailor/cli.py`
- [ ] T020 [P] [US1] Add contract tests for create, read, discard, and the four rejection codes in `backend/tests/contract/test_ingest_upload.py`
- [ ] T021 [P] [US1] Add a test proving the uploaded file is absent from disk and from every response in `backend/tests/contract/test_ingest_privacy.py`

**Checkpoint**: quickstart 1–2 pass; commit.

---

## Phase 4: Slice I2 — Quotes and the first section (US2, US5, US8)

**Goal**: one section is proposed with verified quotes and a marked translation.

**Independent Test**: a faithful quote verifies with block and offset; an invented one is `unverified` and unapprovable.

- [ ] T022 [US2] Wire the experience section call into the draft build in `backend/src/cvtailor/agents/ingest.py`
- [ ] T023 [US5] Attach the translated variant, its exact `source_text`, and the `number_changed`/`entity_changed` warnings in `backend/src/cvtailor/core/ingestion.py`
- [ ] T024 [US2] Record verification results and mark unverified items in `backend/src/cvtailor/core/ingestion.py`
- [ ] T025 [P] [US2] Add an integration test where a fake proposes one faithful and one invented quote in `backend/tests/integration/test_ingest_quotes.py`
- [ ] T026 [P] [US8] Add a test proving an unverified item cannot be approved in `backend/tests/integration/test_ingest_refusals.py`

**Checkpoint**: the quote guarantee holds end to end for one section.

---

## Phase 5: Slice I3 — All sections, async, and retry (US8, US7)

**Goal**: eight sections run in the background with partial success and per-section retry.

**Independent Test**: a failing section leaves a usable draft; polling shows sections settle.

- [ ] T027 [US8] Run the sections on one background thread per draft in `backend/src/cvtailor/core/ingestion.py`, updating `state` to `complete`, `failed`, or `stalled`
- [ ] T028 [US8] Enforce the budget in `backend/src/cvtailor/agents/ingest.py`: 60 seconds per call, two retries per section, 600 seconds per draft, with `budget_exhausted` on the sections not reached
- [ ] T029 [US8] Implement the retry-section route in `backend/src/cvtailor/api/routes.py`, refusing a successful section with `section_not_failed`
- [ ] T030 [US7] Add `ingest review` with `retry SECTION` in `backend/src/cvtailor/cli.py`
- [ ] T031 [P] [US8] Add a test where one section fails and the draft still completes in `backend/tests/integration/test_ingest_partial.py`
- [ ] T032 [P] [US8] Add tests for the retry path, the all-sections-failed state, and the stall transition in `backend/tests/integration/test_ingest_retry.py`
- [ ] T033 [P] [US8] Add a test asserting the create request returns before the sections settle in `backend/tests/contract/test_ingest_async.py`

**Checkpoint**: quickstart 9 passes; commit.

---

## Phase 6: Slice I4 — Decisions, bilingual review, readiness (US3, US5)

**Goal**: the user decides each item once, seeing both variants, and readiness updates.

**Independent Test**: approve, reject, edit, and bulk approve behave as specified; readiness lists what is missing.

- [ ] T034 [US3] Implement the decision route for `approve`, `reject`, and `edit` in `backend/src/cvtailor/api/routes.py`
- [ ] T035 [US3] Implement `approve-verified` restricted to `pending`, verified, non-duplicate items in `backend/src/cvtailor/api/routes.py`
- [ ] T036 [US3] Implement readiness with the renderer's rule set — one role option, one lead summary, one role with bullets — in `backend/src/cvtailor/core/ingestion.py`
- [ ] T037 [US5] Mark edited items `user_edited` and never re-translate silently in `backend/src/cvtailor/core/ingestion.py`
- [ ] T038 [US3] Add decision actions and counts to `ingest review` in `backend/src/cvtailor/cli.py`
- [ ] T039 [P] [US3] Add tests for approve, reject, edit, bulk approve exclusions, and reversibility in `backend/tests/integration/test_ingest_decisions.py`
- [ ] T040 [P] [US5] Add a test that one decision covers both variants and shows the source text in `backend/tests/integration/test_ingest_bilingual.py`

**Checkpoint**: quickstart 3 and 10 pass; commit.

---

## Phase 7: Slice I5 — Commit (US3, US4)

**Goal**: approved items reach the profile with ids and a backup, and an unrenderable master is refused.

**Independent Test**: a new profile renders; an incomplete one is refused and the draft survives.

- [ ] T041 [US4] Implement the commit route writing into a new or existing profile in `backend/src/cvtailor/api/routes.py`
- [ ] T042 [US4] Generate readable, unique ids at commit and append without touching existing items in `backend/src/cvtailor/storage/profiles.py`
- [ ] T043 [US4] Write the timestamped backup before the master in `backend/src/cvtailor/storage/profiles.py`
- [ ] T044 [US3] Refuse a master that would not render with `master_not_renderable` and the missing list in `backend/src/cvtailor/core/ingestion.py`
- [ ] T045 [US3] Return additive counts with `skipped_breakdown` in `backend/src/cvtailor/api/routes.py`
- [ ] T046 [US7] Add `--decisions FILE` and `commit` to `backend/src/cvtailor/cli.py`, with no auto-approval path
- [ ] T047 [P] [US4] Add tests for new-profile creation, append-only merge, backup, and id uniqueness in `backend/tests/integration/test_ingest_commit.py`
- [ ] T048 [P] [US3] Add tests for the renderability refusal and the additive counts in `backend/tests/integration/test_ingest_commit_refusal.py`

**Checkpoint**: quickstart 4–6 pass; commit.

---

## Phase 8: Slice I6 — Duplicates, person, translation rule (US4, US5)

**Goal**: re-uploads do not duplicate, contact details are checked in code, and no translation exists without its source.

**Independent Test**: the same bullet under two roles is accepted; the same CV twice is not duplicated.

- [ ] T049 [US4] Implement parent-scoped duplicate detection by normalized text in `backend/src/cvtailor/core/ingestion.py`
- [ ] T050 [P] [US5] Implement the person checks — equal phone digits, name and email present in the text, location variants carrying source text — in `backend/src/cvtailor/core/ingestion.py`
- [ ] T051 [P] [US4] Add tests for duplicate scope and the same-text-different-role case in `backend/tests/integration/test_ingest_duplicates.py`
- [ ] T052 [P] [US5] Add tests for the person item, including mismatched phone digits and a missing email in `backend/tests/integration/test_ingest_person.py`

**Checkpoint**: quickstart 8 passes; commit.

---

## Phase 9: Slice I7 — CLI surface (US7, US8)

**Goal**: the terminal covers the whole flow with stable exit codes.

- [ ] T053 [US7] Add `ingest` polling with per-section progress lines in `backend/src/cvtailor/cli.py`
- [ ] T054 [US7] Implement the review loop actions — `approve`, `reject`, `edit`, `approve-verified`, `retry`, `next`, `prev`, `show`, `commit`, `discard`, `quit` — in `backend/src/cvtailor/cli.py`
- [ ] T055 [US8] Map the documented exit codes, including the all-files-bad cases, in `backend/src/cvtailor/cli.py`
- [ ] T056 [P] [US7] Add process-boundary tests for the non-interactive JSON object and the exit codes in `backend/tests/integration/test_ingest_cli.py`

**Checkpoint**: quickstart 1–4 and 7 pass from the terminal; commit.

---

## Phase 10: Polish & Cross-Cutting Concerns

- [ ] T057 [P] Add a privacy test proving no key, file name, or file bytes reach logs or responses in `backend/tests/contract/test_ingest_redaction.py`
- [ ] T058 [P] Add the seven-day sweep test with a controlled clock in `backend/tests/unit/test_drafts_sweep.py`
- [ ] T059 Run the full `quickstart.md` checklist and record the result
- [ ] T060 [P] Document the ingestion flow and the bilingual rule in `docs/ingestion.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Setup; blocks every slice.
- **I1 (Phase 3)**: depends on Foundational.
- **I2 (Phase 4)**: depends on I1 — quotes need blocks.
- **I3 (Phase 5)**: depends on I2 — the background runner needs a section call.
- **I4 (Phase 6)**: depends on I3 — decisions need items from every section.
- **I5 (Phase 7)**: depends on I4 — commit needs readiness and approved items.
- **I6 (Phase 8)**: depends on I5 — duplicates and person checks run against a real master.
- **I7 (Phase 9)**: depends on I5 and I6 — the CLI completes the flow.
- **Polish (Phase 10)**: depends on the closed slices it documents.

### Story Dependencies

- US1 and US6 come first: extraction, limits, and draft lifetime unblock everything.
- US2 depends on US1; US5 depends on US2 and US3.
- US3 depends on US2; US4 depends on US3.
- US7 and US8 are adapters over a service that must exist.

### Within Each Slice

- Tests marked [P] can be written in parallel with each other.
- Pure functions before routes; routes before CLI.
- Each slice closes with its "Done when" from `plan.md` and a commit.

### Parallel Opportunities

- Setup: T002 and T003.
- Foundational: T004–T010 touch different files; T012–T014 follow their modules.
- I1: T020 and T021.
- I3: T031, T032, and T033.
- I4: T039 and T040.
- I5: T047 and T048.
- I8: T051 and T052.

---

## Parallel Example: Foundational

```bash
# Extraction, verification, models, and prompts are separate files:
Task: "Implement PDF extraction in backend/src/cvtailor/core/extraction.py"
Task: "Implement quote normalization in backend/src/cvtailor/core/quotes.py"
Task: "Implement the draft models in backend/src/cvtailor/core/ingestion.py"
Task: "Add the ingestion prompt in backend/src/cvtailor/agents/prompts.py"
```

---

## Implementation Strategy

### MVP First

The first useful increment is **I1**: a draft built from a PDF, readable with its
blocks and section status. I2 is the first increment that proves the guarantee.

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (I1), run quickstart 1–2, commit.
3. Continue slice by slice; each closes with its "Done when" and a commit.

### Incremental Delivery

I1 → I2 → I3 → I4 → I5 → I6 → I7. The frontend screen for ingestion belongs to 001's
final slice and consumes I4–I5.

### Commit Discipline

Constitution v2.2.0 requires one commit per completed task. A task is not done until
it is committed.

---

## Notes

- [P] marks different files with no dependency on an incomplete task.
- [USx] maps the task to a story group in the table above.
- Tests are required by the spec; write them first inside each slice.
- Never store the uploaded file, and never echo it in a response or a log.
- The model proposes; code verifies; the user decides.
