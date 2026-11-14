# UI Contract: Frontend

Routes, URL parameters, and the states each screen must render. The backend contract is
the OpenAPI schema; this document covers what the browser does with it.

## Shell

Present on every route:

- Navigation with five destinations: Tailor, History, Settings, Ingest, Evaluate.
- The profile selector, driven by `GET /api/profiles`, in slug order.
- A badge on Settings when any configured chain entry is `stale` or `unadmitted`.
- A persistent error surface when the backend is unreachable, with a retry.

The selected profile is a `profile` search parameter on every route. Absent, it resolves to
the first profile in slug order. Changing it re-renders the current screen for that
profile.

## Routes

| Route | Screen | Data |
| --- | --- | --- |
| `/tailor` | Tailoring | none until submit; then tailor response |
| `/runs` | History | `GET /api/runs` |
| `/runs/:id` | Run detail | `GET /api/runs/{id}`, artifacts |
| `/settings` | Settings | `GET /api/settings?profile=` |
| `/ingest` | Ingestion | none until upload; then the draft |
| `/ingest/:id` | Ingestion review | `GET /api/ingestions/{id}` polled |
| `/eval` | Evaluation | `GET /api/eval/set?profile=` |
| `/eval/:runId` | Evaluation run | `GET /api/eval/runs/{id}` polled |

## Screen states

Every screen renders exactly one of:

| State | Requirement |
| --- | --- |
| Loading | A labelled line naming what is being fetched. No bare spinner. |
| Empty | What is missing and the action that fixes it. |
| Error | The backend `message`, the `code` in a subdued line, and a retry. |
| Ready | The content. |

Specific empties:

- No profiles → "create one with ingestion" and a link to `/ingest`.
- No runs → "tailor a CV first" and a link to `/tailor`.
- No evaluation set → "add ten postings" and the capture form.

## Tailoring

- Submit is disabled while a request is in flight and while the posting is empty.
- On success, the digest and the proposed selection appear; the posting input is cleared.
- The preview loads the PDF artifact; a failure shows the error state, not a blank frame.
- Two downloads, always separate: the PDF and the report.
- "Re-render" is disabled until a selection edit makes the draft dirty; it never triggers
  an analysis.

## History

- Rows show date, profile, enterprise, title, language, page count, and a fallback chip.
- A derived run shows a link to its origin.
- A missing run directory returns to the list with an error line, not a broken page.

## Settings

- Key presence as a boolean; the key is never rendered, even masked.
- Chains per step, each with provider, model, and state (`admitted`, `stale` with reason,
  `unadmitted`), and the last passing metrics when admitted.
- Limits, read-only.

## Ingestion

- Upload accepts the same limits the backend enforces; a client-side rejection explains
  the limit instead of failing after upload.
- Per-section progress rows: pending, ok, or failed with reason.
- A skipped file is listed by name with the reason.
- Each item shows both variants; the translated one carries a "translated" marker and the
  source text is available beside it.
- Commit is enabled only when readiness is true; a refused commit shows the missing list
  and keeps the review state.

## Evaluation

- The ten postings list with their annotations and the set version.
- Capture accepts pasted text or a selected run.
- An annotation edit that changes the version opens a warning naming the models that
  become stale; saving requires confirmation.
- A run shows progress per posting and can be reopened from `/eval/:runId`.
- Metrics show the three numbers, the verdict, and the failing conditions.
- Admit and withdraw require a confirmation dialog that states what changes.

## Accessibility

- One `h1` per screen; headings follow visual order.
- Every input has a label; every action is reachable by keyboard; focus is visible.
- State is never conveyed by colour alone; text carries it.

## Forbidden

- Rendering the API key anywhere, including masked.
- Calling `fetch` outside the client module.
- Persisting the posting text, the profile master, or any key in storage.
- Re-running an analysis on the render-only path.
