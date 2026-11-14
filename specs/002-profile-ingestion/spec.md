# Profile Ingestion — v1

**Feature Branch**: `002-profile-ingestion`
**Created**: 2026-11-14
**Status**: ready-for-agent
**Depends on**: `001-cv-tailor-v1-mvp` (profiles, storage, service, CLI, API)

## Problem Statement

The tailoring pipeline needs a master profile written as a large JSON document with
stable ids, EN and PT text, and a fixed schema. Writing that by hand is slow, easy to
get wrong, and blocks the first real use of the tool: without a master there is
nothing to select from, the deterministic fallback ranks nothing, and no model can be
evaluated. The candidate already has that information — it is in their existing CV
files, in one or more PDFs and DOCX documents, sometimes split across a Portuguese
and an English version.

The risk in copying that content automatically is the one the constitution treats as
non-negotiable: a model must not introduce a claim the candidate never made. Copying
text out of a file is safe only if every extracted sentence can be traced back to the
exact place in the file it came from, and only if the candidate approves each item
before it enters the master.

## Solution

The candidate drops one or more CV files into the app and names the profile. The
backend extracts the text, asks a model to propose master items, and verifies in code
that every proposal carries an exact quote that appears in the extracted text. The
result is a draft: proposed items grouped by master section, each showing its quote,
its verification status, and both language variants — the one taken from the file and
the one translated, marked as such. Nothing is written to the master until the candidate
decides on each item. Approved items receive generated ids and are appended to the
profile's master, which is backed up first. The profile then appears in the existing selector and the
tailoring pipeline can use it immediately.

The same flow is available from the CLI, including a non-interactive mode that emits
JSON, so a profile can be built or updated without the web UI.

## User Stories

### Upload and sources

1. As a job seeker, I want to upload a PDF of my CV, so that I do not have to retype my history.
2. As a job seeker, I want to upload a DOCX of my CV, so that the tool works with the format I already maintain.
3. As a job seeker, I want to upload more than one file into the same draft, so that a Portuguese and an English version can become one profile.
4. As a job seeker, I want a clear rejection when a file is too large, so that I know to split or compress it instead of waiting for a failure.
5. As a job seeker, I want a clear rejection when a file is corrupt or not a real PDF or DOCX, so that I can fix the file instead of guessing.
6. As a job seeker, I want a scanned PDF rejected with an explicit "no text layer" message, so that I understand the tool does not read images.
7. As a job seeker, I want a legacy `.doc` rejected with guidance to save it as DOCX or PDF, so that I am not left with a silent failure.
8. As a job seeker, I want the original file discarded after extraction, so that the source documents do not pile up on disk.

### Draft and quotes

9. As a job seeker, I want the draft grouped by master section (person, roles, summaries, skills, experience, research, projects, education, certifications), so that I can review it in the same shape as the master.
10. As a job seeker, I want every proposed item to show the exact quote from my file, so that I can judge whether the proposal is faithful.
11. As a job seeker, I want each quote to point to the section or line it came from, so that I can find it in the original document.
12. As a job seeker, I want an item with an unverified quote to be impossible to approve, so that no invented sentence can enter my master.
13. As a job seeker, I want to see why a quote failed verification, so that I can decide whether to retype it myself.
14. As a job seeker, I want to read the surrounding extracted text of an item, so that I can confirm the context before approving.
15. As a job seeker, I want the draft to stay a draft until I commit it, so that a bad extraction never touches my master.
16. As a job seeker, I want to discard a draft entirely, so that a wrong upload leaves no trace.

### Approval

17. As a job seeker, I want to approve an item individually, so that I control exactly what enters the master.
18. As a job seeker, I want to reject an item individually, so that a correct-but-unwanted bullet stays out.
19. As a job seeker, I want to edit an item's text before approving it, so that I can fix wording without retyping from scratch.
20. As a job seeker, I want an edited item marked as edited by me, so that the record distinguishes a quote from a rewrite.
21. As a job seeker, I want to approve every verified item at once and still review them afterwards, so that a large CV does not require dozens of clicks.
22. As a job seeker, I want to see how many items are pending, approved, rejected, or duplicated before committing, so that I know what the commit will do.
23. As a job seeker, I want committing to write the master with a timestamped backup first, so that a bad commit is recoverable.
24. As a job seeker, I want the commit to report how many items were added, skipped, or marked as already present, so that I can confirm the outcome.
25. As a job seeker, I want unapproved items left out of the commit rather than blocking it, so that one bad item does not stop a good profile.

