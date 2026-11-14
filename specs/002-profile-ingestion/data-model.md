# Phase 1 Data Model: Profile Ingestion

Pydantic v2 models. Field names are English and stable; the JSON on disk is the
contract. Nothing here may carry a candidate claim that has no quote or an approved
source.

## IngestionDraft

| Field | Type | Rules |
| --- | --- | --- |
| `id` | string | `YYYYMMDDTHHMMSSZ-xxxx`, same scheme as runs. |
| `created_at` | string | ISO 8601 UTC. |
| `profile` | string | Target slug. |
| `create_if_missing` | boolean | Whether a missing profile directory is created at commit. |
| `sources` | SourceFile[] | Name, byte size, and `sha256` of each uploaded file. |
| `sections` | map section -> SectionStatus | One entry per section. |
| `items` | DraftItem[] | Every proposal, including rejected and duplicate ones. |
| `readiness` | Readiness | Recomputed after every decision. |
| `extraction` | ExtractionSummary | Block count, character count, files read, and files skipped with their reasons. |
| `state` | enum | `processing`, `complete`, `failed`, or `stalled`. |
| `updated_at` | string | ISO 8601 UTC; a draft in `processing` older than the ingestion budget becomes `stalled`. |

**State rules**: `processing` while any section is unsettled; `complete` when at least
one section succeeded and none is pending; `failed` when every section failed;
`stalled` when a processing draft stopped moving. A draft older than seven days is
deleted by the lazy sweep and answers `draft_not_found`.

**Sections**: `person`, `summaries`, `skills`, `experience`, `research`,
`projects`, `education`, `certifications`.

## SourceFile

| Field | Type | Rules |
| --- | --- | --- |
| `name` | string | Original file name, for display only. |
| `bytes` | integer | Size at upload. |
| `hash` | string | `sha256` of the file bytes. |
| `format` | enum | `pdf` or `docx`. |

The file itself is never stored. `hash` is what makes a re-upload recognisable.

## ExtractionBlock

| Field | Type | Rules |
| --- | --- | --- |
| `index` | integer | Position in the extracted sequence, stable for the draft. |
| `source` | string | Which uploaded file produced it. |
| `location` | string | Page number for PDF, paragraph index for DOCX. |
| `text` | string | Block text as extracted, before any normalization. |

## SectionStatus

| Field | Type | Rules |
| --- | --- | --- |
| `state` | enum | `ok`, `pending`, or `failed`. |
| `reason` | string \| null | `model_error`, `budget_exhausted`, `invalid_output`. |
| `attempts` | integer | Calls made, including retries. |

## DraftItem

| Field | Type | Rules |
| --- | --- | --- |
| `id` | string | Draft-local id, stable across decisions. |
| `kind` | enum | `person`, `role_option`, `summary_block`, `skill_group`, `experience_entry`, `role`, `bullet`, `research_item`, `project`, `education_entry`, `certification`, `translation`. |
| `section` | string | One of the eight sections. |
| `parent` | string \| null | The enclosing role, research item, or entry, used for duplicates and merge. |
| `fields` | object | The master-shaped values, always carrying both `en` and `pt` for every text field. |
| `quote` | string \| null | The text taken from the file. Absent for pure structure items. |
| `source_language` | enum | `en` or `pt`: the variant the quote came from. |
| `translated_variant` | enum \| null | The variant the model authored; it carries `source_text` and is marked `translated`. Null when the item needs no translation. |
| `source_text` | string \| null | Exact text of the verified variant, shown beside the translation. |
| `verification` | VerificationResult \| null | Present for every quoted item, and it verifies only the source variant. |
| `warnings` | string[] | `number_changed`, `entity_changed`, or empty, raised on the translated variant. |
| `duplicate` | boolean | True when the normalized text already exists under the same parent. |
| `status` | enum | `pending`, `approved`, `rejected`, `unverified`, `duplicate`, `user_edited`. |
| `decided_at` | string \| null | When the user decided. |

## VerificationResult

| Field | Type | Rules |
| --- | --- | --- |
| `verified` | boolean | Whether the normalized quote occurs in a block. |
| `block_index` | integer \| null | The block that contains it. |
| `offset` | integer \| null | Character offset in the normalized block text. |
| `reason` | string \| null | `not_found`, `empty_quote`, `no_blocks`. |

## Readiness

| Field | Type | Rules |
| --- | --- | --- |
| `ready` | boolean | True when the resulting master would render. |
| `missing` | string[] | Human-readable list of what the master still needs. |

The check mirrors the renderer: at least one role option, at least one summary block
with `lead`, and at least one experience role with at least one bullet.

## Bilingual review

There is no separate translation item. One `DraftItem` is one bilingual fact:

- The variant present in the file is the **source**; its quote is verified and
  `source_language` records which side it is.
- The other variant is **translated**; it carries the exact `source_text` and is
  marked `translated` on that field.
- One decision approves or rejects the item as a whole. Approving means accepting the
  quote and the translation together; the reviewer sees both before deciding.
- Rejecting discards both variants. Editing marks the item `user_edited`; the model is
  never asked to re-translate silently.

This is the carve-out in constitution v2.2.0: a translated variant enters only with
the exact source text of the item it belongs to, introducing no claim absent from it,
and reviewed in the same decision as that source.

## Decision

| Field | Type | Rules |
| --- | --- | --- |
| `item_id` | string | Must exist in the draft. |
| `action` | enum | `approve`, `reject`, `edit`. |
| `text` | string \| null | Required for `edit`; replaces the item text. |

Rules: `unverified` and `duplicate` items cannot be approved; `edit` moves the item
to `user_edited` and clears its verification claim; `approve_verified` acts only on
`pending` + verified + non-duplicate items.

## Error codes added by this feature

| Code | HTTP | Raised when |
| --- | --- | --- |
| `unsupported_file` | 400 | Not a PDF or DOCX, including legacy `.doc`. |
| `file_too_large` | 413 | Above the per-file cap. |
| `too_many_files` | 400 | Above the per-draft file cap. |
| `no_text_layer` | 422 | PDF pages yield too little text. |
| `unreadable_file` | 400 | Corrupt or truncated file. |
| `extraction_limit_exceeded` | 422 | Total extracted text above the cap. |
| `draft_not_found` | 404 | Unknown draft id. |
| `draft_not_approvable` | 409 | The item's status forbids the action. |
| `master_not_renderable` | 422 | The resulting master would not render; `missing` lists why. |
| `section_not_failed` | 409 | Retry requested for a section that already succeeded. |

## Lifecycle

```text
POST upload -> 202, state=processing (returns immediately)
            -> extraction (files skipped with warnings)
            -> sections settle one by one (ok | failed)
            -> state=complete when at least one section succeeded
            -> state=failed when every section failed
            -> state=stalled when processing outlives the budget

draft -> decisions (approve | reject | edit | approve_verified)
      -> ready? --no--> stay in draft
                --yes--> commit -> master written + backup -> draft deleted
      -> discard (any time) -> draft deleted
      -> 7 days untouched -> swept on the next ingestion request
```

A failed section, an unready master, or a failed commit never deletes the draft. Only
a successful commit, an explicit discard, or the seven-day sweep does. Commit counts
are additive: `added + skipped = total`, with `skipped` broken down by `pending`,
`rejected`, `unverified`, and `duplicates`.
