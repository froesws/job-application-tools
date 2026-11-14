# Model Admission — v1

**Feature Branch**: `003-model-admission`
**Created**: 2026-11-14
**Status**: ready-for-agent
**Depends on**: `001-cv-tailor-v1-mvp` (pipeline, chains), `002-profile-ingestion` (a real profile)

## Problem Statement

Every model currently runs marked `model_unadmitted`. The mark is honest — nobody
scored the model — but it leaves the user choosing a model by feel: free tiers come
and go, a model can silently degrade after a provider update, and a prompt change can
break a chain that used to work. The constitution says a model joins the default
chain only after passing an evaluation threshold, and today that threshold exists only
on paper.

Without a fixed set of postings with known good answers, there is no way to tell an
improvement from a regression, no way to compare two models, and no way to justify
keeping a weaker free model because it is, in fact, good enough.

## Solution

A small, curated evaluation set: exactly ten real postings, each annotated with the
role title a good selection should pick and the bullets it must include. A harness runs
a candidate model over that set through the real pipeline and reports three numbers:
how many runs produced a valid selection, how often the expected role title was
chosen, and the mean share of must-include bullets captured. A model that clears the
fixed threshold is explicitly admitted; the `model_unadmitted` mark disappears only
then. A prompt change, a change to the set, or a rewrite of the text of an item the set
references invalidates the admission until the model is scored again.

The set is private and git-ignored, with a committed example so the format is
documented. The harness never writes to the market corpus: an evaluation posting is a
test fixture, not market signal.

## User Stories

### The evaluation set

1. As a maintainer, I want to add a real posting to the evaluation set, so that the score reflects the jobs I actually apply to.
2. As a maintainer, I want to record the expected role title for a posting, so that "picked the right headline" is checkable.
3. As a maintainer, I want to record the bullets a good selection must include, so that recall is measurable.
4. As a maintainer, I want the expected bullets to be ids from my own profile, so that the score is tied to the content I would actually send.
5. As a maintainer, I want a posting to be added whenever I notice a model mistake, so that the set grows from real failures instead of guesses.
6. As a maintainer, I want a committed example of the set format, so that the structure is documented without exposing my postings.
7. As a maintainer, I want the evaluation postings kept out of the market corpus, so that testing does not distort market statistics.
8. As a maintainer, I want to see which postings are in the set and when each was added, so that I can spot stale fixtures.

### Scoring a model

9. As a maintainer, I want to run the harness for one model, so that I can judge it before trusting it.
10. As a maintainer, I want the harness to use the real analyze and tailor pipeline, so that the score reflects what the product actually does.
11. As a maintainer, I want each posting scored for selection validity, so that malformed output is counted, not hidden.
12. As a maintainer, I want role-title agreement reported as a count, so that "nine of ten" is visible.
13. As a maintainer, I want must-include recall reported as a mean share, so that partial captures are visible.
14. As a maintainer, I want the fallback excluded from the scored path, so that a model's own output is what gets judged.
15. As a maintainer, I want the harness to be deterministic for the same model and set, so that two runs are comparable.
16. As a maintainer, I want the harness to record the prompt version it used, so that a prompt change is visible in the result.
17. As a maintainer, I want a machine-readable result, so that results can be compared and archived.
18. As a maintainer, I want a failed run to report which posting and which step failed, so that debugging starts from evidence.

### Admission

19. As a maintainer, I want a fixed threshold stated before scoring, so that a model cannot pass by moving the bar.
20. As a maintainer, I want to admit a model explicitly after it passes, so that no run silently promotes itself.
21. As a maintainer, I want the unadmitted mark to stay until an explicit admission, so that a good score alone changes nothing.
22. As a maintainer, I want an admitted model to lose its admission when the prompt, the set, or a referenced item's text changes, so that an old score cannot vouch for new behaviour.
23. As a maintainer, I want to see the admission state and the date of the last passing run in settings, so that I know what I am trusting.
24. As a maintainer, I want to withdraw an admission manually, so that a model that degrades can be demoted without waiting for a new score.
25. As a maintainer, I want a model that misses the threshold to keep its mark, so that the product stays usable without pretending the model is good.
26. As a maintainer, I want admitting a model to leave my configured chains untouched, so that running an evaluation never changes which model the product uses.

### Comparing and keeping trace

27. As a maintainer, I want to compare two stored results side by side, so that a switch is a decision, not a hunch.
28. As a maintainer, I want results archived with date, model, and metrics, so that history survives a provider change.
29. As a maintainer, I want the harness to run without a real key against a scripted model, so that CI can exercise the scorer.
30. As a maintainer, I want the harness to refuse to run without the set or without a profile, so that an empty score is impossible.

### Evaluation screen

31. As a maintainer, I want a screen that lists the ten postings of the set for the selected profile, so that I can see what is being measured.
32. As a maintainer, I want to paste a posting or import one from an existing run, so that a case I just used does not have to be typed again.
33. As a maintainer, I want to pick the expected role and the must-include bullets by clicking, so that annotating ten postings does not mean editing JSON.
34. As a maintainer, I want to replace a posting when the set is full, so that the tenth slot is not a dead end.
35. As a maintainer, I want to run the evaluation from the screen and watch each posting being scored, so that I do not have to switch to a terminal.
36. As a maintainer, I want to admit or withdraw a model from the screen after a confirmation, so that the sensitive decision stays deliberate.
37. As a maintainer, I want the screen to warn that changing an annotation invalidates existing admissions, so that I do not lose evidence by accident.

