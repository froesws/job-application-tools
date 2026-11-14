# Market Corpus Reader — v1

**Feature Branch**: `004-market-corpus`
**Created**: 2026-11-14
**Status**: ready-for-agent
**Depends on**: `001-cv-tailor-v1-mvp` (the corpus is already being written)

## Problem Statement

Every analyzed posting now appends a record to the market corpus: the digest, a hash
of the posting, the date, and the detected language. That data is being collected on
purpose — the user wants to know which skills the market asks for and which skills
travel together, so that a CV can lead with what matters and a gap can be closed
before it costs an application.

Today the corpus is a file nobody can read. Answering "how often does a C#/.NET
posting also ask for RabbitMQ?" means opening a JSONL file and counting by hand,
which nobody does. Meanwhile the sample is small — with three postings any percentage
is noise — so the reader has to be honest about how much it knows.

## Solution

Read-only commands over the existing corpus. `stats skills` shows which skills appear
most often and in how many postings. `stats pairs SKILL` shows, for a skill, which
other skills co-occur and with what conditional probability, given how many postings
support the number. `stats levels` and `stats companies` show how the sample splits.
Every command states its sample size, warns when the sample is too small to mean
anything, and offers JSON for scripting.

The corpus stays append-only and untouched. The reader is a pure aggregation over the
records, so it is cheap to extend and impossible to corrupt the data with.

## User Stories

### Skill demand

1. As a job seeker, I want to see the skills that appear in the most postings, so that I know what the market asks for.
2. As a job seeker, I want each skill shown with its posting count and share, so that I can tell a habit from a trend.
3. As a job seeker, I want to limit the list to a number of skills, so that the output stays readable.
4. As a job seeker, I want to filter by seniority level, so that "junior" and "senior" do not blur together.
5. As a job seeker, I want to filter by date range, so that I can look at the last few months only.
6. As a job seeker, I want the same skill written in different cases or with a known alias counted once, so that `JS` and `JavaScript` do not split the count.

### Relationships between skills

7. As a job seeker, I want to ask which skills co-occur with a given skill, so that I can see what usually comes as a package.
8. As a job seeker, I want the conditional probability shown with its numerator and denominator, so that I can judge the number instead of trusting a percentage.
9. As a job seeker, I want the co-occurrence results sorted by strength, so that the strongest pairing is first.
10. As a job seeker, I want to require a minimum co-occurrence count, so that a pair seen once does not outrank a real pattern.
11. As a job seeker, I want the reverse question too, so that I can check what a skill implies and what implies it.

### Sample honesty

12. As a job seeker, I want the sample size printed on every command, so that I never read a percentage without its denominator.
13. As a job seeker, I want an explicit warning when the sample is too small, so that I do not build a plan on three postings.
14. As a job seeker, I want the warning to name the threshold, so that I know when the numbers become usable.
15. As a job seeker, I want an empty corpus to say so plainly, so that an empty report is not mistaken for zero demand.

### Splits

16. As a job seeker, I want the distribution by seniority level, so that I can see where the market volume is.
17. As a job seeker, I want the companies that appear most often, so that I can spot repeated hiring.
18. As a job seeker, I want a company filter on the skill report, so that I can answer "what does this employer ask for".
19. As a job seeker, I want duplicated postings counted once, so that re-analyzing the same text does not inflate anything.
20. As a job seeker, I want to know how many postings the reader ignored and why, so that the counts are explainable.

### Use and trust

21. As a CLI user, I want machine-readable output, so that I can pipe the numbers elsewhere.
22. As a CLI user, I want a stable ordering for equal counts, so that two runs produce the same output.
23. As a job seeker, I want the commands to be read-only, so that looking at statistics can never change the data.
24. As a job seeker, I want the math documented, so that I can reproduce a number by hand.
25. As a job seeker, I want the reader to work on a corpus written by an older version, so that the file format can grow without losing history.

## Implementation Decisions

- One pure aggregation module over a list of corpus records, plus one validation pass
  over the same list. No new store, no database, no cache. The corpus file remains the
  single source.
