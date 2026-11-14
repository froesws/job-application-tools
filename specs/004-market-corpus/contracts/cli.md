# CLI Contract: Market Corpus Reader

A read-only command group over the corpus. It owns argument parsing, terminal output, and
exit codes.

**Entry point**: `python -m cvtailor.cli` with the Makefile's `PYTHONPATH`.

## Shared flags

Every `stats` command accepts `--json` and reads the corpus from the data root. The
sample line is printed first in text mode:

```text
12 postings · 1 line ignored
```

When the sample is below ten, a warning follows:

```text
warning: only 6 postings; treat these numbers as anecdote, not pattern
```

## `stats skills`

```text
stats skills [--top N] [--level LEVEL] [--company NAME]
             [--since DATE] [--until DATE] [--include-soft] [--json]
```

Prints skills by posting count, then name:

```text
 7/12  58.3%  Python
 5/12  41.7%  PostgreSQL
 3/12  25.0%  Kubernetes
```

`--top` defaults to 20. `--level` accepts the four digest levels. Dates are inclusive
ISO 8601 dates and filter the record's run date, not the posting date. `--include-soft`
adds soft skills as their own rows; without it only hard skills are listed.

Exit codes: `0` success, `2` usage error, `3` corpus missing.

## `stats pairs`

```text
stats pairs SKILL [--min-count N] [--top N]
                  [--level LEVEL] [--company NAME]
                  [--since DATE] [--until DATE] [--json]
```

Answers `P(other | SKILL)`:

```text
given C#/.NET (5 postings)
 4/5  80.0%  RabbitMQ
 3/5  60.0%  SQL Server
```

Without `--min-count`, every pair is listed, ordered by joint count, so a
single-occurrence pair ranks last instead of disappearing. With `--min-count N`, pairs
below `N` are omitted and the output states the minimum used. A skill absent from the
sample prints an explicit empty-report line and exits `0`.

Exit codes: `0` success, `2` usage error, `3` corpus missing.

## `stats levels`

```text
stats levels [--json]
```

```text
 6/12  50.0%  mid_level
 3/12  25.0%  senior
 2/12  16.7%  junior
 1/12   8.3%  trainee
```

Exit codes: `0` success, `2` usage error, `3` corpus missing.

## `stats companies`

```text
stats companies [--top N] [--json]
```

```text
 2/12  16.7%  Acme
 1/12   8.3%  Globex
```

`--top` defaults to 20.

Exit codes: `0` success, `2` usage error, `3` corpus missing.

## `stats validate`

```text
stats validate [--json]
```

Reads the corpus without aggregating and reports findings.

```text
12 postings readable · 2 warnings

warning  line 7   duplicate_hash     a record with this hash already appeared
warning  line 9   missing_digest     record has no digest
```

Errors print the same way with `error` in place of `warning`. Error codes:
`unreadable_file`, `invalid_json`, `missing_hash`, `invalid_date`. Warning codes:
`duplicate_hash`, `missing_digest`, `empty_skills`, `ambiguous_company`.

Exit codes: `0` when there are no errors (warnings allowed), `1` when any error exists,
`2` usage error.

Validation never changes what a normal report shows: the reader keeps skipping malformed
lines and deduplicating hashes.

## JSON output

Every command prints one object:

```json
{
  "kind": "pairs",
  "sample": {"postings": 12, "ignored": 1, "small_sample": false},
  "filters": {"level": null, "company": null, "since": null, "until": null},
  "min_count": 2,
  "rows": [
    {"given": "c#/.net", "skill": "rabbitmq", "both": 4, "given_count": 5, "probability": 0.8}
  ]
}
```

Numbers are unformatted. `small_sample` is always present, so automation can refuse to
act on a thin sample.

## Read-only

No command writes to the corpus, to the profile, or to any file. The only output is
stdout, stderr, and the exit code.

## Errors

- `3` when the corpus file does not exist, with a message naming the expected path.
- `2` for an invalid level, an unparseable date, a reversed date range, or a negative
  `--top`.
- In a report, a malformed line never causes an error; it is counted as ignored. In
  `stats validate`, the same line is an error that exits `1`.
