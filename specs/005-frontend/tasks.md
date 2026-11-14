---
description: "Task list for 005-frontend"
---

# Tasks: Frontend

**Input**: Design documents from `/specs/005-frontend/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ui.md, quickstart.md, `.specify/memory/constitution.md` (v2.2.0)

**Prerequisite features**: `001` supplies the API and the checked-in OpenAPI schema, `002`
the ingestion routes, `003` the evaluation routes. No task here re-implements them.

**Tests**: Required. The spec's Testing Decisions and constitution v2.2.0 make component
tests mandatory, including empty and error states.

**Organization**: Phases follow the plan's slices (F1–F7), each with a "Done when"
condition. The spec's 44 stories are grouped into nine story labels; each task carries the
label of the group it serves.

| Story | Spec stories | Coverage |
| --- | --- | --- |
| US1 | Shell and navigation (1–4) | shell, router, four destinations, offline surface |
| US2 | Profile selector (5–8) | selector, URL, empty state |
| US3 | Workspace (9–15) | posting, generate, digest, selection, review, preview, downloads |
| US4 | Editing (16–19) | editor controls, re-render, invalid edit, derived run |
| US5 | History (20–23) | list, detail, empty, missing run |
| US6 | Settings (24–26) | key, chains, limits, badge |
| US7 | Upload dialog (27–35) | dialog, progress, decisions, Save, Cancel |
| US8 | Evaluation (36–41) | list, capture, annotate, run, admit |
| US9 | Quality (42–44) | states, errors, accessibility, gates |

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: which story group the task serves
- Every task names an exact file path

## Path Conventions

- Frontend: `frontend/src/`, tests in `frontend/tests/`
- Generated types: `frontend/src/api/schema.d.ts` from `backend/openapi.json`

---

## Phase 1: Setup

- [ ] T001 Scaffold the app with Vite, React 19, and TypeScript strict in `frontend/package.json` and `frontend/tsconfig.json`
- [ ] T002 [P] Add Material UI 9 with Emotion, React Router, and TanStack Query in `frontend/package.json`
- [ ] T003 [P] Add Vitest, Testing Library, and `openapi-typescript` with the `generate:api` script in `frontend/package.json`
- [ ] T004 [P] Configure the test environment and setup file in `frontend/vitest.setup.ts`

**Checkpoint**: `npm run build` and `npm test` run on an empty shell.

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: no slice starts until this phase completes.

- [ ] T005 [US1] Implement the shell, the router, and the four destinations in `frontend/src/app/AppShell.tsx`
- [ ] T006 [US1] Generate the types and implement the typed client, the only module that calls fetch, in `frontend/src/api/client.ts`
- [ ] T007 [US9] Normalize every failure to `{code, message}` in `frontend/src/api/client.ts`
- [ ] T008 [US2] Define every query key in one module in `frontend/src/api/keys.ts`
- [ ] T009 [US9] Implement the shared loading, empty, and error component in `frontend/src/components/ScreenState.tsx`
- [ ] T010 [US2] Implement the profile selector in slug order with a blocklist badge in `frontend/src/components/ProfileSelector.tsx`
- [ ] T011 [US2] Carry the selected profile as a search parameter on every route in `frontend/src/app/AppShell.tsx`
- [ ] T012 [US1] Implement the backend-unreachable surface with a retry in `frontend/src/app/AppShell.tsx`
- [ ] T013 [P] [US1] Add tests for navigation, the profile in the URL, and the offline surface in `frontend/tests/shell.test.tsx`

**Checkpoint**: the shell runs against the backend; commit.

---

## Phase 3: Slice F1 — Workspace skeleton and settings (US3, US6)

**Goal**: the start page exists with its three controls, and settings is readable.

**Independent Test**: quickstart steps 1–3 pass.

- [ ] T014 [US3] Implement the workspace route with the posting field and the generate action in `frontend/src/pages/WorkspacePage.tsx`
- [ ] T015 [US3] Disable generate without a profile and write the reason beside it in `frontend/src/pages/WorkspacePage.tsx`
- [ ] T016 [US6] Show key presence without the key in `frontend/src/pages/SettingsPage.tsx`
- [ ] T017 [US6] Show chains with provider, model, state, reason, and last metrics in `frontend/src/pages/SettingsPage.tsx`
- [ ] T018 [US6] Show limits read-only and raise the stale badge in the shell in `frontend/src/pages/SettingsPage.tsx`
- [ ] T019 [P] [US6] Add tests for the two settings states and the masked key rule in `frontend/tests/settings.test.tsx`

**Checkpoint**: quickstart 1–3 pass; commit.

---

## Phase 4: Slice F2 — History (US5)

**Goal**: runs are findable and reopenable.

**Independent Test**: quickstart step 4 passes.

- [ ] T020 [US5] Implement the runs list, newest first, with the summary fields and the fallback chip in `frontend/src/pages/HistoryPage.tsx`
- [ ] T021 [US5] Implement the run detail with digest, selection, warnings, report link, and origin link in `frontend/src/pages/RunDetailPage.tsx`
- [ ] T022 [US5] Handle the empty history with a link to the workspace in `frontend/src/pages/HistoryPage.tsx`
- [ ] T023 [US5] Handle a missing run directory by returning to the list with an error line in `frontend/src/pages/RunDetailPage.tsx`
- [ ] T024 [P] [US5] Add tests for the list, the detail, the empty state, and the missing run in `frontend/tests/history.test.tsx`

**Checkpoint**: quickstart 4 passes; commit.

---

## Phase 5: Slice F3 — Workspace: posting to CV (US3)

**Goal**: a posting becomes a reviewable one-page PDF.

**Independent Test**: quickstart step 5 passes.

- [ ] T025 [US3] Submit the posting and render the digest in `frontend/src/viewmodels/useTailoring.ts`
- [ ] T026 [US3] Render the proposed selection grouped by section with counts in `frontend/src/components/SelectionView.tsx`
- [ ] T027 [US3] Render gaps, coverage, red flags, layout warnings, and the checklist in `frontend/src/components/ReviewPanel.tsx`
- [ ] T028 [US3] Render the PDF artifact in an iframe from a blob with the page count in `frontend/src/components/PdfPreview.tsx`
- [ ] T029 [US3] Implement the PDF and report downloads as separate actions in `frontend/src/components/PdfPreview.tsx`
- [ ] T030 [US3] Clear the posting field on a successful response in `frontend/src/pages/WorkspacePage.tsx`
- [ ] T031 [US3] Restore a run from the `run` URL parameter in `frontend/src/viewmodels/useTailoring.ts`
- [ ] T032 [P] [US3] Add tests for submission, the review panel, the preview failure, and the cleared posting in `frontend/tests/workspace.test.tsx`

**Checkpoint**: quickstart 5 passes; commit.

---

## Phase 6: Slice F4 — Editing and re-render (US4)

**Goal**: the selection is editable and re-renders without a model call.

**Independent Test**: quickstart step 6 passes.

- [ ] T033 [US4] Implement the role selector and the language toggle in `frontend/src/components/SelectionEditor.tsx`
- [ ] T034 [US4] Implement summary add, remove, and reorder with the lead-block rule in `frontend/src/components/SelectionEditor.tsx`
- [ ] T035 [US4] Implement per-role bullet reorder and removal within the validator limits in `frontend/src/components/SelectionEditor.tsx`
- [ ] T036 [US4] Implement skill priority in `frontend/src/components/SelectionEditor.tsx`
- [ ] T037 [US4] Implement project and research toggles in `frontend/src/components/SelectionEditor.tsx`
- [ ] T038 [US4] Implement the render-only mutation with the origin and no analysis call in `frontend/src/viewmodels/useSelectionEditor.ts`
- [ ] T039 [US4] Name the offending item when an edit is rejected in `frontend/src/viewmodels/useSelectionEditor.ts`
- [ ] T040 [US4] Show the derived run in history linked to its origin in `frontend/src/pages/HistoryPage.tsx`
- [ ] T041 [P] [US4] Add tests proving no analysis call on edit and the invalid-edit message in `frontend/tests/editing.test.tsx`

**Checkpoint**: quickstart 6 passes; commit.

---

## Phase 7: Slice F5 — Upload dialog (US7)

**Goal**: CVs are captured and saved without leaving the workspace.

**Independent Test**: quickstart step 7 passes.

- [ ] T042 [US7] Open the dialog from the upload button and return focus on close in `frontend/src/components/IngestionDialog.tsx`
- [ ] T043 [US7] Enforce the client-side limits and name them on refusal in `frontend/src/components/IngestionDialog.tsx`
- [ ] T044 [US7] Poll the draft and render one progress row per section in `frontend/src/viewmodels/useIngestion.ts`
- [ ] T045 [US7] List skipped files by name with the reason in `frontend/src/components/IngestionDialog.tsx`
- [ ] T046 [US7] Render each item with both variants and the translated marker in `frontend/src/components/IngestionDialog.tsx`
- [ ] T047 [US7] Implement approve and reject with immediate counts in `frontend/src/viewmodels/useIngestion.ts`
- [ ] T048 [US7] Implement item editing marked as user-edited in `frontend/src/viewmodels/useIngestion.ts`
- [ ] T049 [US7] Implement bulk approve restricted to verified items in `frontend/src/viewmodels/useIngestion.ts`
- [ ] T050 [US7] Implement the profile target, preselecting the current one in `frontend/src/components/IngestionDialog.tsx`
- [ ] T051 [US7] Show readiness and refuse Save with the missing list in `frontend/src/components/IngestionDialog.tsx`
- [ ] T052 [US7] Implement Save, closing the dialog and selecting the new profile in `frontend/src/viewmodels/useIngestion.ts`
- [ ] T053 [US7] Implement Cancel with confirmation, discarding the draft in `frontend/src/viewmodels/useIngestion.ts`
- [ ] T054 [US7] Enable generate for the new profile after Save in `frontend/src/pages/WorkspacePage.tsx`
- [ ] T055 [P] [US7] Add tests for progress, skipped files, decisions, Save, Cancel, and the refused save in `frontend/tests/ingestion.test.tsx`

**Checkpoint**: quickstart 7 passes; commit.

---

## Phase 8: Slice F6 — Evaluation screen (US8)

**Goal**: the evaluation loop without a terminal.

**Independent Test**: quickstart step 8 passes.

- [ ] T056 [US8] List the ten postings with annotations and the version in `frontend/src/pages/EvaluationPage.tsx`
- [ ] T057 [US8] Capture a posting by pasted text in `frontend/src/components/EvalPostingForm.tsx`
- [ ] T058 [US8] Import a posting from a run's stored text in `frontend/src/components/EvalPostingForm.tsx`
- [ ] T059 [US8] Annotate the expected role in `frontend/src/components/EvalAnnotation.tsx`
- [ ] T060 [US8] Annotate must-include bullets grouped by role in `frontend/src/components/EvalAnnotation.tsx`
- [ ] T061 [US8] Warn before an annotation change that invalidates admissions in `frontend/src/viewmodels/useEvaluation.ts`
- [ ] T062 [US8] Replace a posting while the set is full in `frontend/src/components/EvalPostingForm.tsx`
- [ ] T063 [US8] Run with per-posting progress in `frontend/src/viewmodels/useEvaluation.ts`
- [ ] T064 [US8] Show metrics, verdict, and failing conditions in `frontend/src/components/EvalResult.tsx`
- [ ] T065 [US8] Admit and withdraw behind a confirmation, showing stale reasons in `frontend/src/components/EvalAdmission.tsx`
- [ ] T066 [P] [US8] Add tests for listing, the warning, the run progress, and the confirmation in `frontend/tests/evaluation.test.tsx`

**Checkpoint**: quickstart 8 passes; commit.

---

## Phase 9: Slice F7 — Gates and accessibility (US9)

**Goal**: the frontend is held by the same gate as the backend.

**Independent Test**: quickstart steps 9 and 10 pass.

- [ ] T067 [US9] Add the `typecheck`, `test`, and `build` targets to `Makefile` and include them in `check`
- [ ] T068 [US9] Run the three gates in CI in `.github/workflows/ci.yml`
- [ ] T069 [US9] Pass the keyboard and labelling review, fixing what it finds, in `frontend/src/app/AppShell.tsx`
- [ ] T070 [US9] Amend `.opencode/rules/rules.md` to permit TanStack Query and React Router and record the frontend gates

**Checkpoint**: quickstart 9–10 pass; commit.

---

## Phase 10: Polish & Cross-Cutting Concerns

- [ ] T071 [P] Add a test asserting no component imports fetch directly in `frontend/tests/architecture.test.ts`
- [ ] T072 [P] Add a test asserting the key never appears in any rendered output in `frontend/tests/settings.test.tsx`
- [ ] T073 Run the full `quickstart.md` checklist and record the result

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Setup; blocks every slice.
- **F1 (Phase 3)**: depends on Foundational.
- **F2 (Phase 4)**: depends on Foundational; independent of F1.
- **F3 (Phase 5)**: depends on F1 — the workspace hosts the flow.
- **F4 (Phase 6)**: depends on F3.
- **F5 (Phase 7)**: depends on F1 and F3 — the dialog opens from the workspace.
- **F6 (Phase 8)**: depends on Foundational and F2 (import from a run).
- **F7 (Phase 9)**: depends on the screens it gates.
- **Polish (Phase 10)**: depends on the closed slices.

### Story Dependencies

- US1 and US2 come first: the shell and the profile drive everything.
- US3 depends on US2; US4 depends on US3.
- US5 is independent of US3; US6 depends on US1 only.
- US7 depends on US1, US3, and the ingestion API.
- US8 depends on US5 for import and the evaluation API.
- US9 spans the whole feature.

### Within Each Slice

- Tests marked [P] can be written in parallel.
- Client and keys before viewmodels; viewmodels before pages.
- Each slice closes with its "Done when" and a commit.

### Parallel Opportunities

- Setup: T002, T003, T004.
- Foundational: T013 with T005–T012.
- F1: T019.
- F2: T020–T023 largely independent; T024 after.
- F3: T025–T031 split across components; T032 after.
- F4: T033–T037 are separate controls.
- F5: T043–T050 after the dialog opens.
- F6: T057–T062 split across components.
- Polish: T071 and T072.

---

## Parallel Example: Slice F4

```bash
# Each editor control is its own file concern once the draft model exists:
Task: "Implement role and language in frontend/src/components/SelectionEditor.tsx"
Task: "Implement skill priority in frontend/src/components/SelectionEditor.tsx"
Task: "Implement project toggles in frontend/src/components/SelectionEditor.tsx"
Task: "Add editing tests in frontend/tests/editing.test.tsx"
```

---

## Implementation Strategy

### MVP First

The first useful increment is **F1**: the shell plus the workspace skeleton plus settings.
It proves the client, the profile URL, the states, and the disabled generate rule — the
foundation every other screen reuses.

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (F1), run quickstart 1–3, commit.
3. Continue slice by slice.

### Incremental Delivery

F1 → F2 → F3 → F4 → F5 → F6 → F7. The backend must already expose the routes each slice
consumes; the ingestion dialog needs `002`, the evaluation screen needs `003`.

### Commit Discipline

Constitution v2.2.0 requires one commit per completed task. A task is not done until it is
committed.

---

## Notes

- [P] marks different files with no dependency on an incomplete task.
- [USx] maps the task to a story group in the table above.
- Tests are required by the spec; write them first inside each slice.
- The posting is sent once, never stored, and cleared on success.
- Generate stays disabled with a written reason until a profile exists.
- The upload dialog is the only ingestion UI; there is no ingestion route.
- The label is Save; the backend route stays `commit`.
