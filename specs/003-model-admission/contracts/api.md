# HTTP Contract: Model Admission

Entity shapes are in [data-model.md](../data-model.md). Errors use the existing
`{code, message}` shape. The screen consumes these routes through the generated client.

**Invariants**

- No response carries an API key, a base URL, or a credential.
- The set's posting texts are returned only by the set route, which the screen needs to
  annotate them.
- Admitting never modifies configuration; there is no route that writes `.env`.
- A run's archive is written whether it passes or fails.

## GET /api/eval/set?profile=slug

Returns the set for a profile.

Response `200`:

```json
{
  "profile": "software-engineer",
  "version": "b41c...",
  "complete": true,
  "postings": [
    {
      "id": "p01",
      "text": "Backend engineer. Python, PostgreSQL.",
      "expected_role_id": "sweng",
      "must_include_ids": ["b1", "b5"],
      "added_at": "2026-11-14"
    }
  ]
}
```

`complete` is true only when exactly ten postings load and every annotation resolves
against the profile.

Failures: `404 profile_not_found`, `422 invalid_eval_set` with the problem list.

## POST /api/eval/postings

Adds a posting, by pasted text or by importing a stored run posting.

Request:

```json
{ "profile": "software-engineer", "text": "Backend engineer...", "from_run_id": null }
```

`text` and `from_run_id` are mutually exclusive; `from_run_id` copies the posting text
that run stored.

Response `201`: the created posting. An eleventh posting is refused while the set is
full.

Failures: `404 profile_not_found`, `404 run_not_found`, `409 eval_set_full`.

## PATCH /api/eval/postings/{id}

Updates an annotation.

Request:

```json
{ "expected_role_id": "sweng", "must_include_ids": ["b1", "b5"] }
```

Response `200`: the posting plus the new `version`.

Failures: `404 posting_not_found`, `422 unknown_role` / `unknown_bullet`,
`422 empty_must_include`.

## DELETE /api/eval/postings/{id}

Removes a posting, freeing one slot.

Response `204`.

Failures: `404 posting_not_found`.

## POST /api/eval/runs

Starts an evaluation. Returns immediately.

Request:

```json
{ "provider": "openrouter", "model": "deepseek/deepseek-chat", "profile": "software-engineer", "majority": false }
```

Response `202`:

```json
{ "run_id": "20261114T170000Z-4c1d", "state": "running", "progress": {"scored": 0, "total": 10} }
```

Failures: `404 profile_not_found`, `422 invalid_eval_set`, `500 configuration_error`.

## GET /api/eval/runs/{id}

Polls a run.

Response `200`:

```json
{
  "run_id": "20261114T170000Z-4c1d",
  "state": "running",
  "progress": {"scored": 6, "total": 10},
  "outcomes": [
    {"posting_id": "p01", "outcome": "valid", "role_ok": true, "recall": 1.0}
  ]
}
```

When `state` is `complete`, the response also carries `metrics`, `verdict`, and
`archive`. A run whose every posting errored still completes; the metrics show why it
failed.

Failures: `404 run_not_found`.

## POST /api/eval/admissions

Records an admission.

Request:

```json
{ "provider": "openrouter", "model": "deepseek/deepseek-chat", "profile": "software-engineer", "archive": "eval/results/....json" }
```

`archive` is optional; the latest passing archive for that model is used.

Response `201`: the admission record.

Failures: `404 archive_not_found`, `409 admission_refused` (`failed_threshold` or
`stale_archive`), `404 profile_not_found`.

## DELETE /api/eval/admissions/{provider}/{model}

Withdraws an admission for the current profile.

Response `204`.

Failures: `404 admission_not_found`.

## GET /api/settings?profile=slug

Existing route, extended.

Response `200`:

```json
{
  "api_key_set": true,
  "profile": "software-engineer",
  "chains": {
    "analyze": [
      {"provider": "openrouter", "model": "deepseek/deepseek-chat", "state": "admitted", "reason": null, "admitted_at": "2026-11-14", "metrics": {"valid": 10, "role_ok": 10, "mean_recall": 0.96}}
    ],
    "tailor": [
      {"provider": "gemini", "model": "gemini-2.5-flash", "state": "stale", "reason": "prompt_changed", "admitted_at": null, "metrics": null}
    ]
  },
  "limits": {"posting_max_chars": 100000, "call_timeout_s": 60, "run_budget_s": 300},
  "version": "0.1.0"
}
```

The profile defaults to the first profile in slug order. `state` is `admitted`, `stale`,
or `unadmitted`.
