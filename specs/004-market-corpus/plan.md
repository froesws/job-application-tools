# Implementation Plan: Market Corpus Reader

**Branch**: `004-market-corpus` | **Date**: 2026-11-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-market-corpus/spec.md`

## Summary

Turn the corpus the pipeline already writes into answers. Four read-only reports over
`data/corpus.jsonl`: top skills with their posting counts and share, co-occurrence for a
given skill with the conditional probability and both counts, the split by seniority
level, and the most frequent companies. Every report prints its sample size and warns
when the sample is too small to mean anything; every report has a JSON form for
scripting. The reader never writes, never calls a model, and never adds a dependency.

## Technical Context

**Language/Version**: Python 3.14.4, same environment as 001.

**Primary Dependencies**: none new. The reader reuses the alias table and the corpus
record shape from 001.

**Storage**: reads `data/corpus.jsonl`, which 001 writes. No writes, no index, no
database, no cache.

**Testing**: pytest against the pure aggregation with fixture corpora; the CLI at its
process boundary for flags, exit codes, and JSON.

**Target Platform**: Local CLI. No HTTP route and no screen in this version: the spec
keeps the reader in the terminal so it can land before the frontend exists.

**Project Type**: The same application as 001; this feature adds a command group.

**Performance Goals**: tens to a few thousand records aggregated in memory in a single
pass; the whole corpus fits comfortably.

**Constraints**: read-only; no posting text exists in the corpus, so nothing personal can
leak; a malformed line is skipped and counted, never fatal.

**Scale/Scope**: One user, one corpus, four reports.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
Evaluated against constitution v2.2.0.

| Gate | How the plan satisfies it | Verdict |
| --- | --- | --- |
| II. Code owns deterministic decisions | Every number is computed in pure code from on-disk records; there is no model in this feature at all | PASS |
| III. Untrusted input, isolated secrets | The corpus holds digests, a posting hash, the date, and the detected language — never the posting text; company names stay local and are only printed to the user's terminal | PASS |
| VI. Fixed pipeline and deliberate scope | No new dependency, no new layer, no new directory; one command group over one pure module | PASS |
| Read-only | The reader opens the corpus for reading only; a test asserts the file is byte-identical after every command | PASS |
| Core stays pure | Aggregation lives in `core` with no storage, web, or service import | PASS |
| No unresolved clarification | Decisions are recorded in [research.md](./research.md) | PASS |

No gate fails.

**Post-design re-check** (after Phase 0 and Phase 1): still PASS. The data model adds no
place where a report depends on anything but the corpus records.

## Project Structure

### Documentation (this feature)

```text
specs/004-market-corpus/
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0 decisions
├── data-model.md        # Phase 1 entities
├── contracts/
│   └── cli.md
└── quickstart.md
```

### Source Code

```text
backend/src/cvtailor/
├── core/
│   └── market.py        # loading, normalization, aggregation, sample notice
└── cli.py               # stats skills | pairs | levels | companies
```

No HTTP route: the spec keeps this version in the terminal. A future screen would consume
the same pure aggregation through a thin route, which is why the aggregation holds no
formatting.

**Structure Decision**: one pure module in `core`, one command group in the CLI. No new
layer and no new dependency. Formatting stays in the CLI so a future route can reuse the
numbers without inheriting terminal text.

### Delivery Order

Each slice ends in a commit and has a "Done when" condition.

**M1 — The corpus loads and reports its sample.**
Scope: record shape, dedup by posting hash, malformed-line skipping, the sample notice,
`stats levels` as the first report.
Done when: a fixture corpus yields the right count per level; a corpus with a duplicate
hash counts the posting once; a malformed line is skipped and counted; an empty corpus
says so plainly.

**M2 — Skill demand.**
Scope: hard-skill extraction, case folding and the alias table, frequency and share,
`--top`, `--include-soft`, and the `--level`, `--company`, `--since`, `--until` filters.
Done when: a fixture yields the expected top skills with counts and shares; `JS` and
`JavaScript` count once; soft skills appear only with the flag; the date filters read
the run date; each filter narrows both the numerator and the denominator.

**M3 — Skill relationships.**
Scope: conditional co-occurrence for a named skill, both directions, and `--min-count`
as an on-demand filter.
Done when: a known pair yields the expected probability with numerator and denominator;
the reverse question differs when the marginals differ; without the flag a
single-occurrence pair is listed last rather than hidden; with the flag it disappears.

**M4 — Companies and output shape.**
Scope: `stats companies` with case-folded grouping, the deterministic ordering rule, and
`--json` for every report.
Done when: equal counts sort by name; `ACME` and `acme` group together while `Acme Corp`
stays separate; every report has a JSON form carrying the sample size and the warning
flag.

**M5 — Corpus validation.**
Scope: `stats validate`, the error and warning rules, and the exit code.
Done when: a clean corpus exits `0` with no findings; a malformed line, a record without
a hash, and an invalid date each exit `1` and name the line; a duplicate hash, a missing
digest, and an empty skill list are warnings that exit `0`.

**M6 — The math is written down.**
Scope: the definitions in the CLI help and in `docs/market-stats.md`.
Done when: a reader can reproduce a number by hand from the documented formula.

## Complexity Tracking

| Item | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| A pure aggregation module separate from the CLI | The same numbers must serve a future route without terminal formatting, and must be tested without spawning processes. | Formatting inside the command would make every number a string assertion; a future route would re-implement the math. |
