# Frontend — v1

**Feature Branch**: `005-frontend`
**Created**: 2026-11-14
**Status**: ready-for-agent
**Depends on**: `001-cv-tailor-v1-mvp` (API, OpenAPI schema), `002-profile-ingestion` (ingestion API), `003-model-admission` (evaluation API)

## Problem Statement

The backend exposes five flows — tailor, render, history, ingestion, and evaluation —
but today every one of them is reachable only from the terminal. The product promise is
a reviewable CV: the user must see the PDF, the page count, the layout warnings, the
gaps, and the model that answered, and must be able to edit the selection and re-render
without a model call. A terminal cannot show a PDF, and a JSON dump is not a review.

The screens also keep getting scattered across specs: the pipeline spec described the
tailoring UI, the ingestion spec deferred its screen to "the frontend spec", and the
admission spec grew a screen of its own. Nobody owns the shell, the navigation, the
typed client, or the gates that hold the UI to the same standard as the backend.

## Solution

One React application under `frontend/`, with a single shell and four destinations:
the workspace, run history, settings, and model evaluation. The workspace is the start
page and holds the whole daily flow: a field for the job posting, a button to upload CV
files, and the action that generates the CV, which stays disabled until a profile exists.

Uploading does not navigate away. It opens a dialog that shows what the model read from
the files, where the user approves, edits, or cancels, and where the draft is saved into a
named profile ("Save", never "commit"). The app uses the typed client generated from the
backend's OpenAPI schema and TanStack Query for server state; Material UI for components;
no key ever reaches the browser. It is held by the same gate as the backend: typecheck,
component tests, and build run inside `make check`.

The backend specifications keep owning their behaviour. This spec owns how that
behaviour is delivered to a person: the shell, the navigation, the client, the states,
and the tests.

## User Stories

### Shell and navigation

1. As a job seeker, I want one application with a stable navigation, so that I always know where I am.
2. As a job seeker, I want to move between the workspace, history, settings, and evaluation without losing my review, so that a check mid-flow does not cost me the draft.
3. As a job seeker, I want the app to tell me when the backend is unreachable, so that a blank screen is never mistaken for an empty result.
4. As a job seeker, I want to reload the page without losing the profile I selected, so that a refresh does not reset my context.

### Profile selector

5. As a job seeker, I want a profile selector in the shell, so that every screen acts on the profile I chose.
6. As a job seeker, I want profiles listed in name order, so that the one I want is always in the same place.
7. As a job seeker, I want the selector to show which profiles have a blocklist, so that I know where I am protected.
8. As a job seeker, I want an empty state when no profile exists, so that I know to run ingestion first.

### Tailoring

9. As a job seeker, I want to paste a posting and submit it, so that the analysis starts without leaving the page.
10. As a job seeker, I want to see the digest after submission, so that I can confirm the tool understood the role before the CV is rendered.
11. As a job seeker, I want to see the proposed selection grouped by section, so that I can judge it against the posting.
12. As a job seeker, I want warnings, gaps, coverage, and red flags displayed next to the CV, so that I review before downloading.
13. As a job seeker, I want a preview of the actual PDF, so that I see what the employer will see.
14. As a job seeker, I want to download the PDF and the report separately, so that internal analysis never ships with the CV.
15. As a job seeker, I want the posting text to disappear from the page after submission, so that it is not left in the browser history.

### Editing and re-rendering

16. As a job seeker, I want to change the role, the language, the summaries, the bullet order, the skill priority, the projects, and the research, so that I control what the CV says.
17. As a job seeker, I want every edit to re-render through the render route with the origin run, so that no model is called and the result is reproducible.
18. As a job seeker, I want an invalid edit to tell me which item is wrong, so that I can fix it without guessing.
19. As a job seeker, I want the derived run to appear in history with a link to its origin, so that I can trace how the CV evolved.

### History

20. As a job seeker, I want the runs listed newest first with date, profile, enterprise, title, and language, so that I can find an earlier application.
21. As a job seeker, I want to reopen a run and see its digest, selection, warnings, and report, so that I can resume where I stopped.
22. As a job seeker, I want an empty history to say so, so that a fresh install does not look broken.
23. As a job seeker, I want the list to survive a run directory being deleted, so that one bad directory does not break the page.

### Settings

24. As a job seeker, I want to see whether a provider key is set, without seeing the key, so that I can diagnose a missing configuration.
25. As a job seeker, I want to see the configured chains with their admission state for the selected profile, so that I know which model is trusted.
26. As a job seeker, I want the limits shown, so that I know why a posting was rejected.

### Upload dialog

27. As a job seeker, I want to upload PDF and DOCX files from the workspace, so that building a profile never requires leaving the page.
28. As a job seeker, I want the upload to open a dialog showing what the model read, so that I review before anything is saved.
29. As a job seeker, I want a file without a text layer to be named and skipped, so that the good files still build the draft.
30. As a job seeker, I want each item to show both language variants with the translated one marked, so that I know what I am approving.
31. As a job seeker, I want to approve, reject, edit, and bulk approve inside the dialog, so that the review happens where the upload started.
32. As a job seeker, I want the dialog to ask which profile to save into, suggesting the selected one, so that the first upload and an update both work.
33. As a job seeker, I want the action to be called Save, so that the vocabulary matches what happens.
34. As a job seeker, I want Cancel to discard the draft, so that an abandoned upload leaves nothing behind.
35. As a job seeker, I want a refused save to show what the profile still lacks, so that I can fix it without starting over.

