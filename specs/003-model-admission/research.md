# Phase 0 Research: Model Admission

Each unknown from the plan's Technical Context is resolved here.

## 1. Set layout

**Decision**: one JSON file per posting under `eval/postings/`, plus a manifest naming
the profile and the set version. A committed example directory documents the format with
a synthetic posting.

**Rationale**: one file per posting keeps diffs readable and lets the user add a posting
by dropping a file. The manifest names the profile, which the per-profile admission
requires.

**Alternatives considered**: a single JSON array (conflicts on every edit); a database
(a store for ten records).

## 2. Set size

**Decision**: exactly ten postings. A set of any other size refuses to score.

**Rationale**: the threshold reads "ten of ten" and "nine of ten"; with another size the
numbers lose their denominator. Ten sits inside the constitutional 8-to-10 range.

**Alternatives considered**: proportions with rounding (works at any size, but needs an
amendment to the threshold wording); eight postings (cannot reach nine of ten).

## 3. What the set version covers

**Decision**: a hash over the sorted tuple of each posting's normalized text hash, its
expected role id, and its must-include bullet ids, plus the profile slug.

**Rationale**: any change that alters the test changes the version, and nothing else
does. Editing a posting's wording invalidates; re-saving the same content does not.

**Alternatives considered**: a manual version integer (can be forgotten, which is the
failure we are guarding against); hashing the whole directory (file ordering noise).

## 4. Referenced-text hash

**Decision**: a hash over the text of the role and bullets named by the set, in both
languages.

**Rationale**: the spec invalidates when the text of a referenced item is rewritten, and
not when an unrelated item changes. Hashing exactly the referenced items gives that
precision.

**Alternatives considered**: hashing the whole master (any edit invalidates);
hashing nothing (a reworded bullet silently changes the test).

## 5. Prompt hash

**Decision**: a hash over the analyze and tailor prompt templates and the output schema
they constrain the model to.

**Rationale**: those are the instructions and the contract that shape the model's
answer; a change to either changes what was measured. The LLM transport and retry
policy are excluded, because they do not change the task.

**Alternatives considered**: hashing the whole `agents` package (noise from docstrings);
no prompt hash (a prompt change silently keeps an old score).

## 6. Running the harness

**Decision**: for each posting, run the real analyze and tailor steps with the model
under test, the deterministic fallback disabled, and corpus writes disabled. Each
posting produces valid, invalid, or error.

**Rationale**: the score must reflect the product's real path. Disabling the fallback is
what makes the model's own output the subject; disabling the corpus keeps evaluation
postings out of market statistics.

**Alternatives considered**: scoring with the fallback enabled (a failing model would
look valid); running the scorer against a separate mini-pipeline (measures a different
product).

## 7. Determinism

**Decision**: temperature zero where the provider supports it, one run per posting by
default, and an optional three-run majority per step recorded in the result.

**Rationale**: a provider that samples cannot be compared run to run. The option keeps a
sampling-only provider judgeable without changing the default.

**Alternatives considered**: always three runs (triples cost); always one run (a
sampling provider's single run is noise).

## 8. Errors count as failures

**Decision**: a timeout, a rate limit, or unparseable output is a failure for the metric,
not an exclusion.

**Rationale**: the threshold claims ten valid selections out of ten postings. Excluding
failures would let a flaky model pass by shrinking the denominator.

**Alternatives considered**: retry once then exclude (measures quality, not
availability); abort the run (one transient error would waste the whole evaluation).

## 9. Admission record

**Decision**: `eval/admitted.json` holds records keyed by provider, model, and profile,
each with the set version, prompt hash, referenced-text hash, date, and metrics.

**Rationale**: everything the staleness check needs is stored beside the score, so the
check is a comparison of hashes, not a guess.

**Alternatives considered**: storing admission in `.env` (mixes evidence with
configuration); one file per model (more files, no gain).

## 10. Admission does not edit configuration

**Decision**: admitting writes only the record. The chains stay in `.env`, and settings
show each chain entry with its admission state.

**Rationale**: running a comparison should never change what the product uses. Principle
V is satisfied by the mark and the evidence, not by the command rewriting config.

**Alternatives considered**: admitting prepends the model to the chain (a test mutates
the product); printing a suggested line (an extra manual step that is easy to skip).

## 11. Results archive

**Decision**: `eval/results/<UTC timestamp>-<provider>-<model>.json`, holding the set
version, prompt hash, mode, metrics, and per-posting detail.

**Rationale**: comparisons need history, and a provider change must not erase what the
old model scored. One file per run is trivial to diff.

**Alternatives considered**: a single results file (unbounded growth and merge noise);
no archive (comparison becomes impossible).

## 12. CI path

**Decision**: the harness runs end to end against the fake provider in tests; no test
needs a key.

**Rationale**: the scorer and the runner are the risky parts, and both are deterministic
with a scripted model. A key in CI would be a security problem for no extra coverage.

**Alternatives considered**: a live smoke in CI (leaks a secret into CI and makes the
build depend on a provider); unit-testing only the scorer (leaves the runner untested).
