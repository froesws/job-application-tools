# Phase 1 Data Model: Market Corpus Reader

Everything here is read-only. The models describe what the reader derives from the
append-only corpus file; none of them is persisted.

## CorpusRecord

The shape 001 writes, consumed as-is.

| Field | Type | Rules |
| --- | --- | --- |
| `hash` | string | Dedup key. A repeated hash counts once. |
| `date` | string | Run date, ISO 8601. The only date the range filters read; the digest's posting date is never used for filtering. |
| `detected_language` | `pt-BR` \| `en-US` | Informational; not filtered in this version. |
| `digest` | JobDigest | Supplies enterprise, level, hard skills, and soft skills. |

A record missing `digest.hard_skills` still counts toward levels and companies; it just
contributes no skills. A malformed line is skipped and counted in `ignored`.

## MarketSample

The filtered set every report is computed over.

| Field | Type | Rules |
| --- | --- | --- |
| `postings` | CorpusRecord[] | Deduplicated by hash, in file order. |
| `total` | integer | Count after filters. |
| `ignored` | integer | Lines skipped as malformed. |
| `small_sample` | boolean | True when `total < 10`. |
| `filters` | Filters | Echo of what was applied. |

## Filters

| Field | Type | Rules |
| --- | --- | --- |
| `level` | string \| null | One of `trainee`, `junior`, `mid_level`, `senior`. |
| `company` | string \| null | Case-insensitive exact match on `enterprise_name`. |
| `since` | date \| null | Inclusive. |
| `until` | date \| null | Inclusive. |

Filters apply to the sample, so every share and every denominator uses the filtered
`total`.

## SkillStat

| Field | Type | Rules |
| --- | --- | --- |
| `skill` | string | Canonical form after alias mapping. |
| `label` | string | Most frequent original spelling, for display. |
| `kind` | enum | `hard` or `soft`; hard rows are the default, soft rows appear only with `--include-soft`. |
| `count` | integer | Distinct postings containing it. |
| `share` | number | `count / total`, 0 to 1. |

## PairStat

| Field | Type | Rules |
| --- | --- | --- |
| `given` | string | The skill the user asked about, canonical form. |
| `skill` | string | The co-occurring skill. |
| `both` | integer | Postings containing both. |
| `given_count` | integer | Postings containing the given skill. |
| `probability` | number | `both / given_count`, 0 to 1. |

Rows below `--min-count` on `both` are omitted. The report states the minimum used.

## LevelStat

| Field | Type | Rules |
| --- | --- | --- |
| `level` | string | One of the four values. |
| `count` | integer | Postings at that level. |
| `share` | number | `count / total`. |

## CompanyStat

| Field | Type | Rules |
| --- | --- | --- |
| `company` | string | Most frequent spelling after case folding and trimming. |
| `count` | integer | Postings naming it after that normalization. |
| `share` | number | `count / total`. |

Suffixes are never stripped: `Acme` and `Acme Corp` stay separate rows, because merging
them is a heuristic that can fuse two different companies.

## Report

The CLI's typed result before formatting.

| Field | Type | Rules |
| --- | --- | --- |
| `kind` | enum | `skills`, `pairs`, `levels`, `companies`. |
| `sample` | MarketSample | Always carried, so the formatter can print the notice. |
| `rows` | array | One of the four row types. |
| `min_count` | integer \| null | Present for `pairs` only. |

## Formatting rules

- Text output prints the sample first (`12 postings, 1 line ignored`), then the warning
  when `small_sample`, then the rows.
- Percentages print with one decimal; the raw counts always appear beside them.
- JSON output carries the same numbers unformatted, plus `small_sample` and `ignored`.
- Ordering is applied before formatting, so text and JSON agree exactly.

## ValidationReport

Produced by `stats validate`; never persisted.

| Field | Type | Rules |
| --- | --- | --- |
| `postings` | integer | Records that parsed into a usable entry. |
| `errors` | Finding[] | Unreadable file, non-JSON line, record without a hash, invalid date. |
| `warnings` | Finding[] | Duplicate hash, missing digest, empty skill list, ambiguous company. |
| `ok` | boolean | True when `errors` is empty. Drives the exit code. |

## Finding

| Field | Type | Rules |
| --- | --- | --- |
| `level` | enum | `error` or `warning`. |
| `code` | string | Stable, for scripting: `unreadable_file`, `invalid_json`, `missing_hash`, `invalid_date`, `duplicate_hash`, `missing_digest`, `empty_skills`, `ambiguous_company`. |
| `line` | integer \| null | 1-based line number, absent for file-level findings. |
| `detail` | string | Short, no posting text. |

Validation never mutates the corpus and never changes what a normal report shows.

## Validation rules that live in code

- A `--level` outside the four values is a usage error, not an empty report.
- `--since` after `--until` is a usage error.
- A pair request for a skill absent from the sample returns an empty report with an
  explicit message, not an error.
- `probability` is never computed when `given_count` is zero.