### Evaluation screen

36. As a maintainer, I want to see the ten postings of the evaluation set for the selected profile, so that I know what is measured.
37. As a maintainer, I want to capture a posting by pasting or by importing a run, so that a case I just used is not retyped.
38. As a maintainer, I want to annotate the expected role and the must-include bullets, so that the score means something.
39. As a maintainer, I want to be warned that changing an annotation makes admissions stale, so that I do not lose evidence by accident.
40. As a maintainer, I want to run the evaluation and watch each posting being scored, so that a slow model does not look frozen.
41. As a maintainer, I want to admit or withdraw a model after a confirmation, so that the sensitive decision stays deliberate.

### Quality of the UI

42. As a job seeker, I want a loading state that names what is loading, so that I can tell waiting from failure.
43. As a job seeker, I want errors shown in the language of the product, with the backend's code, so that I can report a problem precisely.
44. As a job seeker, I want the app to work with the keyboard and to have labelled controls, so that I can use it without a mouse.

## Implementation Decisions

- Stack: React 19, TypeScript strict, Vite, Material UI 9 with Emotion, React Router, and
  TanStack Query. No additional data library, no CSS framework, no component kit.
- Four destinations under one shell: workspace, history, settings, evaluation. The
  workspace is the root route and carries the posting field, the upload button, and the
  generate action. The profile selector lives in the shell, and the selected slug is a
  search parameter on every route so a refresh keeps it.
- Uploading opens a dialog rather than navigating: it shows per-section progress, the
  skipped files, and the bilingual items, and it ends in Save, Edit, or Cancel. Save is
  the label; the backend route stays `commit`. Closing the dialog discards the draft.
- The dialog asks for the target profile, preselecting the one already selected, so the
  first upload creates a profile and a later upload can update it.
- Generate is disabled until a profile exists, with the reason written beside it.
- A run id in the workspace URL rehydrates the review from the run; the posting is never
  restored.
- The API client is generated from the checked-in OpenAPI schema into types, with a thin
  typed wrapper around `fetch`. No component calls `fetch` directly; no hand-written type
  duplicates a schema type.
- Server state goes through TanStack Query. Mutations invalidate the queries they affect;
  the render-only edit path does not invalidate the analysis.
- The browser never holds the API key, the posting after submission, or the profile's
  full master beyond what the editing screen needs.
- Error responses are rendered from the backend's `{code, message}` shape. Unknown codes
  fall back to a generic message and keep the code visible.
- Every screen has an explicit loading, empty, and error state. A spinner without a label
  is not acceptable.
- UI chrome is English in version 1; CV output remains EN/PT and is chosen per run.
- Accessibility baseline: labelled inputs, visible focus, keyboard reachable actions, and
  a heading order that matches the visual order.
- The OpenAPI drift check from 001 is the contract gate: a schema change without
  regenerating the client fails CI.
- Gates: `tsc --noEmit`, Vitest, and the production build run from the Makefile and in
  CI, alongside the backend gates.

## Testing Decisions

A good frontend test asserts what the user sees and does, with the generated client
mocked. Domain rules are not re-tested here; they are already covered at the API seam.

- **Tailoring**: from empty to analysis to selection, including the loading and error
  states.
- **Editing**: every edit posts a render with the origin and never an analysis call.
- **History**: listing, reopening, and the empty state.
- **Settings**: key presence without the key, and admission state per profile.
- **Ingestion**: section progress, a skipped file, the bilingual item, and the actions.
- **Evaluation**: listing, annotation with the invalidation warning, and the admit
  confirmation.
- **Shell**: navigation between routes, the profile selector persisting in the URL, and
  the backend-unreachable state.
- **Prior art**: the API seam and fake-provider pattern from 001–003; the component
  testing conventions established here.

## Out of Scope

- A Portuguese UI.
- Mobile layouts or a native app.
- Offline mode or a service worker.
- Editing the PDF in the browser.
- Charts or dashboards for market statistics, which stay in the CLI.
- Authentication, accounts, or multi-user sessions.
- Theme switching or branding beyond the default Material UI theme.

## Further Notes

- **Why a spec of its own.** The UI was described in three places and owned in none:
  001 described the tailoring screens, 002 deferred its screen to "the frontend spec",
  and 003 grew one. One owner for the shell, the client, the states, and the gates
  removes that ambiguity.
- **What moves here.** The delivery of every screen, the shell, the generated client, the
  frontend gates, and the UI testing conventions. The behaviour each screen exercises
  stays owned by its backend spec.
- **Sequencing.** This spec is delivered last, after 001's API is stable and after the
  ingestion and evaluation endpoints exist. Its screens can then land in any order, each
  behind its own route.
- **Tracker.** No issue tracker is configured; published as a file with
  `ready-for-agent` in the status line.
