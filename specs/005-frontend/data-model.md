# Phase 1 Data Model: Frontend

The frontend stores no server state of its own. These models describe what a screen holds
in memory and what it renders; nothing here is persisted.

## Route

| Field | Type | Rules |
| --- | --- | --- |
| `path` | string | One of `/`, `/runs`, `/runs/:id`, `/settings`, `/eval`, `/eval/:runId`. |
| `profile` | string \| null | Search parameter; absent falls back to the first profile. |
| `runId` | string \| null | `/runs/:id`, or the `run` parameter on the workspace. |

Every route renders inside the shell, so navigation and the profile selector exist on all
of them.

## ProfileChoice

| Field | Type | Rules |
| --- | --- | --- |
| `slug` | string | From `GET /api/profiles`, slug order preserved. |
| `hasBlocklist` | boolean | Shown as a badge; no behaviour depends on it. |
| `selected` | boolean | True for the URL parameter, or for the first profile when absent. |

## ScreenState

| Value | Rendered as |
| --- | --- |
| `loading` | A labelled line naming the data being fetched. |
| `empty` | An explanation plus the next action (for example, "run ingestion first"). |
| `error` | The backend `message`, the `code` in a subdued line, and a retry action. |
| `ready` | The screen content. |

A screen never renders `ready` and a spinner at the same time, and never renders a bare
spinner.

## TailoringView

Holds the posting input, the last digest, the proposed selection, the review data, and the
current run.

| Field | Type | Rules |
| --- | --- | --- |
| `posting` | string | Component state only; cleared on a successful tailor response. |
| `digest` | Digest \| null | From the tailor response. |
| `selection` | SelectionDraft \| null | The editable copy of the proposed selection. |
| `review` | Review \| null | Gaps, coverage, red flags, section counts, layout warnings, checklist. |
| `runId` | string \| null | The run the preview and downloads point at. |
| `isDirty` | boolean | True after any edit and before a successful render. |

## SelectionDraft

| Field | Type | Rules |
| --- | --- | --- |
| `roleId` | string | Chosen from the profile's role options. |
| `language` | `pt-BR` \| `en-US` | Defaults to the last choice, then `pt-BR`. |
| `summaryIds` | string[] | Ordered; the first must be a lead block. |
| `experience` | map roleId -> string[] | Per-role bullet order. |
| `skillPriority` | string[] | Ordered. |
| `projectIds`, `researchIds` | string[] | Toggles. |

Any change sets `isDirty` and enables "Re-render"; re-rendering posts the draft with the
origin run.

## RunSummaryView

| Field | Type | Rules |
| --- | --- | --- |
| `id`, `createdAt`, `profile` | string | From the run list. |
| `enterpriseName`, `jobTitle`, `level` | string | From the digest summary. |
| `requestedLanguage` | `pt-BR` \| `en-US` | Shown as a chip. |
| `pages` | integer | One page is the promise; anything else is flagged. |
| `fallbackUsed` | boolean | Shown as a chip. |
| `originRunId` | string \| null | Link to the origin when present. |

## IngestionDialogState

| Field | Type | Rules |
| --- | --- | --- |
| `draftId` | string | From the create response; lives only while the dialog is open. |
| `target` | string | Profile slug to save into; preselected from the shell. |
| `state` | `processing` \| `complete` \| `failed` \| `stalled` | Polled. |
| `sections` | map name -> SectionStatus | One row per section, updated live. |
| `items` | DraftItemView[] | Both variants; the translated one marked. |
| `counts` | map status -> integer | Pending, approved, rejected, duplicate, unverified. |
| `readiness` | Readiness | `{ready, missing[]}`; Save refused while not ready. |
| `skippedFiles` | string[] | Named files that produced no text. |

## EvaluationView

| Field | Type | Rules |
| --- | --- | --- |
| `postings` | EvalPostingView[] | Ten, in manifest order, with annotations. |
| `version` | string | Changes on any annotation edit. |
| `selectedPosting` | string \| null | The one being annotated or replaced. |
| `run` | EvalRunView \| null | `{state, progress, outcomes}` while running. |
| `metrics` | EvalMetrics \| null | Present when the run completes. |
| `verdict` | ThresholdVerdict \| null | With `failedOn` when it fails. |
| `admission` | AdmissionState | `admitted`, `stale` with a reason, or `unadmitted`. |

An annotation edit that would change `version` opens the invalidation warning before
saving; the warning lists the models that would become stale.

## Query keys

| Key | Used by | Invalidated by |
| --- | --- | --- |
| `profiles` | shell, every screen | a save in the upload dialog |
| `profile(slug)` | tailoring, ingestion | profile edits |
| `runs` | history | tailor, render, delete |
| `run(id)` | history detail, tailoring | render of a derived run |
| `settings(profile)` | settings, shell badge | admission changes |
| `draft(id)` | upload dialog | decisions, retry, save |
| `evalSet(profile)` | evaluation | add, annotate, remove |
| `evalRun(id)` | evaluation | polling; terminal state |

The render-only edit invalidates `run(id)`, `runs`, and `settings` — never the analysis.

## Rules that live in code

- No key, no posting after submission, and no profile master outside the editing screen.
- A screen renders exactly one of `loading`, `empty`, `error`, `ready`.
- Every mutation either invalidates explicitly or documents why it does not.
- A disabled action explains why it is disabled.
