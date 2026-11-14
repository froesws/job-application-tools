# Quickstart Validation: Frontend

Run after `001`, `002`, and `003` expose their APIs, and after `backend/openapi.json` is
checked in. Each step states what to observe.

## Prerequisites

- Backend running with `LLM_PROVIDER=fake` and a profile created (by ingestion or by hand).
- Node 26 and npm 11.
- At least one run created by the CLI, and an evaluation set plus one evaluation run.

## 1. Install and generate types

```bash
cd frontend
npm install
npm run generate:api
npm run dev
```

Observe: `src/api/schema.d.ts` is generated from the checked-in schema, the dev server
starts, and the shell renders with five destinations.

## 2. Shell and profile selector

Observe: the selector lists profiles in slug order, with a badge for profiles that have a
blocklist. Reload the page — the selected profile survives because it is in the URL.
Choose a profile and confirm the URL changes.

Then stop the backend and reload.

Observe: an explicit "backend unreachable" surface with a retry, not a blank page.

## 3. Settings

Open `/settings?profile=<slug>`.

Observe: key presence as a boolean, chains with admission state, and limits. The key is
never rendered, not even masked. A `stale` entry shows its reason.

## 4. History

Open `/runs`.

Observe: runs newest first with date, profile, enterprise, title, language, and page count.
Open one: digest, selection, warnings, and the report link. A derived run links to its
origin. With no runs, the empty state points at `/tailor`.

## 5. Tailoring

Open `/tailor?profile=<slug>`, paste a posting, submit.

Observe: a labelled loading state, then the digest and the proposed selection. The posting
input is cleared. The preview shows the actual PDF. Both downloads work and are separate.

Open the browser's network tab and confirm the posting appears in exactly one request and
in no response.

## 6. Editing and re-render

Change the role, remove a bullet, reorder two bullets, and toggle a project.

Observe: "Re-render" enables only after the first edit. Clicking it posts to
`/api/render` with the origin run and no analysis call. A new row appears in history with
a link to the origin.

Then remove a required bullet to make the selection invalid.

Observe: the error names the offending item and the previous run stays intact.

## 7. Ingestion

Open `/ingest?profile=<slug>` and upload a text-layer PDF plus a scanned one.

Observe: per-section progress rows settle one by one; the scanned file is listed by name
as skipped; the draft appears with both variants per item, the translated one marked.
Approve, reject, edit, and bulk approve; then commit.

Observe: a refused commit shows the missing list and keeps the review; a successful commit
returns to the profile list with the new profile selected.

## 8. Evaluation

Open `/eval?profile=<slug>`.

Observe: the ten postings with annotations and the set version. Capture one by pasting and
one by importing a run. Change an annotation.

Observe: the invalidation warning names the models that would become stale before saving.

Run the evaluation.

Observe: per-posting progress, then the three metrics and the verdict. Admit the model —
a confirmation is required — and confirm the state becomes admitted in Settings. Withdraw
and confirm it returns to unadmitted.

## 9. Gates

```bash
make check
```

Observe: `tsc --noEmit`, `vitest run`, and `vite build` run alongside the backend gates. A
deliberately broken type fails the check.

## 10. Accessibility pass

Navigate every route with the keyboard only.

Observe: focus is visible, every action is reachable, every input is labelled, and no state
is conveyed by colour alone.

## Checklist

- [ ] Types are generated from the checked-in schema, not hand-written.
- [ ] The profile survives a reload and drives every screen.
- [ ] The backend-unreachable state is explicit.
- [ ] Every screen has labelled loading, empty, and error states.
- [ ] The key is never rendered; settings shows booleans and admission state only.
- [ ] The posting is sent once and never returned or persisted.
- [ ] Edits re-render with the origin and never re-analyze.
- [ ] Ingestion shows section progress, skipped files, and both variants.
- [ ] Evaluation lists, captures, annotates with a warning, runs, and admits with confirmation.
- [ ] `make check` includes typecheck, tests, and build.
- [ ] Keyboard-only navigation reaches every action.
