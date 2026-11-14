# Implementation Plan: Profile Ingestion

**Branch**: `002-profile-ingestion` | **Date**: 2026-11-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-profile-ingestion/spec.md`

## Summary

Build the master profile from the CV files the candidate already has. The backend
extracts text from PDF and DOCX, asks a model for master items one section at a
time, and verifies in code that every proposed item carries an exact quote from the
extracted text. The result is a draft the user approves item by item; a commit
appends approved items to the profile with generated ids and a timestamped backup,
and refuses to write a master that would not render. Every item is proposed
bilingual: one variant is verified by quote, the other is translated from it and
marked `translated`, and one decision approves both.

Delivered after the 001 pipeline and before the frontend, because the first screen
a user meets is uploading a CV.

## Technical Context

**Language/Version**: Python 3.14.4, same environment as 001.

**Primary Dependencies**: `pypdf` 7.1.0 for PDF text layers and `python-docx` 1.2.0
for DOCX, both verified against CPython 3.14 on 2026-11-14. Everything else already
exists: FastAPI, Pydantic 2, pytest, httpx, the `LLMClient` layer, the profile
storage, and the renderer's validator.

**Storage**: `data/ingestions/<id>/` holding `draft.json` and `blocks.json`. The
uploaded file is read into memory, extracted, and dropped. Drafts are removed on
commit, on discard, and by a seven-day lazy sweep.

**Processing model**: the create request returns as soon as extraction finishes and
the sections are proposed by one background thread per draft inside the running
process. No new service and no worker process; the client polls the draft route for
per-section progress. A draft that stops moving past the budget becomes `stalled`.

**Testing**: pytest at the HTTP API seam with a scripted fake model and fixture
files; the quote verifier tested directly as a pure function; the CLI at its process
boundary.

**Target Platform**: Local backend, localhost only. No new service, no worker.

**Project Type**: The same web application plus CLI as 001; this spec adds backend
capabilities and CLI commands, not a new process.

**Performance Goals**: 60 seconds per model call, 600 seconds per ingestion, 10 MB
per file, 5 files per draft.

**Constraints**: No OCR, no legacy `.doc`, never store the source file, never
auto-commit, never write a master that fails the renderer's validator.

**Scale/Scope**: One user, a handful of files per profile, one draft at a time.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
Evaluated against constitution v2.2.0.

| Gate | How the plan satisfies it | Verdict |
| --- | --- | --- |
| I. Master profile is the single source of facts | An item enters the draft only with an exact quote verified in code; it enters the master only after per-item approval. A translation enters only from an already-approved item, adds no claim, and is marked `translated` | PASS |
| II. Code owns validation and deterministic decisions | Extraction, normalization, quote verification, duplicate detection, id generation, and the renderability check are pure code. The model only proposes | PASS |
| III. Untrusted input, isolated secrets | Uploaded content is delimited as data with an ignore-instructions rule; the file is never stored; drafts are git-ignored; no file content in logs or responses | PASS |
| IV. Human review before artifacts leave | Every item is decided by the user; commit requires approval; readiness is shown before committing | PASS |
| V. Provider-agnostic LLM layer | Ingestion reuses the existing `LLMClient`, chains, retries, and admission mark; no new transport | PASS |
| VI. Fixed pipeline and deliberate scope | Ingestion is a fixed sequence of steps; no agent framework; two new dependencies, justified in Complexity Tracking | PASS |
| Core stays pure | Extraction and verification are pure functions over bytes and text; no FastAPI, storage, or service imports | PASS |
| No unresolved clarification | Decisions are recorded in [research.md](./research.md) | PASS |

No gate fails.

**Post-design re-check** (after Phase 0 and Phase 1): still PASS. The data model
adds no place where model text reaches the master without a decision, and the
contracts expose readiness before commit.

## Project Structure

### Documentation (this feature)

```text
specs/002-profile-ingestion/
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0 decisions
├── data-model.md        # Phase 1 entities
├── contracts/
│   ├── api.md
│   └── cli.md
└── quickstart.md
```

### Source Code

```text
backend/src/cvtailor/
├── core/
│   ├── extraction.py    # bytes -> blocks, deterministic, no model
│   ├── quotes.py        # normalization and verification
│   ├── ingestion.py     # draft building, duplicates, readiness, ids
│   └── render_pdf.py    # existing; its validator defines readiness
├── agents/
│   ├── prompts.py       # existing; gains ingestion prompts
│   └── ingest.py        # one call per section
├── storage/
│   ├── drafts.py        # draft persistence, discard, cleanup
│   └── profiles.py      # existing; gains atomic append with backup
├── api/
│   ├── routes.py        # ingestion routes
│   └── schemas.py       # upload, decision, and draft models
└── cli.py               # ingest, ingest show, ingest review
```

**Structure Decision**: no new layer. Extraction and verification are pure and live
in `core` beside the renderer, which already imports a third-party library for a
deterministic transformation. Draft persistence joins `storage`. The model calls
join `agents`, where the prompt builders already live. The routes join `api`.

### Delivery Order

Each slice ends in a commit and has an explicit "Done when" condition.

**I1 — Upload a PDF and read its blocks.**
Scope: extraction, draft storage, draft read endpoint, CLI `ingest show`.
Done when: a text-layer PDF yields blocks with page indexes; a scanned PDF fails
with `no_text_layer`; the source file is gone from disk; a draft can be read and
discarded.

**I2 — Quotes and the first section.**
Scope: normalization, verification, one section call (experience), verification
results in the draft.
Done when: a faithful quote verifies with its block and offset; an invented one is
`unverified` and cannot be approved; a hyphenated line break still verifies.

**I3 — All sections, partial success, and retry.**
Scope: the eight sections, asynchronous polling, per-section budget, `section_failed`,
`retry_section`, all-sections-failed as `state: failed`.
Done when: create returns before the sections finish and polling shows them settle; a
failed section does not sink the draft; the budget cut reports `budget_exhausted`;
retry re-runs one section from stored text and keeps decisions.

**I4 — Decisions, bilingual review, and readiness.**
Scope: approve, reject, edit, `approve_verified`, the bilingual item with its marked
translation, readiness verdict.
Done when: one decision approves both variants; the translated variant shows its
source text; edited items are marked `user_edited`; bulk approve skips unverified and
duplicate items; readiness lists what the master would still miss.

**I5 — Commit.**
Scope: merge into a new or existing profile, generated ids, timestamped backup,
renderability validation, additive counts.
Done when: a new profile is created and renders; an existing profile gains items
without changes to old ones; a master without a lead summary is refused with
`master_not_renderable` and the draft survives; the counts close and break down.

**I6 — Duplicates, person, and the translation rule.**
Scope: parent-scoped duplicate detection, the person item checks, and enforcement of
the v2.2.0 rule that a translated variant carries its source text.
Done when: re-upload adds no duplicate; the same bullet under another role is
accepted; phone variants with different digits are rejected; no translated variant
exists without its source text.

**I7 — CLI.**
Scope: `ingest`, `ingest review`, exit codes.
Done when: the non-interactive mode emits one JSON object; the review loop approves,
rejects, edits, retries, and commits; exit codes match the contract.

## Complexity Tracking

| Item | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| `pypdf` and `python-docx` dependencies | The candidate's CVs exist as PDF and DOCX, and the whole feature is reading them. | Asking the user to export plain text defeats the entry point; shelling out to external tools adds a system dependency worse than a Python package. |
| Extraction inside `core` | Extraction is deterministic and must be tested exhaustively; it is the same shape as the renderer. | Putting it in `storage` would misname persistence as I/O-bound work and hide it from the pure-function tests. |