## Implementation Decisions

- The set lives in the git-ignored data root, one JSON file per posting, holding the
  posting text, the expected role id, the must-include bullet ids, and the date added.
  A committed example directory documents the format with a synthetic posting.
- Expected bullets are profile ids, so the set is scoped to one profile; the harness
  runs against that profile and refuses a set whose ids are absent from it.
- The set holds exactly ten postings. A set with any other size refuses to score, so
  the threshold below always has the same denominator.
- The harness runs the real analyze and tailor steps with the model under test, on
  one posting at a time, with the deterministic fallback disabled. Every posting
  produces one of three outcomes: valid selection, invalid selection, or error.
  Invalid output and provider errors both count as failures, so a flaky model cannot
  pass by shrinking the denominator.
- Determinism: temperature zero where the provider supports it, one run per posting
  by default, and an optional three-run majority per step so a sampling provider can
  still be judged. The mode is recorded in the result.
- Metrics: valid-selection count, expected-role count, and mean must-include recall,
  all computed in code from the scored runs. No judged-by-LLM scoring.
- Threshold, fixed before scoring: valid selection in ten of ten runs, expected role
  in at least nine of ten, mean must-include recall of at least 0.9.
- Admission is an explicit command after a passing result. It records the provider and
  model, the profile, the set version, a hash of the prompt used, a hash over the text
  of the items the set references, the date, and the metrics. It never edits the
  configured chains: the chain stays what the environment says, and admission is only
  evidence about the entries in it.
- The admission is stale, and the settings response says so instead of admitted, when
  the model or provider changes, when the prompt changes, when the set changes, or
  when the text of an item the set references is rewritten. Editing any other part of
  the profile does not invalidate it.
- The harness disables corpus writes, so evaluation postings never enter the market
  corpus.
- Results are archived as JSON under the data root with the model, date, mode,
  metrics, prompt hash, and per-posting detail.
- The corpus and the master are only read; the harness never writes profile data.
- `GET /api/settings` takes an optional profile slug, defaulting to the first profile,
  and reports admission state per chain entry for that profile.
- Majority mode: three runs per posting; at least two must produce a valid selection,
  and their ids are merged by majority. Fewer than two valid runs makes the posting a
  failure, and an error in any run is recorded.
- The evaluation screen is a fourth frontend route. For the selected profile it lists
  the ten postings with their annotations, captures a posting by pasted text or by
  importing a run's stored posting, sets the expected role and the must-include bullets
  by picking from the profile, replaces a posting when the set is full, runs the
  evaluation with per-posting progress, shows the metrics and verdict, and admits or
  withdraws after a confirmation. Changing an annotation warns that existing admissions
  become stale before saving.

## Testing Decisions

A good test asserts observable behavior: the score a given model produces for a given
set. The scorer is pure arithmetic over scored runs, so it is tested directly; the
harness is tested at its process boundary with a scripted model.

- **Scorer**: perfect model, model with an invalid output, model with the wrong role,
  model missing one must-include bullet, and the exact threshold edges.
- **Harness**: run against a scripted model that returns known picks and assert the
  stored result; a posting that fails validation is reported, not skipped.
- **Admission state**: passing then admitting clears the mark; changing the prompt
  hash marks it stale; withdrawing marks it unadmitted.
- **Isolation**: running the harness appends nothing to the corpus and does not
  modify the profile.
- **Frontend**: the screen lists the set for the selected profile, imports a posting
  from a run, saves an annotation and updates the version, warns before an annotation
  change that would invalidate an admission, and requires a confirmation to admit.
- **Prior art**: the same fake-provider pattern, CLI process-boundary tests, and
  Testing Library component tests used in 001 and 002.

## Out of Scope

- Fine-tuning or training a model.
- Automatic discovery or ranking of provider catalogues.
- Per-provider cost accounting.
- Judged-by-LLM scoring or subjective quality ratings.
- Live A/B routing between models inside a normal run.

## Further Notes

- **Constitutional basis.** Principle V requires that a model stay in the default
  chain only while it passes the evaluation threshold, and the Workflow section fixes
  the posting set and the threshold. The set is exactly ten postings, which sits inside
  the constitutional 8-to-10 range and makes the "ten of ten" threshold literal.
  Constitution v2.1.0 lets an unevaluated model run marked `model_unadmitted`; this
  spec is what removes that mark.
- **Admission is not installation.** Admitting records evidence and leaves the
  configured chain untouched, so running an evaluation for comparison never changes
  which model the product uses.
- **Sequencing.** This spec needs a real profile (002) because must-include bullets
  are the candidate's own. It can land any time after that, before or after the
  frontend.
- **Tracker.** No issue tracker is configured; published as a file with
  `ready-for-agent` in the status line.
