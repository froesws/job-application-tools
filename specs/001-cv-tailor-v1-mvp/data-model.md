# Phase 1 Data Model: CV Tailor v1 MVP

Every entity below is defined as a Pydantic v2 model. Field names are English and
stable; the JSON on disk is the contract. Text that reaches the CV exists in the
master in both `en` and `pt` variants.

## Profile

A directory under `profile/`. The slug is both identity and display name.

| Field | Type | Rules |
| --- | --- | --- |
| `slug` | string | Directory name. Lowercase letters, digits, and hyphens. Unique. |
| `master` | MasterProfile | Loaded from `<slug>/master.json`. Required to tailor or render. |
| `has_blocklist` | boolean | True when `<slug>/blocklist.txt` exists. Only reported; no behavior depends on it. |

- Profiles are listed in slug order, which is the order the CLI and the UI show.
- Committed examples (`profile/master.example.json`, `profile/blocklist.example.txt`)
  sit outside profile directories and never appear in the listing.
- Backups are written beside the master as `master.json.bak.<UTC timestamp>`.

## MasterProfile

Source of truth for candidate facts inside one profile.

| Field | Type | Rules |
| --- | --- | --- |
| `person` | Person | Required. |
| `role_options` | RoleOption[] | At least one; `id` unique. |
| `summary_blocks` | SummaryBlock[] | At least one with `lead: true`. |
| `skills` | SkillGroup[] | At least one group. |
| `experience` | ExperienceEntry[] | At least one entry with at least one role. |
| `research` | ResearchItem[] | May be empty. |
| `projects` | Project[] | May be empty. |
| `education` | EducationEntry[] | May be empty. |
| `certs` | LocalizedText | Required. |

- **Person**: `name`, `phone_intl`, `phone_local`, `email`, `location_en`,
  `location_pt`, `links[]` with `label` and `url`.
- **RoleOption**: `id`, `en`, `pt`.
- **SummaryBlock**: `id`, `lead` (bool, optional), `en`, `pt`.
- **SkillGroup**: `label_en`, `label_pt`, `core[]`, `extra[]`, where an item is a
  plain string (same in both languages) or `{en, pt}`.
- **ExperienceEntry**: `header_en`, `header_pt`, `date_en`, `date_pt`, `roles[]`.
- **ExperienceRole**: `id`, `title_en`, `title_pt`, `date_en`, `date_pt`,
  `intro_en`, `intro_pt`, `bullets[]`.
- **Bullet**: `id`, `en`, `pt`.
- **ResearchItem**: `id`, `header_en`, `header_pt`, `date_en`, `date_pt`,
  `intro_en`, `intro_pt`, `bullets[]`.
- **Project**: `id`, `en`, `pt`.
- **EducationEntry**: `header_en`, `header_pt`, `date`, `desc_en`, `desc_pt`.
- **LocalizedText**: `{en, pt}`.

**Identity rules**: role ids are unique across all experience entries of the
profile; bullet ids are unique within their role or research item; summary, project,
research, and role-option ids are unique within their own collection. Ids are opaque
strings, never localized, and scoped to one profile.

## Selection

The only input the renderer accepts besides the master.

| Field | Type | Rules |
| --- | --- | --- |
| `language` | `pt-BR` \| `en-US` | Required at the API; mapped to `pt` \| `en` before rendering. |
| `role_id` | string | Must exist in the profile's `role_options`. |
| `summary_ids` | string[] | 1 to 4; each must exist; the first must have `lead: true`. |
| `skill_priority` | string[] | Each must match a core or extra skill item, case-insensitive. |
| `experience` | map role_id -> string[] | Each role 1 to 7 distinct bullet ids that belong to it. A role omitted from the map renders all its bullets in master order. |
| `research_ids` | string[] | Optional; each must exist. Omitted means all research items, in master order. |
| `research` | map research_id -> string[] | Same bullet rules as experience. |
| `project_ids` | string[] | Optional; each must exist. No count limit. |

**Validation**: `core/validation.py` merges the renderer's `validate_selection` with
the rules the renderer does not own — language enum mapping, blocklist check, and the
page-fit check after render. A failed check produces typed errors, never a partial
render.

## JobDigest

Fixed by the constitution. Stored as `digest.json` in every run and copied into the
corpus.

| Field | Type | Rules |
| --- | --- | --- |
| `enterprise_name` | string | Non-empty. |
| `date` | string | ISO 8601 date; posting date when stated, else the run date. |
| `job_title` | string | Non-empty. |
| `level` | enum | `trainee`, `junior`, `mid_level`, `senior`; aliases `pleno`, `mid level`, `mid-level` normalize to `mid_level`. |
| `resume` | string | Non-empty summary of the posting. |
| `hard_skills` | string[] | Non-empty items, deduplicated, each verified against the posting or an alias. |
| `soft_skills` | string[] | Non-empty items, deduplicated. |

