# HTTP Contract: CV Tailor v1 MVP

The FastAPI application generates the authoritative OpenAPI schema, checked in as
`backend/openapi.json`. This document states the behavior the schema must express.
Entity shapes are in [data-model.md](../data-model.md).

**Base URL**: `http://127.0.0.1:8000`. **Allowed origin**: the Vite development
origin only (`http://localhost:5173`). No other host may call the API.

**Invariants for every response**

- The posting text never appears in any response body.
- The API key never appears in any response, header, or log line.
- Only `/api/settings` reports key state, and only as a boolean.
- Artifact paths in responses are run-relative names, never absolute paths.
- Errors use `{ "code", "message" }` with the codes and statuses in the data model.

## POST /api/jobs/analyze

Turns posting text into a validated digest and appends one corpus record. Runs the
analyze step only; no profile is involved.

Request:

```json
{ "posting": "We are hiring a ...", "language": "pt-BR" }
```

`posting` is 1 to 100,000 characters. `language` is optional and only affects
detection reporting; it never translates the digest.

Response `200`:

```json
{
  "digest": {
    "enterprise_name": "Acme",
    "date": "2026-11-14",
    "job_title": "Backend Engineer",
    "level": "mid_level",
    "resume": "Builds and operates Python services.",
    "hard_skills": ["Python", "PostgreSQL"],
    "soft_skills": ["Ownership"]
  },
  "detected_language": "en-US",
  "digest_hash": "3f9c...",
  "corpus_appended": true,
  "models": { "analyze": { "id": "provider/model-id", "admitted": false } },
  "retries": { "analyze": 0 }
}
```

`corpus_appended` is false when the same normalized posting is already in the corpus.

Failures: `400 invalid_posting`, `422 digest_failure`, `503 model_unavailable`.

## GET /api/profiles

Response `200`:

```json
{
  "profiles": [
    { "slug": "data-scientist", "has_blocklist": false },
    { "slug": "software-engineer", "has_blocklist": true }
  ]
}
```

Always in slug order. Only directories containing `master.json` are listed.

## GET /api/profiles/{slug}

Response `200`: the profile's master, exactly as stored, so the UI can resolve labels
and offer valid edits. Read-only; version 1 has no write endpoint.

Failures: `404 profile_not_found`, `500 configuration_error` (unreadable master).

## POST /api/tailor

Runs analyze, pre-rank, tailor, validate, blocklist, render, and report against a
profile. Writes a complete run and appends a corpus record when the posting is new.

Request:

```json
{ "posting": "We are hiring a ...", "profile": "software-engineer", "language": "pt-BR" }
```

`profile` is required. `language` is optional and defaults to `pt-BR`.

Response `201`: run summary (below).

Failures: `400 invalid_posting`, `400 blocklist_hit`, `404 profile_not_found`,
`422 digest_failure`, `422 page_overflow`, `422 fallback_exhausted`,
`503 model_unavailable`.

## POST /api/render

Validates and renders a supplied selection with no model call. `origin_run_id` is
required: there is no bare selection render in version 1.

Request:

```json
{
  "profile": "software-engineer",
  "origin_run_id": "20261114T143012Z-9f3a",
  "selection": {
    "language": "pt-BR",
    "role_id": "sweng",
    "summary_ids": ["s1"],
    "skill_priority": ["Python"],
    "experience": { "role1": ["b1", "b2"] },
    "research_ids": [],
    "research": {},
    "project_ids": ["p1"]
  }
}
```

Response `201`: run summary with `origin_run_id` set. The new run copies the origin's
`digest.json` and `analysis.json` and records `mode: render`. The origin is never
modified.

Failures: `400 invalid_selection`, `400 blocklist_hit`, `404 profile_not_found`,
`404 run_not_found` (unknown origin), `422 page_overflow`, `500 configuration_error`.

## GET /api/runs

Response `200`:

```json
{
  "runs": [
    {
      "id": "20261114T143012Z-9f3a",
      "created_at": "2026-11-14T14:30:12Z",
      "profile": "software-engineer",
      "enterprise_name": "Acme",
      "job_title": "Backend Engineer",
      "level": "mid_level",
      "requested_language": "pt-BR",
      "pages": 1,
      "fallback_used": false,
      "origin_run_id": null,
      "has_report": true
    }
  ]
}
```

Sorted newest first. Runs whose directory is incomplete or unreadable are skipped,
not returned as errors.

## GET /api/runs/{id}

Response `200`:

```json
{
  "summary": { "id": "...", "profile": "software-engineer", "pages": 1, "fallback_used": false },
  "digest": { "...": "constitution fields only" },
  "selection": { "...": "validated selection" },
  "analysis": {
    "detected_language": "en-US",
    "must_have_skills": ["Python"],
    "nice_to_have_skills": ["PostgreSQL"],
    "keywords": [{ "term": "python", "weight": 3, "source": "posting" }],
    "pre_rank": { "roles": {}, "summary_blocks": {}, "bullets": {} }
  },
  "review": {
    "gaps": [{ "skill": "PostgreSQL", "severity": "must_have" }],
    "coverage": 0.5,
    "red_flags": [{ "code": "uncovered_must_have", "message": "..." }],
    "section_counts": { "summaries": 1, "experience_bullets": 2, "research_bullets": 0, "projects": 1, "skills": 1 },
    "layout_warnings": [{ "code": "bullets_trimmed", "detail": "...", "removed_bullet_ids": ["b3"] }],
    "checklist": ["Confirm the enterprise name.", "Check the page count."]
  },
  "models": { "analyze": { "id": "provider/model-id", "admitted": false }, "tailor": { "id": "provider/model-id", "admitted": false } },
  "retries": { "analyze": 0, "tailor": 1 },
  "artifacts": { "cv": "cv.pdf", "report": "report.md", "llm_log": null }
}
```

The response never contains the posting.

Failures: `404 run_not_found`.

## GET /api/runs/{id}/cv.pdf

Returns `application/pdf` with `Content-Disposition: inline; filename="<id>.pdf"`.
The PDF contains CV content only: no gaps, red flags, model notes, or layout
warnings.

Failures: `404 run_not_found` (including when the artifact is missing).

## GET /api/runs/{id}/report.md

Returns `text/markdown; charset=utf-8` with the report as written at run time.

The report contains, in order: digest, selected section counts, gaps, coverage, red
flags, models with admission state, retries, fallback status, layout warnings, and
the review checklist.

Failures: `404 run_not_found`.

## GET /api/settings

Response `200`:

```json
{
  "api_key_set": true,
  "chains": {
    "analyze": [{ "provider": "openrouter", "model": "deepseek/deepseek-chat", "admitted": false }],
    "tailor": [{ "provider": "gemini", "model": "gemini-2.5-flash", "admitted": false }]
  },
  "admission": { "evaluated": false, "threshold_met": false },
  "limits": { "posting_max_chars": 100000, "call_timeout_s": 60, "run_budget_s": 300 },
  "version": "0.1.0"
}
```

No values beyond these. The key, the base URL, and any credential never appear.

## CORS and binding

The server binds to `127.0.0.1`. CORS allows exactly one origin, configured by
`FRONTEND_ORIGIN` (default `http://localhost:5173`), with `GET, POST` and the
`Content-Type` header. No wildcard origin.