### Creating and updating a profile

26. As a job seeker, I want ingestion to create a new profile when the slug does not exist, so that onboarding starts from the files I have.
27. As a job seeker, I want ingestion to update an existing profile, so that a new CV version adds what is missing without rebuilding everything.
28. As a job seeker, I want items already present in the master detected and marked as duplicates, so that repeated uploads do not create a second copy of every bullet.
29. As a job seeker, I want existing items never overwritten without my approval, so that reviewed wording survives a re-import.
30. As a job seeker, I want generated ids that are readable and stable, so that selections and reports stay understandable.
31. As a job seeker, I want approved items appended in a predictable order per section, so that the CV reads sensibly after an import.
32. As a job seeker, I want the new profile to appear in the selector in name order, so that it is usable immediately after onboarding.

### Bilingual items

33. As a job seeker, I want every proposed item to arrive in both languages, so that one decision yields a CV I can send in either language.
34. As a job seeker, I want to see which variant came from my file and which was translated, so that I know what I am trusting.
35. As a job seeker, I want the translation shown beside the source text, so that I can judge it without opening the original.
36. As a job seeker, I want to edit or reject an item whose translation is wrong, so that a bad translation never reaches the CV.

### Privacy and safety

37. As a job seeker, I want my CV files and extracted text to stay on my machine, so that personal data never leaves it beyond the model call.
38. As a job seeker, I want the file content and the API key kept out of logs and API responses, so that nothing private is exposed by accident.
39. As a job seeker, I want drafts stored in a git-ignored folder, so that personal data cannot be committed.
40. As a job seeker, I want a draft to disappear once committed or discarded, so that stale drafts do not accumulate.
41. As a job seeker, I want the model instructed to ignore any instruction found inside my CV text, so that a document cannot redirect the extraction.

### Command line

42. As a CLI user, I want to ingest one or more files into a profile without the UI, so that onboarding can be scripted.
43. As a CLI user, I want a non-interactive mode that emits JSON and exits with a stable code, so that tests and automation can rely on it.
44. As a CLI user, I want an interactive review loop that shows each item with its quote and lets me approve, reject, or edit, so that reviewing away from the UI is practical.
45. As a CLI user, I want to resume an existing draft by id, so that a long review can be interrupted.

### Failures

46. As a job seeker, I want a clear message when every model in the chain fails, so that I know the draft could not be produced.
47. As a job seeker, I want a clear message when a file yields too little text to build a profile, so that I do not commit an empty master.
48. As a job seeker, I want a clear message when the extracted text exceeds the processing limit, so that I can split the upload.
49. As a job seeker, I want to see whether the profile would render before I commit, so that I never write an unusable master.
50. As a job seeker, I want to retry a failed section without uploading the file again, so that one bad section does not cost me the whole draft.
51. As a job seeker, I want to know when the time budget cut off the remaining sections, so that I can retry exactly those.
52. As a job seeker, I want to watch each section settle while the draft builds, so that I know it is working and where it stalled.
53. As a job seeker, I want an abandoned draft to disappear after a week, so that my CV text does not sit on disk forever.

## Implementation Decisions

### Boundary and trust

- Ingestion is a backend concern. Extraction, quote verification, draft storage, and
  master writes happen in the Python backend; the frontend only uploads files and
  shows the draft.
- File content is untrusted. Prompts delimit the extracted text as data and instruct
  the model to ignore instructions inside it.
- The model proposes items and quotes. It never writes the master and never assigns
  ids.

### Extraction

- Accepted formats: PDF with a text layer, and DOCX. Legacy `.doc` and images are
  rejected with distinct error codes.
- PDF text is read with `pypdf` 7.1.0; DOCX with `python-docx` 1.2.0. Both were
  resolved against CPython 3.14 before this spec was written.
- A file that yields fewer than 200 extractable characters is treated as having no
  text layer. That file is skipped with a visible warning naming it; the draft
  continues with the files that produced text. If every file is skipped, the upload
  fails with the code of the first rejection.