**Normalization order**: trim, collapse whitespace, drop empty, drop duplicates,
normalize level aliases, verify skills, discard unknown fields. Any surviving failure
is a `digest_failure`.

**Derived**: `digest_hash = sha256(canonical_json(validated digest))`.

## Analysis

Rich internal artifact stored as `analysis.json`. Never returned with the raw posting.

| Field | Type | Rules |
| --- | --- | --- |
| `detected_language` | `pt-BR` \| `en-US` | Informational only. |
| `must_have_skills` | string[] | Subset of `hard_skills` marked as requirements. |
| `nice_to_have_skills` | string[] | Remaining hard skills. |
| `keywords` | Keyword[] | `{term, weight, source}` where source is `posting` or `alias`. |
| `pre_rank` | PreRank | Scores computed without a model. |

## PreRank

| Field | Type | Rules |
| --- | --- | --- |
| `roles` | map id -> number | Title overlap with `job_title` plus keyword matches. |
| `summary_blocks` | map id -> number | Keyword overlap; a lead block gets a fixed bonus. |
| `bullets` | map id -> number | Keyword coverage, normalized 0 to 1. |
| `skills` | map canonical_name -> number | Posting overlap. |
| `projects` | map id -> number | Keyword overlap. |
| `research` | map id -> number | Keyword overlap. |

Scores are deterministic for the same digest, profile, and alias table.

## GapReport

Computed after selection, stored in `report.md` and the run detail.

| Field | Type | Rules |
| --- | --- | --- |
| `gaps` | Gap[] | Hard skills with no mapped master item; `{skill, severity}`. |
| `coverage` | number | Covered hard skills divided by total hard skills, 0 to 1. |
| `red_flags` | RedFlag[] | `{code, message}`; codes: `level_mismatch`, `uncovered_must_have`, `blocklist_adjacent`, `auto_fit_trimmed`, `model_unadmitted`. |
| `section_counts` | SectionCounts | Selected items per section: summaries, experience bullets, research bullets, projects, skills. |
| `layout_warnings` | LayoutWarning[] | See below. |
| `checklist` | string[] | Fixed review items, English labels. |
| `models` | map step -> ModelAttempt[] | Model id, admission state, retries, errors, fallback flag. |

## LayoutWarning

| Field | Type | Rules |
| --- | --- | --- |
| `code` | enum | `font_scaled`, `bullets_trimmed`. |
| `detail` | string | Human-readable, English. |
| `removed_bullet_ids` | string[] | Present only for `bullets_trimmed`; the ids the cap dropped. |
| `font_scale` | number | Present only for `font_scaled`. |

`page_overflow` is not a warning; it is an error that stops the render.

## RunMetadata

Stored as `run.json` inside the run directory.

| Field | Type | Rules |
| --- | --- | --- |
| `id` | string | `YYYYMMDDTHHMMSSZ-xxxx`, UTC, sortable by prefix. |
| `schema_version` | integer | Starts at 1; bumped when an artifact shape changes. |
| `created_at` | string | ISO 8601 UTC. |
| `profile` | string | Slug of the profile the run used. Required. |
| `origin_run_id` | string \| null | Required for render runs; null for tailoring runs. |
| `mode` | enum | `tailor` or `render`. |
| `requested_language` | `pt-BR` \| `en-US` | What the user asked for. |
| `render_language` | `pt` \| `en` | What the renderer used. |
| `digest_hash` | string | sha256 of the validated digest. |
| `models` | map step -> ModelRecord | `{id, admitted}` per step. |
| `retries` | map step -> integer | Validation retries per step. |
| `fallback_used` | boolean | True when the deterministic fallback produced the selection. |
| `paths` | map name -> string | Relative artifact names, never absolute paths. |

**No snapshot**: the run does not copy the master. Re-rendering resolves ids against
the current profile and fails validation when one disappeared. The stored PDF remains
the record of what was produced.

## Run artifacts

One directory per run under `data/runs/<id>/`:

| File | Written by | Notes |
| --- | --- | --- |
| `run.json` | pipeline | `RunMetadata`. |
| `digest.json` | analyze | Contract fields only. |
| `analysis.json` | analyze | Copied to derived runs from the origin. |
| `selection.json` | tailor or render | The validated selection. |
| `cv.pdf` | render | One page, or the run fails. |
| `report.md` | report | Digest, counts, gaps, coverage, red flags, models, warnings, checklist. |
| `llm_log.jsonl` | llm | Only when logging is enabled; one JSON object per call. |
| `posting.txt` | tailor | Stored for reopening, never returned by the API. |

