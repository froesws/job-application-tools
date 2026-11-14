# Quickstart Validation: Model Admission

Run after `001-cv-tailor-v1-mvp` and `002-profile-ingestion` are delivered and a real
profile exists. Each step states what to observe.

## Prerequisites

- A profile with at least one role option and enough bullets to annotate.
- Ten real postings you would actually apply to, as text.
- A configured chain, or `LLM_PROVIDER=fake` for the offline path.

## 1. Build the set

Preferred: open the evaluation screen with a profile selected and add ten postings,
pasting each text or importing it from a run you already did.

Equivalent by hand: one JSON file per posting under the data root's `eval/postings/`,
following the committed example, plus a manifest naming the profile and the ten posting
ids.

Observe: each posting holds the text, the expected role id, and the must-include bullet
ids. Nothing is committed; the directory is git-ignored.

## 2. Load and validate

```bash
PYTHONPATH=backend/src uv run python -m cvtailor.cli eval status
```

Observe: the set loads, its version is computed, and a malformed set is refused with a
reason. Try these refusals:

- remove one posting from the manifest → refused for size
- point `expected_role_id` at a missing role → refused for an unknown id
- change a stored version by hand → refused for a version mismatch

## 3. Score an offline model

```bash
LLM_PROVIDER=fake PYTHONPATH=backend/src uv run python -m cvtailor.cli eval run \
  --model fake:scripted --json
```

Observe: one object with the three metrics, the verdict, and an archive path. With the
scripted model answering correctly, `valid` is 10, `role_ok` is 10, and recall is 1.0.

## 4. Score a failing model

Point the scripted model at picks that miss one must-include bullet on three postings.

Observe: `role_ok` stays high, recall drops, the verdict fails on recall, the archive is
still written, and the exit code is `1`.

Then make the model time out on two postings.

Observe: those postings count as `error`, `valid` drops to 8, and the run fails. They are
not excluded from the denominator.

## 5. The evaluation leaves no trace elsewhere

```bash
wc -l data/corpus.jsonl
```

Run step 3 again.

Observe: the corpus line count is unchanged, and the profile's master is byte-identical.
Evaluation postings never enter market statistics.

## 6. Admit

```bash
PYTHONPATH=backend/src uv run python -m cvtailor.cli eval admit --model fake:scripted --json
```

Observe: a record is written with the provider, model, profile, set version, prompt hash,
referenced-text hash, date, and metrics. `eval status` reports `admitted`.

Then check `.env`: it is byte-identical. Admitting never edits configuration, and
`GET /api/settings` now reports the chain entry as admitted.

## 7. Invalidate precisely

- **Prompt**: change a word in the tailor prompt template. `eval status` reports `stale`
  with `prompt_changed`.
- **Set**: add a posting and update the manifest. The set version changes and the state
  becomes `stale` with `set_changed`.
- **Referenced text**: reword a bullet that the set names. State becomes `stale` with
  `referenced_text_changed`.
- **Unrelated edit**: add a project the set does not reference. The state stays
  `admitted`.

Restore the prompt and the wording, then re-run step 3 and admit again.

## 8. Withdraw

```bash
PYTHONPATH=backend/src uv run python -m cvtailor.cli eval withdraw --model fake:scripted
```

Observe: the state becomes `unadmitted`, and the model still runs in a normal tailoring
with the `model_unadmitted` mark in the report.

## 9. Compare

```bash
PYTHONPATH=backend/src uv run python -m cvtailor.cli eval compare \
  eval/results/<failing>.json eval/results/<passing>.json
```

Observe: both archives side by side with their metrics and the postings that differed.

## 10. The refusal paths

- `eval admit` on a failing archive → refused, exit `1`, nothing written.
- `eval admit --from` an archive whose prompt hash is old → refused as stale.
- `eval run` against an unreachable provider → exit `5`, no archive claiming success.

## 11. Majority mode

```bash
PYTHONPATH=backend/src uv run python -m cvtailor.cli eval run \
  --model fake:scripted --majority --json
```

Observe: three runs per posting. When at least two produce a valid selection, their ids
merge by majority and the posting is scored on the merged pick. A posting with fewer than
two valid runs fails, and an error in any of the three is recorded. The archive says
`mode: majority`.

## 12. The screen end to end

With the frontend running and a profile selected:

- list the set → ten postings with their annotations and the set version
- add by importing a run → the form fills with exactly the text that run analyzed
- annotate role and bullets → the version changes and the invalidation warning names the
  models that would go stale before saving
- replace a posting while the set is full → the other nine remain
- run the evaluation → progress per posting, then metrics and verdict
- admit → a confirmation is required; the state becomes admitted
- open a model whose prompt changed → `stale`, with the reason visible
- withdraw → a confirmation is required; the state becomes unadmitted

Observe: the whole loop finishes without a terminal, and `.env` is byte-identical at the
end.

## Checklist

- [ ] A set of any size other than ten refuses to score.
- [ ] An unknown role or bullet id refuses the set.
- [ ] Errors count as failures and are not excluded.
- [ ] The corpus and the master are untouched by an evaluation.
- [ ] Admitting writes a record and leaves `.env` byte-identical.
- [ ] A prompt change, a set change, and a referenced-text change each mark the admission stale.
- [ ] An unrelated profile edit does not mark it stale.
- [ ] Withdrawing keeps the model usable, marked unadmitted.
- [ ] Two archives compare with their metrics.
- [ ] The screen lists, captures, annotates, runs, admits, and withdraws without a terminal.
- [ ] Importing a posting from a run yields exactly the analyzed text.
- [ ] Majority mode merges at least two valid runs and fails below that.