- Extraction is a pure function from file bytes to structured text: a list of blocks
  with their source page or paragraph index. It is deterministic and testable
  without a model.
- The uploaded file is read into memory, extracted, and dropped. It is never stored
  in the draft directory.
- Limits: 10 MB per file, up to 5 files per draft, and a total extracted-text cap of
  200,000 characters that fails the draft rather than truncating it silently.

### Model calls

- The model is called once per section: person, summaries, skills, experience,
  research, projects, education, certifications. Each call returns only items for its
  section, each with its quote and its translated variant, constrained to a schema.
- Each section gets bounded validation retries with the errors fed back, following the
  existing LLM layer rules.
- Budget: 60 seconds per call and 600 seconds for the whole ingestion. When the budget
  is exhausted, sections not yet processed are marked `section_failed` with reason
  `budget_exhausted` and the draft is returned with whatever succeeded.
- A failed section never invalidates the rest of the draft. The draft exposes a
  `retry_section` action that re-runs only that section from the stored extracted
  text, keeps every decision already taken, and does not require a new upload.
- When every section fails, the draft ends in `state: failed` and the client reports
  it as `model_unavailable`. A partial draft is never reported as a failure.

### Quote verification

- Verification is code, not a model judgement. A quote is verified when, after
  normalization, it appears contiguously in the extracted text of a source block.
- Normalization: Unicode NFC, de-hyphenation of a line break (a hyphen followed by a
  line break and a lowercase word joins the word), collapse runs of whitespace to a
  single space, unify curly quotes and dashes to their ASCII forms, and strip leading
  and trailing whitespace. The same normalizer runs on the extracted text and on the
  quote, so verification compares like with like.
- Comparison is case-sensitive; case folding would let a rewritten sentence pass as a
  quote.
- Verification returns, for each quote, a boolean plus the source block index and the
  character offset in the normalized text, so the UI can show context.
- An item whose quote fails verification is created with status `unverified` and
  cannot be approved. The only path for it is to be edited by the user, which marks
  it `user_edited` and no longer claims to be a quote.

### Draft model

- A draft holds: its id, the target profile slug, whether the profile will be
  created, the source file names and their hashes, the extraction summary, the
  per-section status (`ok`, `pending`, or `section_failed` with its reason), the
  proposed items, and per-item decisions.
- The draft also holds a readiness verdict computed by the same validator the
  renderer uses, listing what the resulting master would still be missing. Readiness
  is shown before commit, so an unusable master is visible early.
- Each proposed item carries: its kind (person, role option, summary block, skill
  group, experience entry, role, bullet, research item, project, education entry,
  certification), its proposed field values, its quote, the verification result, a
  duplicate check against the target master, and a status of `pending`,
  `approved`, `rejected`, `inapplicable`, `duplicate`, or `unverified`.
- The draft never writes to the master. Only an explicit commit does.

### Approval and commit

- Decisions are per item: `approve`, `reject`, and `edit`. `edit` replaces the item's
  text and marks it `user_edited`; from then on the item no longer claims to be a
  quote, because the user is the author.
- `approve_verified` is a bulk action restricted to items that are `pending`,
  verified, and not duplicates. It reports the affected counts, and every decision
  stays individually reversible until commit. Unverified, duplicate, and
  `section_failed` items are never included.
- `retry_section` re-runs one failed section from the stored extracted text and keeps
  existing decisions.
- Commit is allowed while some items are still pending or rejected; those are left
  out and reported. Commit is refused when no item is approved.
- The commit summary is additive: added plus skipped equals the total item count, and
  skipped is broken down by pending, rejected, unverified, and duplicates.
- Commit first computes the master that would result and validates it with the same
  rules the renderer needs: at least one role option, at least one summary block with
  `lead`, and at least one experience role with bullets. Failure returns
  `master_not_renderable` with the missing list; nothing is written and the draft
  survives.
- Commit then writes the master atomically: read the current master (or initialize an
  empty one for a new profile), append approved items, write a timestamped backup
  of the previous master, then replace the file.
- Ids are generated at commit from the item's kind and the first words of its text,
  made unique within the master. Ids never come from the model.