**Write order**: `.tmp-<id>/` receives every file, then the directory is renamed to
`<id>/`. Listing ignores `.tmp-*`.

**Immutability**: a derived run never modifies its origin; it records `origin_run_id`
and copies `digest.json` and `analysis.json`.

## CorpusEntry

One JSON object per line in `data/corpus.jsonl`. Written by a successful analyze,
independent of the run lifecycle.

| Field | Type | Rules |
| --- | --- | --- |
| `hash` | string | sha256 of the normalized posting text (whitespace collapsed, lowercased). Unique in the file; a repeat appends nothing. |
| `date` | string | Run date, ISO 8601. |
| `detected_language` | `pt-BR` \| `en-US` | From analysis. |
| `digest` | JobDigest | The seven contract fields. |

The posting text is never written to the corpus. Records are append-only; a
correction is a new line only if the posting text differs.

## Blocklist

`profile/<slug>/blocklist.txt`; one term per line; `#` starts a comment; blank lines
are ignored; matching is case-insensitive substring across every selected string.
A hit blocks the render and names the item id, never the matched term.

**Missing file** is treated as an empty list, with no warning. This is the accepted
trade-off: a new profile is unprotected until its blocklist is created.

## ModelChainConfig

Read from the environment by `settings/env.py`. Not part of the API surface.

| Field | Type | Default |
| --- | --- | --- |
| `analyze_chain` | `provider:model`[] | unset (configuration error) |
| `tailor_chain` | `provider:model`[] | unset (configuration error) |
| `call_timeout_s` | integer | 60 |
| `run_budget_s` | integer | 300 |
| `validation_retries` | integer | 2 |
| `vote_runs` | integer | 1 (or 3) |
| `prompt_logging` | boolean | false |

A provider is resolved through `llm/registry.py`, which maps a name to its default
base URL and key variable (`openai`, `openrouter`, `gemini`, `deepseek`). Adding a
provider is one registry entry; adding or switching a model is one configuration
line. The `fake` provider is valid for tests and demos and is never a default in a
real environment file.

## SettingsView

`GET /api/settings` response. Booleans and enumerations only.

| Field | Type | Rules |
| --- | --- | --- |
| `api_key_set` | boolean | Never the key. True when the active provider's key is present. |
| `chains` | map step -> ChainEntry[] | `{provider, model, admitted}` in order. |
| `admission` | object | `{evaluated: boolean, threshold_met: boolean}`; false until the evaluation follow-up. |
| `limits` | object | `posting_max_chars`, `call_timeout_s`, `run_budget_s`. |
| `version` | string | Application version. |

## Error model

Serialized as `{ "code": string, "message": string }`. `message` never contains
posting text, a key, a blocklisted term, or a path outside the run directory.

| Code | HTTP | Raised when |
| --- | --- | --- |
| `invalid_posting` | 400 | Empty, oversized, or wrong-type posting text. |
| `invalid_selection` | 400 | Unknown id, bad counts, missing lead block, or absent skill. |
| `blocklist_hit` | 400 | A selected string matches the profile's blocklist; `message` names item ids. |
| `profile_not_found` | 404 | Unknown profile slug. |
| `run_not_found` | 404 | Unknown run id, including a missing origin run. |
| `digest_failure` | 422 | The digest stays invalid after the retry budget. |
| `page_overflow` | 422 | The PDF still has more than one page after every auto-fit attempt. |
| `fallback_exhausted` | 422 | The deterministic fallback cannot satisfy the validator. |
| `model_unavailable` | 503 | Every model in the chain failed, timed out, or exceeded the run budget. |
| `configuration_error` | 500 | Unreadable master, missing chain, or unknown provider. |

## State transitions

```text
tailor:  posting -> analyzed(digest) -> pre_ranked -> tailored(selection)
         -> validated -> blocklisted -> rendered(pdf) -> reported
         on success: corpus line appended (once per unique posting)

render:  origin run -> selection validated against the current profile
         -> blocklisted -> rendered -> reported (derived run)

analyze step invalid  -> retry (<= validation_retries) -> digest_failure
tailor  step invalid  -> retry (<= validation_retries) -> fallback
fallback invalid      -> fallback_exhausted
pages > 1             -> page_overflow (no run is completed)
blocklist hit         -> blocklist_hit (no render, no run is completed)
```

A run directory exists only after the render succeeds; failed attempts leave no
readable run behind.
