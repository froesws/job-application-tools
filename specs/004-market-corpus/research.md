# Phase 0 Research: Market Corpus Reader

## 1. Where the aggregation runs

**Decision**: one pure module in `core` that takes a list of records and returns typed
results; the CLI formats them. No HTTP route in this version.

**Rationale**: the spec keeps the reader in the terminal, but the numbers should not be
trapped in a print statement. A pure module is testable with fixtures and reusable by a
future screen without rewriting the math.

**Alternatives considered**: aggregating inside the command (every test becomes a string
assertion); a database or index (thousands of records do not need one).

## 2. Loading the corpus

**Decision**: read the JSONL file line by line; a malformed line is skipped and counted;
a record missing a field is counted for the fields it has.

**Rationale**: the file is append-only and written by an older version of the product.
One corrupt line must not hide the other 400. Counting the skipped lines keeps the report
explainable.

**Alternatives considered**: failing on the first bad line (one bad append kills the
report); silently ignoring (the count would not add up).

## 3. Deduplication

**Decision**: records are deduplicated by `hash`, keeping the first occurrence.

**Rationale**: the writer is already idempotent, but a manual append or a future format
change could introduce a duplicate. Deduplicating on read makes every number independent
of how many times a record reached the file.

**Alternatives considered**: trusting the writer (a manual edit skews the stats);
deduplicating by enterprise and title (different postings can share both).

## 4. Skill normalization

**Decision**: case-fold and trim each skill; map through the same alias table the digest
verifier uses; display the most frequent original spelling for a canonical form.

**Rationale**: `JS`, `js`, and `JavaScript` are one skill, and so are `Postgres` and
`PostgreSQL` when the alias table says so. Reusing the pipeline's table keeps one
definition of "same skill" across the product.

**Alternatives considered**: exact string matching (splits the same skill across
spellings); a new normalization list (two sources of truth that drift).

## 5. Counts and shares

**Decision**: a skill's count is the number of distinct postings containing it; its share
is that count divided by the number of postings in the filtered sample.

**Rationale**: postings, not mentions, is the unit the user cares about: "asked for in 7
of 10 postings". Dividing by the filtered sample keeps a level or company filter honest.

**Alternatives considered**: counting occurrences (a posting that repeats a skill counts
twice); dividing by the whole corpus regardless of filters (the shares would not add to
the visible sample).

## 6. Conditional co-occurrence

**Decision**: `P(B | A)` is postings containing both divided by postings containing A,
printed with both counts. The reverse report answers `P(A | B)`.

**Rationale**: a percentage without its denominator is exactly the misleading number the
spec forbids. Both directions are offered because they answer different questions.

**Alternatives considered**: Jaccard or lift (harder to read and to check by hand);
a single symmetric score (loses the direction the user asked about).

## 7. Minimum co-occurrence count

**Decision**: no default. Every pair is listed, ordered by joint count, so a
single-occurrence pair ranks last instead of disappearing. `--min-count N` filters on
demand.

**Rationale**: the spec's story asks that a rare pair not outrank a real pattern, which
is ordering, not hiding. Hiding by default repeats the problem the sample warning
exists to solve: the number looks stronger because the user cannot see what was cut.

**Alternatives considered**: a default of 2 (silently drops data and invites doubt when
a known pair is missing); a proportional threshold (harder to explain).

## 8. Sample honesty

**Decision**: every report prints the number of postings considered, and warns when it is
below ten. The warning is part of both the text and the JSON payload.

**Rationale**: the spec's own example is a corpus of three postings, where any percentage
is noise. Ten is the point where a repeated pattern can appear twice.

**Alternatives considered**: no warning (the numbers look authoritative); a configurable
threshold (one more knob for a personal tool).

## 9. Ordering

**Decision**: count descending, then name ascending, for every report.

**Rationale**: equal counts must not shuffle between runs, or two invocations would
disagree and `--json` consumers would see churn.

**Alternatives considered**: insertion order (depends on file order); alphabetical only
(buries the signal).

## 10. JSON shape

**Decision**: each report has a JSON object with the sample (`postings`, `ignored`,
`small_sample`), the filter echo, and the rows. Numbers are numbers, not formatted
strings.

**Rationale**: the CLI prints text for humans; automation needs the raw values and the
sample size in the same payload.

**Alternatives considered**: JSON of formatted strings (unparseable); no JSON (the spec
requires it).

## 11. Read-only guarantee

**Decision**: the reader opens the corpus for reading and never rewrites it; a test
compares the file's bytes before and after each command.

**Rationale**: the spec promises that looking at statistics cannot change the data, and a
byte comparison is the only proof that survives refactoring.

**Alternatives considered**: trusting code review (a future "cleanup" could rewrite the
file); a read-only file mode (does not survive a copy).

## 12. Which date the range filters read

**Decision**: the record's own `date`, which is the run date. The digest's posting date
is not used for filtering.

**Rationale**: the run date is always present and has one meaning — "when this posting
passed through the tool". The digest's date falls back to the run date when the posting
states none, so filtering on it would silently mix two meanings.

**Alternatives considered**: the posting date (ambiguous and partial); both flags (two
timelines for one report).

## 13. Hard and soft skills

**Decision**: `stats skills` reads hard skills only. `--include-soft` adds the soft
entries as separate rows.

**Rationale**: a CV's skills section is built from hard skills. Soft entries appear in
almost every posting, so mixing them by default would push Python down the list and make
the shares harder to read.

**Alternatives considered**: both by default with a `--hard-only` flag (the main report
becomes a list of generic words); hard only, forever (leaves half the corpus unread).

## 14. Company grouping

**Decision**: case-fold and trim the company name for grouping, and display the most
frequent spelling. No suffix stripping.

**Rationale**: same rule as skills, and it is deterministic. Merging suffixes is a
heuristic that can fuse two different companies, and a wrong market number is worse than
a fragmented one.

**Alternatives considered**: strip Corp/Inc/Ltda (silent false merges); exact strings
(case variants split the count).

## 15. Validation severity

**Decision**: two levels. Errors — unreadable file, non-JSON line, record without a
hash, invalid date — exit `1`. Warnings — duplicate hash, missing digest, empty skill
list, ambiguous company — are listed and exit `0`. Normal reports keep tolerating both.

**Rationale**: the question validation answers is "can I trust these numbers". A
duplicate hash does not stop the reader from deduplicating, so failing on it would make
the command unusable in automation. A line that is not JSON does mean a record is
missing, which is worth a non-zero exit.

**Alternatives considered**: failing on any finding (one duplicate breaks the gate
forever); never failing (the command stops being a gate at all).

## 16. Terminal only

**Decision**: no HTTP route and no screen in this version.

**Rationale**: the reader needs nothing from the browser, and it can land before the
frontend exists. A screen would be a separate slice over the same pure module.

**Alternatives considered**: adding a route now (a surface with no consumer); a screen
now (the frontend does not exist yet).