- Duplicate detection is scoped to the parent and the kind: a bullet is compared with
  the bullets of its matched role or research item, an experience entry with entries
  by header and dates, a role with roles by title and dates, a project with projects,
  a summary with summaries, and a role option with role options. Comparison is exact
  after normalization (NFC, de-hyphenation, collapsed whitespace, casefolded); no
  fuzzy matching. A duplicate cannot be approved and is reported as already present.
- Committing into an existing profile never modifies an existing item; it only
  appends. Changing an existing item is out of scope for this spec.
- After a successful commit the draft is deleted. A failed commit leaves both the
  master and the draft intact.

### Person

- `person` is a single draft item whose proposal carries the whole object.
- Code checks, not the model: `phone_intl` and `phone_local` must contain the same
  digits; the name and the email must appear in the extracted text.
- `location_en` and `location_pt` are language variants of one fact, so they follow
  the translation rule below: the proposal carries the source location text and is
  marked `translated`.

### Bilingual items

- Every master text field is bilingual. At ingestion, one variant is taken from the
  file and verified by quote; the other is translated from it and marked `translated`
  on that field. One decision approves both.
- The translated variant carries its source text and a short reason, so the reviewer
  sees what it was derived from without opening the original file.
- The translated variant must introduce no claim absent from its source. Numbers,
  named entities, technologies, and scope must survive; a changed number or entity
  raises a warning on the item, and approval is still the user's call.
- Rejecting an item rejects both variants. Editing one variant marks the item
  `user_edited`; the other variant is regenerated only if the user asks for it, never
  silently.
- No translation is produced or applied during tailoring or rendering.

### API

- Create a draft: upload one or more files with the target profile slug and a
  create-if-missing flag. Returns `202` at once with the draft id and
  `state: processing`; sections settle in the background, and the client polls the
  draft route to watch them. A draft whose every section fails ends in `state:
  failed`. Inference never blocks the request for the whole budget.
- A draft past its seven-day lifetime is deleted during the next ingestion request;
  its id then answers `draft_not_found`.
- Read a draft: returns items, verification results, duplicates, counts, per-section
  status, the readiness verdict with its missing list, and the extraction summary.
  The extracted text is available per block for context, never as the original file.
- Decide an item: body holds the item id and the action (`approve`, `reject`,
  `edit`), plus the edited text when the action is `edit`. Returns the updated counts.
- Approve verified as a batch: one request approving every `pending`, verified,
  non-duplicate item, returning the affected counts.
- Retry a failed section: body holds the section name; the section is re-run from the
  stored extracted text and existing decisions are preserved. Refused with
  `section_not_failed` when the section already succeeded.
- Commit a draft: validates the resulting master, writes it, and returns the profile
  summary with added, skipped, and duplicate counts.
- Discard a draft: deletes it.
- Errors follow the existing `{code, message}` shape. New stable codes:
  `unsupported_file`, `file_too_large`, `too_many_files`, `no_text_layer`,
  `unreadable_file`, `extraction_limit_exceeded`, `draft_not_found`,
  `draft_not_approvable`, `master_not_renderable`, `section_not_failed`.

### CLI

- `ingest` takes a profile slug, one or more file paths, an optional create flag,
  non-interactive and JSON flags, and an optional decisions file.
- Without a decisions file, `ingest` builds the draft and stops; nothing is committed.
  A decisions file supplies explicit `{item_id, action}` entries, which are applied
  and then committed. There is no auto-approval path.
- `ingest review DRAFT_ID` runs the interactive loop: show both variants with the
  translated one marked, the quote, the verification result and the duplicate state,
  print the readiness verdict and per-section status, and accept `approve`, `reject`,
  `edit`, `approve-verified`, `retry SECTION`, `next`, `prev`, and `commit`.
- `ingest show DRAFT_ID` prints the draft as JSON.
- Exit codes follow the existing CLI contract; a draft that cannot be produced exits
  with the model-unavailable code, and an unsupported file exits as a usage error.

### Storage

- Drafts live under the git-ignored data root in their own directory, holding the
  draft JSON and the extracted text blocks.
- Source files are never stored. Draft directories are removed on commit, on discard,
  and on the seven-day sweep.
- The master write reuses the existing profile storage module and its timestamped
  backup rule.

## Testing Decisions

