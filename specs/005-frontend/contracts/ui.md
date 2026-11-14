# UI Contract: Frontend

Routes, URL parameters, and the states each screen must render. The backend contract is
the OpenAPI schema; this document covers what the browser does with it.

## Shell

Present on every route:

- Navigation with four destinations: Workspace, History, Settings, Evaluate.
- The profile selector, driven by `GET /api/profiles`, in slug order.
- A badge on Settings when any configured chain entry is `stale` or `unadmitted`.
- A persistent error surface when the backend is unreachable, with a retry.

The selected profile is a `profile` search parameter on every route. Absent, it resolves to
the first profile in slug order. Changing it re-renders the current screen for that
profile.

## Routes

| Route | Screen | Data |
| --- | --- | --- |
| `/` | Workspace | none until submit; then the tailor response, or the run named by `run` |
| `/?run=<id>` | Workspace with a restored review | `GET /api/runs/{id}` |
| `/runs` | History | `GET /api/runs` |
| `/runs/:id` | Run detail | `GET /api/runs/{id}`, artifacts |
| `/settings` | Settings | `GET /api/settings?profile=` |
| `/eval` | Evaluation | `GET /api/eval/set?profile=` |
| `/eval/:runId` | Evaluation run | `GET /api/eval/runs/{id}` polled |

There is no ingestion route. Uploading is a dialog over the workspace.

## Workspace

- A posting field, an upload button, and a generate action.
- Generate is disabled until a profile exists, with the reason written beside it and a
  pointer to the upload button.
- Submit is disabled while a request is in flight and while the posting is empty.
- On success, the digest and the proposed selection appear; the posting input is cleared.
- The review panel shows gaps, coverage, red flags, section counts, layout warnings, and
  the checklist.
- The preview loads the PDF artifact; a failure shows the error state, not a blank frame.
- Two downloads, always separate: the PDF and the report.
- "Re-render" is disabled until a selection edit makes the draft dirty; it never triggers
  an analysis.
- A run id in the URL restores the review from the run. The posting is never restored.

## Upload dialog

Opening the upload button opens a dialog; the workspace stays visible behind it. Closing
the dialog returns focus to the button.

| Step | Requirement |
| --- | --- |
| Select files | Accepted types and limits are stated; oversized or too-many files are refused before upload, matching the backend |
| Progress | One row per section: pending, ok, or failed with reason; an all-failed draft says so |
| Skipped files | A file without text is named with the reason, and the rest of the draft continues |
| Items | Both variants per item; the translated one marked with its source text available |
| Decisions | Approve, reject, edit, and bulk approve; every decision reversible until Save |
| Target | The profile to save into, preselecting the current one; a new name is allowed |
| Readiness | The missing list is shown; Save is refused while the master would not render |
| Save | Writes the profile, closes the dialog, selects the new profile, enables generate |
| Cancel | Confirms when decisions were made, discards the draft, writes nothing |

The label is **Save**. The backend route stays `commit`.

## History

- Rows show date, profile, enterprise, title, language, page count, and a fallback chip.
- A derived run shows a link to its origin.
- A missing run directory returns to the list with an error line, not a broken page.

## Settings

- Key presence as a boolean; the key is never rendered, even masked.
- Chains per step, each with provider, model, and state (`admitted`, `stale` with reason,
  `unadmitted`), and the last passing metrics when admitted.
- Limits, read-only.

## Evaluation

- The ten postings list with their annotations and the set version.
- Capture accepts pasted text or a selected run.
- An annotation edit that changes the version opens a warning naming the models that
  become stale; saving requires confirmation.
- A run shows progress per posting and can be reopened from `/eval/:runId`.
- Metrics show the three numbers, the verdict, and the failing conditions.
- Admit and withdraw require a confirmation dialog that states what changes.

## Screen states

Every screen renders exactly one of:

| State | Requirement |
| --- | --- |
| Loading | A labelled line naming what is being fetched. No bare spinner. |
| Empty | What is missing and the action that fixes it. |
| Error | The backend `message`, the `code` in a subdued line, and a retry. |
| Ready | The content. |

## Accessibility

- One `h1` per screen; headings follow visual order.
- Every input has a label; every action is reachable by keyboard; focus is visible.
- State is never conveyed by colour alone; text carries it.
- The dialog traps focus and returns it on close.

## Forbidden

- Rendering the API key anywhere, including masked.
- Calling `fetch` outside the client module.
- Persisting the posting text, the profile master, or any key in storage.
- Re-running an analysis on the render-only path.
- Navigating away from the workspace to upload.
