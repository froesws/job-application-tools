# Phase 0 Research: Profile Ingestion

Each unknown from the plan's Technical Context is resolved here.

## 1. PDF extraction library

**Decision**: `pypdf` 7.1.0. Text is read per page and split into blocks on blank
lines and bullet markers, each block recording its page index.

**Rationale**: Pure Python, no system dependency, resolves on CPython 3.14, and
reads the text layer of the CVs the user actually has. Page-level provenance is
enough to show context for a quote.

**Alternatives considered**: `pdfplumber` (better layout reconstruction, heavier and
pulls `pdfminer.six`); `PyMuPDF` (fast, but a compiled dependency); shelling out to
`pdftotext` (a system dependency worse than a Python package).

## 2. DOCX extraction

**Decision**: `python-docx` 1.2.0. Paragraphs and table cells are read in document
order, each block recording its paragraph index.

**Rationale**: DOCX is the format a user is most likely to still edit. Tables carry
real content in many CVs, so they are read rather than skipped.

**Alternatives considered**: unzipping and parsing the XML directly (reimplements the
library); converting to PDF first (adds a converter).

## 3. Scanned PDFs and legacy `.doc`

**Decision**: A PDF whose pages yield less than a documented minimum of extractable
characters fails with `no_text_layer`. `.doc` fails with `unsupported_file` and a
message telling the user to save as DOCX or PDF.

**Rationale**: OCR is a non-goal in the constitution and would make the text
unverifiable against the original pixels. `.doc` has no reliable pure-Python reader
without LibreOffice.

**Alternatives considered**: OCR via Tesseract (a system dependency and a different
verification story); asking LibreOffice to convert (a heavy system requirement).

## 4. Where extraction lives

**Decision**: `core/extraction.py`, a pure function from bytes and a filename to a
list of blocks. No file system access inside it.

**Rationale**: Same shape as the renderer: deterministic, library-backed,
exhaustively testable. Keeping it in `core` means the quote verifier can be tested
against real extraction output without a server.

**Alternatives considered**: a new `extraction` layer (the constitution fixes six
layers, and this is not a layer); `storage` (storage means persistence).

## 5. Quote normalization

**Decision**: Unicode NFC; a hyphen followed by a line break and a lowercase word
joins the word; curly quotes and dashes unify to ASCII; whitespace runs collapse to
one space; ends are trimmed. Comparison is case-sensitive.

**Rationale**: PDF extraction breaks words across lines and changes punctuation.
Normalizing both sides identically keeps the check honest: nothing passes that was
not there. Case folding is deliberately excluded because it would let a rewritten
sentence pass as a quote.

**Alternatives considered**: fuzzy matching or edit distance (makes the guarantee
unpredictable); case-insensitive comparison (weakens the only real defence).

## 6. Model call shape

**Decision**: one call per section, eight sections, two validation retries per
section, 60 seconds per call, 600 seconds per ingestion. A section that fails or
runs out of budget becomes `section_failed` with a reason, and the draft survives.

**Rationale**: a 40-item response from a weak free model fails often and fails
entirely. Per-section calls isolate the failure and match the constitution's
"narrow the model's job".

**Alternatives considered**: one call for the whole CV (long JSON, total failure on
one bad field, retry re-sends everything); one call per file (still long, and the
PT and EN files would compete for the same sections).

## 7. Draft storage and lifecycle

**Decision**: `data/ingestions/<id>/draft.json` plus `blocks.json`, both git-ignored.
The uploaded file is never written. A draft is deleted on successful commit or on
discard.

**Rationale**: the extracted text is needed for context and for `retry_section`, so
it must outlive the request; the original file is not needed once extracted, and
keeping it would double the personal data on disk.

**Alternatives considered**: keeping the source file (privacy and size); rebuilding
from the file on retry (the file is gone by design).

## 8. Id generation

**Decision**: ids are generated at commit from the item kind and the first words of
its text, slugified, with a numeric suffix when the id already exists in the master.

**Rationale**: readable ids make selections and reports legible; generation at commit
means the model never controls identity.

**Alternatives considered**: UUIDs (unreadable in a selection file); ids from the
model (lets untrusted output choose identity).

## 9. Duplicate detection

**Decision**: scoped to the parent and kind. A bullet is compared with the bullets
of its matched role or research item; an entry with entries by header and dates; a
project with projects; a summary with summaries. Comparison is exact after
normalization.

