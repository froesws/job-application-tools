---
description: "Task list for 003-model-admission"
---

# Tasks: Model Admission

**Input**: Design documents from `/specs/003-model-admission/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md, contracts/cli.md, quickstart.md, `.specify/memory/constitution.md` (v2.2.0)

**Prerequisite features**: `001-cv-tailor-v1-mvp` supplies the pipeline, the profile
storage, the API app, and the CLI. `002-profile-ingestion` supplies a
real profile. No task here re-implements them.

**Tests**: Required. The spec's Testing Decisions and constitution v2.2.0 make tests
mandatory, including failure paths.

**Organization**: Phases follow the plan's slices (E1–E6), each with a "Done when"
condition and demonstrable on its own. The spec's 37 stories are grouped into five story
labels; each task carries the label of the group it serves.

| Story | Spec stories | Coverage |
| --- | --- | --- |
| US1 | The evaluation set (1–8) | layout, loading, validation, version |
| US2 | Scoring a model (9–18) | outcomes, metrics, threshold, harness |
| US3 | Admission (19–25) | record, staleness, withdrawal, settings |
| US4 | Comparing and keeping trace (26–30) | archives, comparison, offline path |
| US5 | Where the screen lives (31–32) | the eval API the screen consumes |

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: which story group the task serves
- Every task names an exact file path

## Path Conventions

- Backend: `backend/src/cvtailor/`, tests in `backend/tests/`
- Eval data: `<data root>/eval/postings/`, `eval/results/`, `eval/admitted.json`

---

## Phase 1: Setup

**Purpose**: The fixture set and the temporary roots every slice reuses.

- [ ] T001 [P] Create an evaluation fixture — a manifest naming one profile plus ten posting files with known annotations — in `backend/tests/fixtures/eval/`
- [ ] T002 [P] Create the invalid variants of that fixture — nine postings, an unknown role id, an unknown bullet id, and a mismatched version — in `backend/tests/fixtures/eval/invalid/`
- [ ] T003 [P] Add a fixture giving a temporary eval root and a scripted model to `backend/tests/conftest.py`

**Checkpoint**: `make check` still green with the fixtures in place.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The dataset, the math, and the hashes every slice needs.

**⚠️ CRITICAL**: no slice starts until this phase completes.

- [ ] T004 [US1] Implement manifest and posting loading in `backend/src/cvtailor/core/evals.py`: exactly ten postings, one file each, in manifest order
- [ ] T005 [US1] Implement annotation validation against the profile in `backend/src/cvtailor/core/evals.py`: the role id and every must-include bullet id must exist, and all problems are reported together
- [ ] T006 [US1] Implement the set version hash over sorted posting hashes, expected role ids, must-include ids, and the profile slug in `backend/src/cvtailor/core/evals.py`
- [ ] T007 [US2] Implement the metrics — valid count, role agreement, mean recall dividing by the expected count — in `backend/src/cvtailor/core/evals.py`
- [ ] T008 [US2] Implement the threshold verdict — ten of ten valid, at least nine of ten role, recall at least 0.9 — in `backend/src/cvtailor/core/evals.py`
- [ ] T009 [US3] Implement the prompt hash and the referenced-text hash in `backend/src/cvtailor/core/evals.py`
- [ ] T010 [P] [US1] Add unit tests for loading and validation, including each invalid fixture, in `backend/tests/unit/test_evals_load.py`
- [ ] T011 [P] [US2] Add unit tests for the metrics and the threshold edges in `backend/tests/unit/test_evals_metrics.py`
- [ ] T012 [P] [US3] Add unit tests for the three hashes, including that re-saving identical content does not change them, in `backend/tests/unit/test_evals_hashes.py`

**Checkpoint**: the set loads and scores in isolation, with no model and no server.

---

## Phase 3: Slice E1 — The set, loaded and validated (US1)

**Goal**: the set can be inspected, and an invalid one is refused with a reason.

**Independent Test**: quickstart step 2 passes, including the three refusals.

- [ ] T013 [US1] Implement `eval status` showing the profile, the version, and the ten postings in `backend/src/cvtailor/cli.py`
- [ ] T014 [US1] Refuse a wrong count, a missing file, an unknown id, and a version mismatch with the offending item named, in `backend/src/cvtailor/core/evals.py`
- [ ] T015 [P] [US1] Add a process-boundary test for each refusal in `backend/tests/integration/test_eval_status_cli.py`

**Checkpoint**: quickstart 1–2 pass; commit.

---

## Phase 4: Slice E2 — Score one posting (US2)

**Goal**: one posting runs through the real pipeline with the model under test.

**Independent Test**: a scripted model produces a valid outcome; a failing one produces invalid; a timeout produces error.

- [ ] T016 [US2] Implement scoring one posting through the analyze and tailor steps with the fallback disabled in `backend/src/cvtailor/service.py`
- [ ] T017 [US2] Map the three outcomes — valid, invalid, error — and record retries and the error code in `backend/src/cvtailor/core/evals.py`
- [ ] T018 [P] [US2] Add tests for the three outcomes with a scripted model in `backend/tests/integration/test_eval_one_posting.py`

**Checkpoint**: one posting is scored and its outcome is inspectable; commit.

---

## Phase 5: Slice E3 — Run the set and archive (US2, US4)

**Goal**: ten postings scored in one command, with an archive and no side effects.

**Independent Test**: quickstart steps 3 and 5 pass.

- [ ] T019 [US4] Implement the run loop and the archive writer in `backend/src/cvtailor/storage/evals.py`, with a sanitized file name
- [ ] T020 [US2] Disable corpus writes on the evaluation path in `backend/src/cvtailor/service.py`
- [ ] T021 [US2] Implement majority mode — three runs, at least two valid, ids merged by majority — in `backend/src/cvtailor/service.py`
- [ ] T022 [US4] Implement `eval run` with `--model`, `--set`, `--majority`, and `--json`, exiting `0` on pass and `1` on fail, in `backend/src/cvtailor/cli.py`
- [ ] T023 [P] [US2] Add a test proving a provider error lowers the valid count and does not shrink the denominator, in `backend/tests/integration/test_eval_errors.py`
- [ ] T024 [P] [US4] Add a test proving the corpus and the master are byte-identical after a run, in `backend/tests/integration/test_eval_isolation.py`

**Checkpoint**: quickstart 3–5 pass; commit.

---

## Phase 6: Slice E4 — Admission (US3, US4)

**Goal**: a passing run can be admitted, and any change that invalidates it is detected.

**Independent Test**: quickstart steps 6–9 and 11 pass.

- [ ] T025 [US3] Implement the admission record and its storage in `backend/src/cvtailor/storage/evals.py`
- [ ] T026 [US3] Implement staleness detection with the three reasons in `backend/src/cvtailor/core/evals.py`
- [ ] T027 [US3] Implement `eval admit` and `eval withdraw` with the documented refusals in `backend/src/cvtailor/cli.py`
- [ ] T028 [US3] Report admission state and reason per chain entry for a requested profile in `backend/src/cvtailor/api/routes.py`
- [ ] T029 [US4] Implement `eval compare` over two archives in `backend/src/cvtailor/cli.py`
- [ ] T030 [P] [US3] Add tests for admitting, the three staleness reasons, and the untouched configuration in `backend/tests/integration/test_eval_admission.py`
- [ ] T031 [P] [US3] Add a contract test for the settings profile parameter and its default, in `backend/tests/contract/test_settings_admission.py`
- [ ] T032 [P] [US4] Add a test for comparing two archives, including the differing postings, in `backend/tests/integration/test_eval_compare.py`

**Checkpoint**: quickstart 6–9 and 11 pass; commit.

---

## Phase 7: Slice E5 — The offline path (US4)

**Goal**: the whole harness runs without a key, so CI can exercise it.

**Independent Test**: the run completes against the fake provider and archives a result.

- [ ] T033 [US4] Wire the fake provider into the evaluation entry point in `backend/src/cvtailor/service.py`
- [ ] T034 [P] [US4] Add the end-to-end fake test asserting an archive and no key access in `backend/tests/integration/test_eval_fake.py`

**Checkpoint**: CI can run the harness; commit.

---

## Phase 8: Slice E6 — HTTP surface (US5)

**Goal**: the screen can list, capture, annotate, run, and admit over HTTP.

**Independent Test**: contract tests pass for every route with the fake model.

- [ ] T035 [US5] Implement the set read route in `backend/src/cvtailor/api/routes.py`
- [ ] T036 [US5] Implement adding a posting by pasted text or by importing a stored run posting in `backend/src/cvtailor/api/routes.py`
- [ ] T037 [US5] Implement annotation updates and posting removal in `backend/src/cvtailor/api/routes.py`
- [ ] T038 [US5] Implement the asynchronous run start and its poll route with per-posting progress in `backend/src/cvtailor/api/routes.py`
- [ ] T039 [US5] Implement the admission and withdrawal routes in `backend/src/cvtailor/api/routes.py`
- [ ] T040 [P] [US5] Add contract tests for every eval route in `backend/tests/contract/test_eval_api.py`
- [ ] T041 [P] [US5] Add redaction tests proving no key and no posting text beyond the set route, in `backend/tests/contract/test_eval_redaction.py`

**Checkpoint**: the API contract is green; commit.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [ ] T042 [P] Add a test proving no evaluation command or route modifies `.env`, in `backend/tests/integration/test_eval_config_untouched.py`
- [ ] T043 [P] Document the admission rule and the staleness reasons in `docs/model-admission.md`
- [ ] T044 Run the full `quickstart.md` checklist and record the result

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Setup; blocks every slice.
- **E1 (Phase 3)**: depends on Foundational.
- **E2 (Phase 4)**: depends on E1 — scoring needs a valid set.
- **E3 (Phase 5)**: depends on E2.
- **E4 (Phase 6)**: depends on E3 — admission needs a passing archive.
- **E5 (Phase 7)**: depends on E3; independent of E4.
- **E6 (Phase 8)**: depends on E4 — the routes expose admission. The screen itself is
  delivered by `specs/005-frontend`.
- **Polish (Phase 9)**: depends on the closed slices.

### Story Dependencies

- US1 comes first: nothing scores without a valid set.
- US2 depends on US1; US3 depends on US2 and US4's archive.
- US4 spans E3 and E5.
- US5 depends on US3 and US4 being reachable over HTTP.

### Within Each Slice

- Tests marked [P] can be written in parallel with each other.
- Pure functions before the service, the service before the CLI or the routes, the
  routes before the screen.
- Each slice closes with its "Done when" from `plan.md` and a commit.

### Parallel Opportunities

- Setup: T001, T002, T003.
- Foundational: T010, T011, T012.
- E3: T023 and T024.
- E4: T030, T031, T032.
- E6: T040 and T041.
- Polish: T042 and T043.

---

## Parallel Example: Slice E4

```bash
# Three independent test files once admission exists:
Task: "Add admission and staleness tests in backend/tests/integration/test_eval_admission.py"
Task: "Add settings contract test in backend/tests/contract/test_settings_admission.py"
Task: "Add compare test in backend/tests/integration/test_eval_compare.py"
```

---

## Implementation Strategy

### MVP First

The first useful increment is **E1 + E2**: a validated set and one posting scored. It
proves the dataset and the outcome mapping, which everything else measures.

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (E1), run quickstart 1–2, commit.
3. Continue slice by slice; each closes with its "Done when" and a commit.

### Incremental Delivery

E1 → E2 → E3 → E4 → E5 → E6. The evaluation screen is delivered by
`specs/005-frontend`, on top of E6.

### Commit Discipline

Constitution v2.2.0 requires one commit per completed task. A task is not done until it
is committed.

---

## Notes

- [P] marks different files with no dependency on an incomplete task.
- [USx] maps the task to a story group in the table above.
- Tests are required by the spec; write them first inside each slice.
- No response, command, or report prints a key, a posting text, or the profile content.
- Admitting writes evidence; it never edits configuration.
