# Quickstart Validation: Profile Ingestion

Run after `001-cv-tailor-v1-mvp` is delivered. Each step states what to observe.

## Prerequisites

- A built backend with a configured model chain, or `LLM_PROVIDER=fake` for the
  offline path.
- Two fixture CVs: one PDF with a text layer and one DOCX.
- A scanned PDF and a legacy `.doc` for the rejection checks.

## 1. Build a draft from one PDF

```bash
PYTHONPATH=backend/src uv run python -m cvtailor.cli ingest \
  --profile software-engineer --create --file fixtures/cv.pdf --json
```

Observe: the command returns after the sections settle, with a `draft_id`, state
`complete`, per-section statuses, item counts, and a readiness verdict. Nothing is
written to the profile: without a decisions file, `ingest` stops at the draft.
`data/ingestions/<draft_id>/` exists; the PDF is not there.

While it runs, the terminal prints one line per section as it settles.

## 2. Inspect quotes and variants

```bash
PYTHONPATH=backend/src uv run python -m cvtailor.cli ingest show <draft_id>
```

Observe: each item shows both language variants, which one came from the file, the
translated one marked with its source text, and the verification result with a page
reference.

## 3. Prove the guarantee

Edit one item in the draft JSON to a sentence that is not in the file (test only),
then re-read the draft.

Observe: the item is `unverified` and `approve` fails with `draft_not_approvable`.
Editing the text by hand turns it `user_edited` and it can then be approved.

## 4. Review and commit

```bash
PYTHONPATH=backend/src uv run python -m cvtailor.cli ingest review <draft_id>
```

Approve a few items, run `approve-verified`, then `commit`.

Observe: the summary reports `added`, `skipped`, and the breakdown by status, and
`added + skipped` equals the item count. The master file exists with a timestamped
backup beside it, and the draft directory is gone.

The scripted equivalent:

```bash
PYTHONPATH=backend/src uv run python -m cvtailor.cli ingest \
  --profile software-engineer --file fixtures/cv.pdf \
  --decisions decisions.json --json
```

## 5. The new profile renders

```bash
PYTHONPATH=backend/src uv run python -m cvtailor.cli tailor \
  --profile software-engineer --posting fixtures/posting.txt --non-interactive
```

Observe: a one-page PDF in Portuguese, with no English text leaking into it.

## 6. Refusals

- **Not renderable**: reject every summary with `lead` and commit. Observe
  `master_not_renderable`, a missing list, and the draft still present.
- **No decisions**: ingest without a decisions file and confirm nothing was written
  to the profile.
- **Legacy `.doc`**: observe `unsupported_file` with guidance.
- **Oversized file**: observe `file_too_large` before any extraction work.

## 7. Partial files

Ingest a good PDF together with a scanned one.

Observe: the draft is built from the good file; the scanned file is listed as skipped
with a warning naming it; the exit code is still success. Then ingest only the scanned
file and observe `no_text_layer` and a non-zero exit.

## 8. Duplicates

Ingest the same PDF twice into the same profile and commit both.

Observe: the second draft marks items `duplicate`, cannot approve them, and the master
does not grow. Then move one bullet's text under a different role in a fixture and
confirm it is accepted.

## 9. Partial failure and retry

Force a section to fail (point the chain at an unreachable provider, or use a scripted
fake that fails `education`).

Observe: the draft still contains the other sections and ends in `complete`, `education`
is `failed`, and `retry SECTION` re-runs only that section from the stored text while
keeping the decisions already made. If every section fails, the draft ends in `failed`.

## 10. Bilingual review

Take an item whose source variant is Portuguese.

Observe: the English variant is present, marked as translated, and shows the Portuguese
source text beside it. One approval accepts both. Rejecting the item discards both, and
editing marks it `user_edited`.

## 11. Privacy and lifetime

Search the draft directory, the master, the logs, and every API response for the
original file name, its bytes, and the API key.

Observe: none appear. Only extracted blocks and the `sha256` of the file remain.

Then age a draft past seven days (test clock) and make any ingestion request.

Observe: the draft is gone and its id answers `draft_not_found`.

## Checklist

- [ ] A text-layer PDF yields blocks with page references.
- [ ] An invented quote cannot be approved.
- [ ] A hyphenated line break still verifies.
- [ ] Every item arrives with both variants, the translated one marked.
- [ ] A failed section leaves a usable draft and can be retried.
- [ ] `ingest` without decisions never writes the profile.
- [ ] Commit counts close and break down by status.
- [ ] Commit creates a profile that renders in Portuguese, with a backup.
- [ ] A non-renderable master is refused and the draft survives.
- [ ] Duplicates are blocked; the same text under another role is accepted.
- [ ] A bad file is skipped with a warning; all bad files fail the upload.
- [ ] The source file is never stored and never echoed.
- [ ] An abandoned draft disappears after seven days.