- Commands: `stats skills`, `stats pairs SKILL`, `stats levels`, `stats companies`.
  All accept `--json`; the skill and company reports accept `--top N`; the skill
  report accepts `--level`, `--company`, `--since`, `--until`, and `--include-soft`;
  the pair report accepts `--min-count`, which filters on demand. Without it, every
  pair is listed, ordered by count, so a single occurrence is ranked last rather than
  hidden.
- Metrics: a skill's count is the number of distinct postings containing it; share is
  that count divided by the number of postings in the filtered sample. Co-occurrence
  is `P(B | A) = postings with both / postings with A`, always printed with both
  counts.
- Normalization: skills compare case-folded and trimmed, and reuse the alias table
  from the pipeline so `js` and `javascript` are one skill. Display uses the most
  frequent spelling.
- Hard and soft skills are separate signals. `stats skills` reads `hard_skills` only;
  `--include-soft` adds the soft entries as their own rows, because mixing them lets
  generic words outrank the technologies a CV is actually built from.
- Company names group by case-folded, trimmed text and display the most frequent
  spelling. Common suffixes are not stripped: a heuristic that merged "Acme Corp" with
  "Acme Ltda" would produce a wrong number silently.
- The date filters read the record's own `date`, which is always present and means
  "when this posting passed through the tool". The digest's posting date is not used:
  it falls back to the run date when the posting states none, so filtering on it would
  mix two meanings behind one number.
- Deduplication: records are deduplicated by their posting hash, so a future format
  change or a manual re-append cannot double count.
- Ordering: count descending, then name ascending, so equal counts are stable.
- Sample honesty: every report prints the number of postings considered and warns
  when it is below a documented threshold. The warning is part of the text and of the
  JSON payload, not a stderr aside.
- Read-only: the reader opens the corpus for reading only and never rewrites it.
- A validation mode reads the corpus without aggregating and reports what it finds in
  two levels. Errors are an unreadable file, a line that is not JSON, a record without a
  hash, and an invalid date; any error exits non-zero. Warnings are a duplicate hash, a
  record without a digest, an empty skill list, and an ambiguous company name; warnings
  are listed and exit zero. Normal reports keep tolerating both, so validating never
  changes what a report shows.
- Forward compatibility: records missing a field are counted for the fields they do
  have; unknown fields are ignored; a malformed line is skipped and counted in the
  ignored total.
- Company and level reports are counts, not probabilities; they exist to explain the
  sample, not to rank employers.

## Testing Decisions

A good test asserts the number a given corpus produces. The aggregation is pure, so
it is tested directly with fixture corpora rather than through the CLI.

- **Aggregation**: empty corpus, one posting, a small sample below the warning
  threshold, and a larger fixture with known counts.
- **Co-occurrence**: conditional probability and both counts for a known pair, the
  reverse direction, and the minimum-count filter.
- **Normalization**: case variants and an alias collapsing into one skill; the
  displayed spelling is the most frequent.
- **Filters**: level, company, and date range each narrow the sample and the
  denominators consistently.
- **Robustness**: a malformed line is skipped and counted; an unknown field is
  ignored; a record from an older shape is still counted.
- **Read-only**: running a command leaves the corpus byte-identical.
- **Prior art**: the pure-function tests established by the renderer and the market
  scorer in 003; the CLI process boundary used by 001.

## Out of Scope

- Charts, dashboards, or any UI. This is terminal output in version 1.
- Recommendations such as "learn RabbitMQ next".
- Machine learning, clustering, or association rules beyond pairwise co-occurrence.
- Scraping postings to grow the corpus automatically.
- Writing back to the corpus, editing records, or deleting them.
- Cross-profile statistics; the corpus is market data and stays profile-independent.
- Cost, salary, or location analysis, which the digest does not carry.

## Further Notes

- **Why this is small.** The data already exists and is already deduplicated on write.
  This spec adds a reader, not a pipeline: one pure module, four commands, and a
  warning threshold.
- **Threshold.** The warning starts below ten postings. Ten is enough to see a
  repeated pattern and small enough to reach in a few weeks of real use.
- **Sequencing.** Can land any time after 001 closes. It needs nothing from 002 or
  003, which makes it a good candidate for a short wave between larger ones.
- **Tracker.** No issue tracker is configured; published as a file with
  `ready-for-agent` in the status line.
