# HTTP Contract: Profile Ingestion

Entity shapes are in [data-model.md](../data-model.md). Errors use the existing
`{code, message}` shape with the codes listed there.

**Base URL**: `http://127.0.0.1:8000`. The same CORS rule as 001 applies.

**Invariants**

- The uploaded file never appears in a response, and is never stored server-side.
- Extracted text appears only through the draft read route, per block, as context.
- No route commits without an explicit commit request.
- A response never contains an API key.

## POST /api/ingestions

Creates a draft from one or more files.

Request: multipart form with:

| Field | Type | Rules |
| --- | --- | --- |
| `profile` | string | Target slug. |
| `create_if_missing` | boolean | Default false. |
| `files` | file[] | 1 to 5 files, each up to 10 MB, PDF or DOCX. |

Response `202`, immediately:

```json
{
  "id": "20261114T150000Z-1a2b",
  "state": "processing",
  "profile": "software-engineer",
  "create_if_missing": true,
  "sources": [{"name": "cv.pdf", "bytes": 182000, "hash": "9f2c...", "format": "pdf"}],
  "sections": {
    "person": {"state": "pending", "reason": null, "attempts": 0},
    "experience": {"state": "pending", "reason": null, "attempts": 0}
  },
  "items": [],
  "readiness": {"ready": false, "missing": ["no items yet"]},
  "extraction": {"blocks": 42, "characters": 7800, "files_read": 1, "files_skipped": []}
}
```

Sections settle in the background and are read through the draft route. A draft whose
every section fails ends in `state: failed`; a draft that stops moving past the budget
ends in `state: stalled`.

Failures at create: `400 unsupported_file` (every file rejected), `400
unreadable_file`, `400 too_many_files`, `413 file_too_large`, `422 no_text_layer`
(every file without text), `422 extraction_limit_exceeded`. A provider failure is
never a create failure; it shows up as `state: failed`.

## GET /api/ingestions/{id}

Returns the draft, including per-item decisions and, for each item, the block that
contains its quote so the UI can show context.

Response `200`: the same shape as create with the current `state`, plus items and the
blocks their quotes came from:

```json
{
  "id": "20261114T150000Z-1a2b",
  "state": "complete",
  "items": [
    {
      "id": "it-001",
      "kind": "bullet",
      "section": "experience",
      "parent": "role1",
      "fields": {"en": "Led the migration to Kubernetes.", "pt": "Liderou a migracao para Kubernetes."},
      "quote": "Led the migration to Kubernetes.",
      "source_language": "en",
      "translated_variant": "pt",
      "source_text": "Led the migration to Kubernetes.",
      "verification": {"verified": true, "block_index": 4, "offset": 128, "reason": null},
      "warnings": [],
      "duplicate": false,
      "status": "pending"
    }
  ],
  "blocks": [{"index": 4, "location": "page 2", "text": "Led the migration to Kubernetes."}]
}
```

Failures: `404 draft_not_found`.

## POST /api/ingestions/{id}/decisions

Decides one item.

Request:

```json
{ "item_id": "it-001", "action": "edit", "text": "Led the Kubernetes migration." }
```

Response `200`: updated counts and readiness.

```json
{
  "counts": {"pending": 3, "approved": 12, "rejected": 1, "duplicate": 2, "unverified": 1},
  "readiness": {"ready": true, "missing": []}
}
```

Failures: `404 draft_not_found`, `409 draft_not_approvable` (approving an
unverified or duplicate item), `400 invalid_selection`-shaped validation for an edit
that empties required text.

## POST /api/ingestions/{id}/approve-verified

Approves every `pending`, verified, non-duplicate item in one request.

Response `200`: the affected count plus updated counts and readiness.

Failures: `404 draft_not_found`.

## POST /api/ingestions/{id}/retry-section

Request:

```json
{ "section": "experience" }
```

Response `200`: the updated section status and any new items. Existing decisions are
preserved.

Failures: `404 draft_not_found`, `409 section_not_failed` (the section already
succeeded), `503 model_unavailable`.

## POST /api/ingestions/{id}/commit

Writes the master and deletes the draft.

Response `200`:

```json
{
  "profile": "software-engineer",
  "created": true,
  "added": 12,
  "skipped": 5,
  "skipped_breakdown": {"pending": 1, "rejected": 2, "unverified": 0, "duplicates": 2},
  "master_path": "software-engineer/master.json"
}
```

`added + skipped` equals the number of items in the draft; the breakdown explains
every skipped item.

Failures: `404 draft_not_found`, `422 master_not_renderable` with a `missing` list,
`409 draft_not_approvable` when no item is approved.

## DELETE /api/ingestions/{id}

Discards the draft and its extracted text.

Response `204`.

Failures: `404 draft_not_found`.
