# Implementation Plan: Frontend

**Branch**: `005-frontend` | **Date**: 2026-11-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-frontend/spec.md`

## Summary

One React application under `frontend/` that puts the five backend flows in a browser:
tailoring, run history, settings, profile ingestion, and model evaluation. A single shell
owns navigation and the profile selector; every screen reads and writes through a typed
client generated from the checked-in OpenAPI schema; TanStack Query holds server state.
The application is held by the same gate as the backend — typecheck, component tests, and
build run inside `make check` and in CI.

This spec owns the delivery of the UI. The behaviour each screen exercises stays owned by
the backend spec that defines it.

## Technical Context

**Language/Version**: TypeScript 5.x with `strict`, React 19, Node 26.13 and npm 11.20.

**Primary Dependencies**: Vite, Material UI 9 with Emotion, React Router, TanStack Query,
and `openapi-typescript` as a development dependency for the generated types. No other
runtime library.

**Storage**: none. The browser holds no API key, no posting after submission, and no
persisted server state beyond the profile slug in the URL and the query cache in memory.

**Testing**: Vitest with Testing Library and `user-event`. The generated client module is
mocked per test; no network and no MSW.

**Target Platform**: A modern browser against the backend on `127.0.0.1`. The app is served
by Vite in development and as static files in a production build.

**Project Type**: The web frontend of the existing application.

**Performance Goals**: first paint of the shell without waiting for data; each screen
renders its loading state immediately and its content once the query resolves.

**Constraints**: no key in the browser; the posting text is dropped after submission; UI
chrome is English in version 1; the checked-in OpenAPI schema is the only source of types;
no direct `fetch` in components.

**Scale/Scope**: Five routes, one shell, one typed client, five viewmodels, and component
tests per screen.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
Evaluated against constitution v2.2.0.

| Gate | How the plan satisfies it | Verdict |
| --- | --- | --- |
| III. Untrusted input, isolated secrets | The key never reaches the browser; settings renders booleans only; the posting is dropped after submission | PASS |
| IV. Human review before artifacts leave | The tailoring screen shows the PDF, page count, warnings, gaps, models, and the report link before any download | PASS |
| V. Provider-agnostic LLM layer | The UI never calls a model; it reads admission state from settings | PASS |
| Frontend stack matches the constitution | React 19, TypeScript, Vite, Material UI 9 + Emotion, React Router, TanStack Query, generated client, Vitest, Testing Library | PASS |
| Contract is the schema | Types come from `backend/openapi.json`; the drift gate from 001 fails CI when they diverge | PASS |
| No new dependency without need | Only `openapi-typescript` is added, and only to generate types | PASS |
| No unresolved clarification | Decisions are recorded in [research.md](./research.md) | PASS |

No gate fails.

**Post-design re-check** (after Phase 0 and Phase 1): still PASS. The UI contract adds no
route the backend does not expose, and the state model keeps the posting out of storage.

## Project Structure

### Documentation (this feature)

```text
specs/005-frontend/
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0 decisions
├── data-model.md        # view models and screen state
├── contracts/
│   └── ui.md            # routes, URL parameters, and screen states
└── quickstart.md
```

### Source Code

```text
frontend/
├── src/
│   ├── api/
│   │   ├── schema.d.ts      # generated from backend/openapi.json
│   │   ├── client.ts        # typed fetch wrapper; the only place fetch appears
│   │   └── keys.ts          # query keys, one place so invalidation is checkable
│   ├── app/
│   │   ├── App.tsx          # router and providers
│   │   └── AppShell.tsx     # navigation, profile selector, error boundary
│   ├── components/
│   │   ├── ProfileSelector.tsx
│   │   ├── ScreenState.tsx  # loading, empty, and error rendering
│   │   ├── PdfPreview.tsx
│   │   ├── SelectionEditor.tsx
│   │   ├── IngestionReview.tsx
│   │   ├── EvalAnnotation.tsx
│   │   └── EvalResult.tsx
│   ├── viewmodels/
│   │   ├── useTailoring.ts
│   │   ├── useSelectionEditor.ts
│   │   ├── useRuns.ts
│   │   ├── useSettings.ts
│   │   ├── useIngestion.ts
│   │   └── useEvaluation.ts
│   ├── pages/
│   │   ├── TailoringPage.tsx
│   │   ├── HistoryPage.tsx
│   │   ├── SettingsPage.tsx
│   │   ├── IngestionPage.tsx
│   │   └── EvaluationPage.tsx
│   └── main.tsx
├── tests/
├── package.json
├── tsconfig.json
├── vite.config.ts
└── vitest.setup.ts
```

**Structure Decision**: pages are presentational and compose components; viewmodels own
queries, mutations, and screen state; `api/` is the only module that talks HTTP. This
matches the project rules: UI presentational, state in hooks, HTTP in a typed client.

### Delivery Order

Each slice ends in a commit and has a "Done when" condition.

**F1 — Shell, client, profile selector, settings.**
Scope: the app shell, the router, the generated client, the profile selector, the settings
page, and the shared loading/empty/error component.
Done when: the app runs against the backend; navigation reaches all five routes with
placeholder pages; the selector lists profiles in slug order and persists in the URL;
settings shows key presence and admission state without the key; the backend-unreachable
state is visible.

**F2 — History.**
Scope: the runs list, the run detail, and the report/PDF links.
Done when: a CLI-created run appears with date, profile, enterprise, title, language, and
page count; reopening shows the digest, selection, warnings, and report link; an empty
history and a deleted run directory are both handled.

**F3 — Tailoring.**
Scope: posting input, analysis, selection display, warnings, PDF preview, downloads.
Done when: submitting a posting shows the digest and the proposed selection; the preview
renders the actual PDF; the report downloads separately; the posting text disappears from
the page after submission.

**F4 — Editing and re-render.**
Scope: the selection editor and the render-only mutation.
Done when: changing role, language, summaries, bullet order, skill priority, projects, or
research posts a render with the origin run and never an analysis call; an invalid edit
names the offending item; the derived run appears in history linked to its origin.

**F5 — Ingestion screen.**
Scope: upload, per-section progress, skipped-file warnings, bilingual review, decisions,
and commit.
Done when: uploading files shows each section settling; a skipped file is named; an item
shows both variants with the translated one marked; approve, reject, edit, bulk approve,
and commit work; a refused commit shows the missing list and keeps the draft.

**F6 — Evaluation screen.**
Scope: the set list, capture, annotation, the invalidation warning, the run with progress,
metrics, and admit/withdraw.
Done when: the ten postings list for the selected profile; capture works by paste and by
run import; annotation updates the version and warns before invalidating; the run shows
per-posting progress and then metrics; admitting requires a confirmation.

**F7 — Gates and accessibility.**
Scope: `tsc --noEmit`, Vitest, and the build wired into `make check` and CI; the
accessibility pass; the rules amendment.
Done when: the three gates run from `make check`; a deliberately broken type fails; a
keyboard-only pass reaches every action; `.opencode/rules/rules.md` permits TanStack Query
and React Router.

## Complexity Tracking

| Item | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| `openapi-typescript` as a dev dependency | The constitution requires a client generated from the schema. | Hand-written types drift from the contract and defeat the drift gate. |
| One client module plus one query-key module | Invalidation is the main source of stale-UI bugs; centralising keys makes it reviewable. | Inline keys scattered per hook make cache bugs invisible until a user sees stale data. |
