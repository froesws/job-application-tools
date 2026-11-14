# Quickstart Validation: Market Corpus Reader

Run after `001-cv-tailor-v1-mvp` has produced a corpus. Each step states what to observe.

## Prerequisites

- A corpus file at the data root, written by real runs, or the fixture corpus used below.
- The CLI entry point available through the Makefile's `PYTHONPATH`.

## 1. A fixture with known answers

Use a corpus of twelve records where the expectations are written down: four mention
Python, three mention Kubernetes, three mention both, and two of the four Python postings
also mention RabbitMQ.

Observe: every number in the following steps can be computed by hand from those four
sentences.

## 2. Empty corpus

Point the reader at an empty file.

```bash
PYTHONPATH=backend/src uv run python -m cvtailor.cli stats skills
```

Observe: an explicit "no postings yet" line, not a zero percentage, and exit code `0`.

Then point it at a path that does not exist.

Observe: exit code `3` and a message naming the expected path.

## 3. Levels first

```bash
PYTHONPATH=backend/src uv run python -m cvtailor.cli stats levels
```

Observe: the sample line (`12 postings`), then one row per level with `count/total` and a
share. The shares add to 100% within rounding.

## 4. Skill demand

```bash
PYTHONPATH=backend/src uv run python -m cvtailor.cli stats skills --top 5
```

Observe: Python first with `4/12 33.3%`, then Kubernetes with `3/12 25.0%`. Ordering is by
count, then name. Only hard skills appear: the fixture's soft skills are absent until you
add `--include-soft`, and then they appear as their own rows rather than mixed into the
ranking.

Now add a record using `JS` and another using `JavaScript` where the alias table maps them
to the same canonical skill.

Observe: they count once, and the label shown is the most frequent original spelling.

## 5. Filters narrow the sample

```bash
PYTHONPATH=backend/src uv run python -m cvtailor.cli stats skills --level senior
```

Observe: both the numerator and the denominator change — the sample line reports the
filtered total, and no share is computed against the unfiltered corpus.

Try `--company` the same way. For `--since` and `--until`, remember they filter the run
date — when the posting passed through the tool — not the date the posting was published.
Add a record with an older run date and confirm it drops out of a recent range while
staying in an older one. Then combine two filters and confirm the total shrinks again.

## 6. Co-occurrence with its denominator

```bash
PYTHONPATH=backend/src uv run python -m cvtailor.cli stats pairs Python
```

Observe: `2/4 50.0% RabbitMQ` for the fixture. The numerator and the denominator are both
printed.

Then ask the reverse question for a pair whose marginals differ, and confirm the
probability changes because the denominator changed.

## 7. Minimum count is on demand

Run step 6 without flags.

Observe: every pair is listed, ordered by joint count. A pair seen once appears last
rather than disappearing.

Then run with `--min-count 3`.

Observe: the RabbitMQ pair disappears because its joint count is 2, and the output states
the minimum used.

## 8. Honest small samples

Point the reader at a corpus of six postings.

Observe: the warning line appears in text mode, and `"small_sample": true` appears in JSON
mode. The numbers are still printed.

## 9. Ordering is stable

Run the same command twice and diff the output.

Observe: identical bytes. Two skills with the same count are ordered by name.

## 10. JSON is machine-readable

```bash
PYTHONPATH=backend/src uv run python -m cvtailor.cli stats skills --json | jq '.rows[0]'
```

Observe: numbers are numbers, the payload carries `sample`, `filters`, and `small_sample`,
and the same ordering as the text output.

## 11. Read-only

```bash
sha256sum data/corpus.jsonl
```

Run every command above, then hash the file again.

Observe: identical hash. No command writes to the corpus, the profile, or any other file.

## 12. Malformed input is survivable

Append a truncated line to a copy of the corpus and run any report.

Observe: the report still renders, and the sample line reports one ignored line.

## 13. Validation

```bash
PYTHONPATH=backend/src uv run python -m cvtailor.cli stats validate
```

Observe on a clean corpus: the readable count, no findings, exit `0`.

Then introduce each case in a copy of the corpus:

- a line that is not JSON → `error invalid_json`, exit `1`
- a record without a hash → `error missing_hash`, exit `1`
- an unparseable date → `error invalid_date`, exit `1`
- a duplicated hash → `warning duplicate_hash`, exit stays `0`
- a record without a digest → `warning missing_digest`, exit stays `0`

Observe: errors and warnings are visually distinct, the line number is present for
line-level findings, and no finding prints posting text.

Then run step 4 on the same dirty corpus and confirm the report still renders — validation
reports, it does not change how a normal report behaves.

## Checklist

- [ ] An empty corpus says so plainly and exits `0`.
- [ ] A missing corpus exits `3` with the expected path.
- [ ] Shares divide by the filtered sample, not the whole corpus.
- [ ] Alias variants count once and display one spelling.
- [ ] Co-occurrence prints both counts and the conditional probability.
- [ ] The minimum count hides single-occurrence pairs and states its value.
- [ ] A sample under ten warns in both text and JSON.
- [ ] Equal counts order by name, and two runs are byte-identical.
- [ ] JSON carries the raw numbers and the sample metadata.
- [ ] The corpus hash is unchanged after every command.
- [ ] A malformed line is counted as ignored in reports, not fatal.
- [ ] `stats validate` exits `1` on an error and `0` with warnings only.
- [ ] Soft skills appear only with `--include-soft`.
- [ ] Without `--min-count`, a single-occurrence pair is listed last, not hidden.
- [ ] The date filters use the run date, not the posting date.