A good test asserts observable behavior at the outermost boundary that can express
the rule. It does not reach into private functions, assert call order, or mock the
domain. External, nondeterministic edges — the model and the file system — are
replaced; the domain is real.

### Seams

- **Primary seam: the HTTP API.** Tests create a draft from fixture files with a
  scripted fake model, read the draft, decide items, and commit, then assert the
  saved master and the counts. This single seam covers extraction wiring, prompt
  construction, draft storage, approval, commit, backup, duplicate detection, and
  error serialization.
- **Second seam: the quote verifier as a pure function.** Exactness is the
  constitution's core guarantee, and its edge cases (whitespace, curly quotes,
  dashes, accents, hyphenation across lines) are cheaper and clearer as unit tests
  than as API round trips. The verifier returns a result object; tests assert on
  that object.
- **Third seam: the CLI process boundary.** Non-interactive ingestion and the review
  loop are verified as processes: exit codes, JSON on stdout, and artifacts on disk.
  These tests never re-check domain rules already covered at the API seam.

No fourth seam is introduced for PDF or DOCX parsing. The file format is an input
fixture; the observable result is the extracted block list and the draft built from
it. A parser bug surfaces there.

### Modules under test

- Extraction: PDF with a text layer, DOCX, empty text layer, corrupt file, size and
  count limits, one bad file among good ones, and every file bad.
- Quote verification: exact match, whitespace collapse, curly quotes and dashes,
  NFC normalization, case sensitivity, hyphenated line breaks, non-contiguous quote.
- Draft building: item grouping by section, per-section failure with partial success,
  retry of one section from stored text, a bilingual item reviewed in one decision,
  and the translated variant marked with its source text.
- Duplicate detection: the same bullet text is a duplicate inside one role and is
  accepted under a different role; re-upload matches by parent and kind.
- Approval: per-item decisions, edit marking, `approve_verified` excluding
  unverified and duplicate items, counts, commit with pending items, refusal when
  nothing is approved.
- Commit: refusal with `master_not_renderable` and the missing list, new profile
  creation, append into an existing profile, backup creation, id generation and
  uniqueness, atomicity on failure, and an additive summary whose counts close.
- Lifecycle: the create request returns before the sections finish, polling shows
  them settle, every-section failure ends in `failed`, and a draft older than seven
  days is swept.
- Security: file content and key absent from responses and logs; prompt delimiters
  present.

### Prior art

The API seam, the scripted fake model, and the CLI boundary tests come from
`001-cv-tailor-v1-mvp`. The pure-function tests follow the renderer's pattern: a
deterministic core with no model in the loop, exercised directly.

## Out of Scope

- OCR of scanned PDFs or images.
- Legacy `.doc`, `.rtf`, `.odt`, and HTML files.
- Reading a CV from a URL or a cloud drive.
- Editing or deleting existing master items; this spec only appends.
- Automatic approval, auto-commit, or a "trust this model" mode.
- Multi-user uploads, accounts, or server-side storage of source files.
- Profile deletion or renaming.
- Tailoring, rendering, the report, and the market corpus, which belong to
  `001-cv-tailor-v1-mvp`.
- The ingestion screen itself, which is delivered by `specs/005-frontend`.

## Further Notes

- **Constitutional basis.** Principle I names the ingestion draft as the only
  exception to "models never author CV text": an item may enter the draft only with
  an exact quote verified in code and marked for review, and may enter the master
  only after per-item approval. Constitution v2.2.0 adds the translation carve-out: a
  translated variant may enter the draft only with the exact source text of the item
  it belongs to, introducing no claim absent from it, marked `translated`, and
  reviewed in the same decision as that source. The Localization Contract still
  forbids producing or applying a translation during tailoring or rendering.
- **Sequencing.** This spec is delivered after the pipeline core and before the
  frontend, so the first screen a user meets can be "upload your CV". It also
  unblocks the evaluation set, because must-include bullets come from a real master.
- **Dependencies.** `pypdf` 7.1.0 and `python-docx` 1.2.0 resolve on CPython 3.14 as
  of 2026-11-14; `uv add` remains the authority.
- **Tracker.** No issue tracker is configured in this repository; this spec is
  published as a file under `specs/` with `ready-for-agent` in the status line.
