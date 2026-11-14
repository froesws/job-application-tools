---
description: "Task list for 004-market-corpus"
---

# Tasks: Market Corpus Reader

**Input**: Design documents from `/specs/004-market-corpus/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md, `.specify/memory/constitution.md` (v2.2.0)

**Prerequisite feature**: `001-cv-tailor-v1-mvp` writes `data/corpus.jsonl` and supplies
the CLI entry point and the alias table. No task here re-implements them.

**Tests**: Required. The spec's Testing Decisions and constitution v2.2.0 make tests
mandatory, including failure paths.

**Organization**: Phases follow the plan's slices (M1–M6), each with a "Done when"
condition and demonstrable on its own. The spec's 25 stories are grouped into five
story labels; each task carries the label of the group it serves.

| Story | Spec stories | Coverage |
| --- | --- | --- |
| US1 | Skill demand (1–6) | normalization, counts, share, filters, soft skills |
| US2 | Relationships (7–11) | conditional co-occurrence, directions, minimum count |
| US3 | Sample honesty (12–15) | sample line, warning, empty corpus |
| US4 | Splits (16–20) | levels, companies, deduplication, ignored count |
| US5 | Use and trust (21–25) | JSON, ordering, read-only, validation, documented math |

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: which story group the task serves
- Every task names an exact file path

## Path Conventions

- Backend: `backend/src/cvtailor/`, tests in `backend/tests/`
- Corpus: `data/corpus.jsonl` (git-ignored, written by 001)
- Fixtures: `backend/tests/fixtures/corpus/`

---

## Phase 1: Setup

**Purpose**: The fixture corpora every slice reuses.

- [ ] T001 [P] Create a twelve-record fixture with known answers — four mention Python, three Kubernetes, three both, two of the four Python records also mention RabbitMQ — in `backend/tests/fixtures/corpus/clean.jsonl`
- [ ] T002 [P] Create the edge fixtures — empty, one record, six records, a duplicated hash, a truncated line, a missing digest, an invalid date, and an older record shape — in `backend/tests/fixtures/corpus/`

**Checkpoint**: `make check` still green with the fixtures in place.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Loading, deduplication, and the sample notice that every report prints.

**⚠️ CRITICAL**: no slice starts until this phase completes.

- [ ] T003 [US3] Implement line-by-line corpus loading in `backend/src/cvtailor/core/market.py`: a malformed line is skipped and counted, a record missing a field counts for the fields it has, and unknown fields are ignored
- [ ] T004 [US4] Implement deduplication by posting hash, keeping the first occurrence, in `backend/src/cvtailor/core/market.py`
- [ ] T005 [US3] Implement the `MarketSample` with `total`, `ignored`, and `small_sample` (true below ten postings) in `backend/src/cvtailor/core/market.py`
- [ ] T006 [P] [US3] Add unit tests for loading, malformed-line handling, deduplication, and the sample notice in `backend/tests/unit/test_market_load.py`
- [ ] T007 [P] [US4] Add a test with the older record shape and an unknown field, asserting both are counted correctly, in `backend/tests/unit/test_market_compat.py`

**Checkpoint**: the sample is correct for every fixture, with no report implemented yet.

---

## Phase 3: Slice M1 — Levels (US4, US3)

**Goal**: the first report, proving the loader composes into output.

**Independent Test**: quickstart step 3 passes on the clean fixture.

- [ ] T008 [US4] Implement level aggregation with count and share in `backend/src/cvtailor/core/market.py`
- [ ] T009 [US5] Implement `stats levels` in `backend/src/cvtailor/cli.py`, printing the sample line first, then rows
- [ ] T010 [US3] Print the small-sample warning and the empty-corpus message in `backend/src/cvtailor/cli.py`
- [ ] T011 [P] [US4] Add a test asserting the level counts and shares for the clean fixture in `backend/tests/unit/test_market_levels.py`
- [ ] T012 [P] [US3] Add process-boundary tests for the empty corpus (`0`) and the missing corpus (`3`) in `backend/tests/integration/test_stats_errors.py`

**Checkpoint**: quickstart step 2 and 3 pass; commit.

---

## Phase 4: Slice M2 — Skill demand (US1, US3)

**Goal**: the main report, with normalization and filters.

**Independent Test**: quickstart steps 4 and 5 pass.

- [ ] T013 [US1] Implement hard-skill extraction with case folding, trimming, and the pipeline's alias table in `backend/src/cvtailor/core/market.py`
- [ ] T014 [US1] Implement frequency and share over the filtered sample, counting distinct postings in `backend/src/cvtailor/core/market.py`
- [ ] T015 [US1] Implement the filters — level, company, and the run-date range — in `backend/src/cvtailor/core/market.py`
- [ ] T016 [US1] Implement `stats skills` with `--top`, `--include-soft`, `--level`, `--company`, `--since`, and `--until` in `backend/src/cvtailor/cli.py`
- [ ] T017 [P] [US1] Add tests for alias collapsing, the displayed spelling, and case variants in `backend/tests/unit/test_market_skills.py`
- [ ] T018 [P] [US1] Add tests proving each filter narrows both the numerator and the denominator, and that the date filter reads the run date, in `backend/tests/unit/test_market_filters.py`
- [ ] T019 [P] [US1] Add a test proving soft skills appear only with `--include-soft` in `backend/tests/integration/test_stats_skills_cli.py`

**Checkpoint**: quickstart 4–5 pass; commit.

---

## Phase 5: Slice M3 — Skill relationships (US2)

**Goal**: co-occurrence with its denominator.

**Independent Test**: quickstart steps 6 and 7 pass.

- [ ] T020 [US2] Implement conditional co-occurrence for a named skill, carrying `both` and `given_count`, in `backend/src/cvtailor/core/market.py`
- [ ] T021 [US2] Implement the reverse direction, so a pair whose marginals differ yields different probabilities, in `backend/src/cvtailor/core/market.py`
- [ ] T022 [US2] Implement `stats pairs` with `--min-count` as an on-demand filter and the empty-report line for an absent skill in `backend/src/cvtailor/cli.py`
- [ ] T023 [P] [US2] Add tests for the known pair (`2/4`, 50%), the reverse question, and the absent-skill case in `backend/tests/unit/test_market_pairs.py`
- [ ] T024 [P] [US2] Add a test asserting that without `--min-count` a single-occurrence pair is listed last and not hidden, in `backend/tests/integration/test_stats_pairs_cli.py`

**Checkpoint**: quickstart 6–7 pass; commit.

---

## Phase 6: Slice M4 — Companies, ordering, and JSON (US4, US5)

**Goal**: the last report, plus the output guarantees that apply to all of them.

**Independent Test**: quickstart steps 9 and 10 pass.

- [ ] T025 [US4] Implement company aggregation with case-folded, trimmed grouping and the most frequent spelling, in `backend/src/cvtailor/core/market.py`
- [ ] T026 [US5] Implement the deterministic ordering — count descending, then name ascending — in `backend/src/cvtailor/core/market.py`
- [ ] T027 [US5] Implement `--json` for every report, carrying the raw numbers, the sample, and the filters, in `backend/src/cvtailor/cli.py`
- [ ] T028 [P] [US4] Add a test asserting `ACME` and `acme` group together while `Acme Corp` stays separate, in `backend/tests/unit/test_market_companies.py`
- [ ] T029 [P] [US5] Add a test proving two runs on the same corpus produce identical bytes and that JSON order matches text order, in `backend/tests/integration/test_stats_ordering.py`

**Checkpoint**: quickstart 9–10 pass; commit.

---

## Phase 7: Slice M5 — Corpus validation (US5)

**Goal**: a report on the data itself, with a usable exit code.

**Independent Test**: quickstart step 13 passes.

- [ ] T030 [US5] Implement the validation pass with the documented error codes — `unreadable_file`, `invalid_json`, `missing_hash`, `invalid_date` — and warning codes — `duplicate_hash`, `missing_digest`, `empty_skills`, `ambiguous_company` — in `backend/src/cvtailor/core/market.py`
- [ ] T031 [US5] Implement `stats validate` with line numbers, a readable count, and exit `1` only when an error exists, in `backend/src/cvtailor/cli.py`
- [ ] T032 [P] [US5] Add fixture-driven tests for each error and warning code in `backend/tests/unit/test_market_validate.py`
- [ ] T033 [P] [US5] Add a process-boundary test proving exit `1` on an error, exit `0` with warnings only, and that a normal report still renders on the same dirty corpus, in `backend/tests/integration/test_stats_validate_cli.py`

**Checkpoint**: quickstart 13 passes; commit.

---

## Phase 8: Slice M6 — The math is written down (US5)

**Goal**: a reader can reproduce each number by hand.

**Independent Test**: a number from the clean fixture is recomputed from the document.

- [ ] T034 [US5] Write the formulas — count, share, conditional probability, deduplication, the sample threshold, and the ordering rule — in `docs/market-stats.md`
- [ ] T035 [US5] Put the same definitions in each command's help text in `backend/src/cvtailor/cli.py`
- [ ] T036 [P] [US5] Add a test asserting the help text of each command mentions its formula or its denominator rule, in `backend/tests/integration/test_stats_help.py`

**Checkpoint**: the documentation and the help agree; commit.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [ ] T037 [P] Add the read-only test: every command leaves the corpus byte-identical, in `backend/tests/integration/test_stats_readonly.py`
- [ ] T038 [P] Add a JSON schema test asserting every report carries `sample`, `filters`, and `rows`, in `backend/tests/integration/test_stats_json.py`
- [ ] T039 Run the full `quickstart.md` checklist and record the result

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Setup; blocks every report.
- **M1 (Phase 3)**: depends on Foundational.
- **M2 (Phase 4)**: depends on M1 — it reuses the sample line and the report shape.
- **M3 (Phase 5)**: depends on M2 — pairs reuse the normalized skill set.
- **M4 (Phase 6)**: depends on M2 for the JSON shape; independent of M3.
- **M5 (Phase 7)**: depends on Foundational only; it does not aggregate.
- **M6 (Phase 8)**: depends on M2–M5 being defined.
- **Polish (Phase 9)**: depends on the closed slices.

### Story Dependencies

- US3 (sample honesty) comes first because every report prints it.
- US4 (splits) supplies deduplication and levels, which M1 needs.
- US1 (skill demand) is the main report and blocks US2.
- US2 (relationships) needs the normalized skills from US1.
- US5 (trust) spans the whole feature: ordering, JSON, validation, and documentation.

### Within Each Slice

- Tests marked [P] can be written in parallel with each other.
- Pure aggregation before the command that prints it.
- Each slice closes with its "Done when" from `plan.md` and a commit.

### Parallel Opportunities

- Setup: T001 and T002.
- Foundational: T006 and T007.
- M1: T011 and T012.
- M2: T017, T018, T019.
- M3: T023 and T024.
- M4: T028 and T029.
- M5: T032 and T033.
- Polish: T037 and T038.

---

## Parallel Example: Slice M2

```bash
# Each test file is independent once the aggregation exists:
Task: "Add alias and spelling tests in backend/tests/unit/test_market_skills.py"
Task: "Add filter tests in backend/tests/unit/test_market_filters.py"
Task: "Add CLI soft-skill test in backend/tests/integration/test_stats_skills_cli.py"
```

---

## Implementation Strategy

### MVP First

The first useful increment is **M1**: `stats levels` on a real corpus, with the sample
line and the empty-corpus behaviour. It proves the loader end to end and is the smallest
thing that answers a question.

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (M1), run quickstart 2–3, commit.
3. Continue slice by slice; each closes with its "Done when" and a commit.

### Incremental Delivery

M1 → M2 → M3 → M4 → M5 → M6. The reader can land any time after 001 closes; nothing
here depends on 002 or 003.

### Commit Discipline

Constitution v2.2.0 requires one commit per completed task. A task is not done until it
is committed.

---

## Notes

- [P] marks different files with no dependency on an incomplete task.
- [USx] maps the task to a story group in the table above.
- Tests are required by the spec; write them first inside each slice.
- Every report prints its sample size; no percentage is shown without its denominator.
- The reader never writes: the corpus stays append-only.