**Rationale**: the same bullet under two employers is legitimate; a re-upload of the
same CV is not. Global dedupe would block the first case, and no dedupe would
duplicate the second.

**Alternatives considered**: global per kind (blocks legitimate repetition); fuzzy
matching (unpredictable approvals).

## 10. Readiness and commit time

**Decision**: readiness is computed with the renderer's own validator rule set: at
least one role option, at least one lead summary block, and at least one experience
role with bullets. The same check runs at commit and refuses with
`master_not_renderable`.

**Rationale**: a profile that cannot render is not a profile. Checking before the
write keeps the draft alive and the fix one item away.

**Alternatives considered**: committing and failing at the first tailoring (the
draft is already gone); synthesizing the missing structure (the system invents
structure silently).

## 11. Bilingual items, reviewed once

**Decision**: every item is proposed with both variants. The variant present in the
file is verified by quote and recorded as `source_language`; the other is translated
from it, carries the exact `source_text`, and is marked `translated` on that field.
One decision approves both.

**Rationale**: the master is bilingual by schema and the default output is Portuguese,
so the second variant is mandatory, not optional. A second approval pass would double
the review for every item and leave a window where a half-translated profile can be
committed. This is the carve-out in constitution v2.2.0: the translation carries the
source text, adds no claim, and is reviewed in the same decision as that source.

**Alternatives considered**: two passes with separate translation items (double the
decisions, and a commit window with missing variants); copying the source text into
the missing variant (the Portuguese CV would show English text); requiring both
language files (turns onboarding back into manual work).

## 12. Person item

**Decision**: one item carrying the whole person object. Code requires that
`phone_intl` and `phone_local` contain the same digits and that the name and email
appear in the extracted text. Location variants follow the translation rule.

**Rationale**: the master needs two phone formats and two location variants, while a
CV has one of each. The digit check catches the common error; the source check keeps
the claim anchored.

**Alternatives considered**: leaving contact fields empty (the profile never
renders); excluding person from ingestion (it was the manual-JSON problem).

## 13. Upload transport

**Decision**: multipart form upload on the ingestion create route. Files are read
into memory with a size check before extraction.

**Rationale**: multipart is what browsers and `curl -F` do natively, and the size cap
bounds memory.

**Alternatives considered**: base64 in JSON (33% larger and awkward in the browser);
a two-step presigned upload (needs object storage that does not exist here).

## 14. Asynchronous processing with polling

**Decision**: the create request returns `202` once extraction is done; sections are
proposed by one background thread per draft inside the running process. The client
polls the draft route, which reports per-section state. A draft that stops moving
past the budget becomes `stalled`.

**Rationale**: eight calls with retries can take minutes. A single synchronous
request of that length has no progress, loses everything on disconnect, and gives the
browser a reason to give up. A thread is not a new service and adds no dependency.

**Alternatives considered**: synchronous with the full budget (fragile, no progress);
synchronous with a shorter budget (most drafts would need section retries).

## 15. Draft lifetime

**Decision**: a draft untouched for seven days is deleted during the next ingestion
request; the id then answers `draft_not_found`.

**Rationale**: the draft holds the extracted CV text, which is personal data on disk.
The lazy sweep needs no scheduler, and seven days is long enough for a real review.

**Alternatives considered**: keep until commit or discard (personal data stays
indefinitely); delete on process exit (restarting the server would destroy a draft in
progress).

## 16. Partial file acceptance

**Decision**: a file yielding fewer than 200 characters is skipped with a warning
naming it, and the draft continues with the files that produced text. If every file
is skipped, the upload fails. Limits are 10 MB per file, five files, and 200,000
characters of extracted text.

**Rationale**: a scanned file among good ones should not force a re-upload of the
good ones; but an empty draft must not exist. The numbers accept short CVs and reject
scanned pages and pasted transcripts.

**Alternatives considered**: fail the whole upload on one bad file (forces a redo of
the good files); ignore bad files silently (the profile is quietly incomplete).

## 17. Additive commit counts

**Decision**: commit reports `added`, `skipped`, and `skipped_breakdown` by status, so
`added + skipped` equals the item count.

**Rationale**: the user and the tests need a sum that closes, and "skipped" alone does
not explain why an item was left out.

**Alternatives considered**: three parallel totals with duplicates outside skipped
(ambiguous); six raw counters (the caller re-implements the sum).
