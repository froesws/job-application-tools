# Implementation Plan: Model Admission

**Branch**: `003-model-admission` | **Date**: 2026-11-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-model-admission/spec.md`

## Summary

Give "this model is good" a measurable meaning. Ten real postings, annotated with the
role and the bullets a good selection must include, are run through the real pipeline
against one model. Code computes three numbers — valid selections, role agreement,
must-include recall — and an explicit act records an admission when the fixed threshold
is met. The record names the provider, model, profile, set version, prompt hash, and the
text of the referenced items, so any change that would invalidate the score is
detectable. Admitting writes evidence, never configuration: the chains stay where the
operator put them.

The whole loop is reachable without a terminal: a fourth frontend route captures a
posting, annotates it, runs the evaluation, and admits the model after a confirmation.

## Technical Context

**Language/Version**: Python 3.14.4, same environment as 001.

**Primary Dependencies**: none new. The harness reuses the pipeline, the `LLMClient`
layer, the fake provider, and the CLI adapter. The screen reuses the frontend shell,
the generated client, and TanStack Query from 001.

**Storage**: under the git-ignored data root — `eval/postings/` with one JSON file per
posting and a manifest naming the profile, `eval/results/` with one archive per run, and
`eval/admitted.json` with the admission records. A committed example directory
documents the format.

**Testing**: pytest against the pure scorer and the dataset loader; the harness is
exercised with a scripted model at the CLI process boundary.

**Target Platform**: Local backend, CLI, and browser. No new service and no scheduled
job; evaluation runs execute on a background thread inside the process, like ingestion.

**Project Type**: The same web application and CLI as 001; this feature adds a command
group, an HTTP surface for the screen, and one frontend route.

**Performance Goals**: ten postings, one run each by default; the run budget is the
existing per-run budget, so an evaluation is a sequence of normal runs.

**Constraints**: exactly ten postings; the evaluated path disables the deterministic
fallback and the corpus write; errors count as failures; admitting never edits `.env`.

**Scale/Scope**: One user, one profile per set, a handful of candidate models.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
Evaluated against constitution v2.2.0.

| Gate | How the plan satisfies it | Verdict |
| --- | --- | --- |
| I. Master profile is the single source of facts | The set references role and bullet ids from one profile; the harness refuses a set whose ids are absent | PASS |
| II. Code owns validation and deterministic decisions | Every metric is computed in code from scored runs; no judged-by-LLM scoring | PASS |
| III. Untrusted input, isolated secrets | Postings are untrusted text and are delimited by the existing prompt builder; the set and results are git-ignored; CI uses the fake provider, never a key | PASS |
| IV. Human review before artifacts leave | Evaluation results are archived and inspectable; admission is an explicit operator command | PASS |
| V. Provider-agnostic LLM layer with graceful degradation | The harness uses the existing `LLMClient` and chains, and turns the fallback off so the model is judged on its own output; an unadmitted model still runs, marked | PASS |
| VI. Fixed pipeline and deliberate scope | The harness composes the existing fixed steps; no agent framework; no new dependency | PASS |
| The threshold is literal | The set is exactly ten postings, so "ten of ten" and "nine of ten" always have a denominator | PASS |
| Core stays pure | Dataset validation, hashing, and metrics live in `core`; no network, no storage, no service import | PASS |
| Frontend stack matches the constitution | The screen uses the existing React, TypeScript, Material UI, TanStack Query, and generated-client setup; no new library | PASS |
| No unresolved clarification | Decisions are recorded in [research.md](./research.md) | PASS |

No gate fails.

**Post-design re-check** (after Phase 0 and Phase 1): still PASS. The data model adds no
place where a model's output is trusted without a metric, and the CLI contract keeps
admission separate from configuration.

## Project Structure

### Documentation (this feature)

```text
specs/003-model-admission/
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0 decisions
├── data-model.md        # Phase 1 entities
├── contracts/
│   ├── api.md           # eval routes for the screen
│   └── cli.md
└── quickstart.md
```

### Source Code

```text
backend/src/cvtailor/
├── core/
│   └── evals.py         # dataset validation, hashing, metrics, staleness
├── storage/
│   └── evals.py         # postings, results, admissions on disk
├── service.py           # evaluation runner over the existing pipeline
├── api/
│   ├── routes.py        # eval routes; settings learns the profile parameter
│   └── schemas.py       # eval request and response models
└── cli.py               # eval run | status | admit | withdraw | compare

frontend/src/
├── pages/
│   └── EvaluationPage.tsx
└── viewmodels/
    └── useEvaluation.ts
```

**Structure Decision**: the scoring is pure and joins `core`; the persistence joins
`storage`; the orchestration joins the application service; the routes join `api`; the
command group joins the CLI; the screen joins the frontend that 001 already establishes.
The feature adds no layer and no dependency.

The one change to an existing route is `GET /api/settings?profile=`, which now reads the
admission records and reports state per chain entry for that profile.

### Delivery Order

Each slice ends in a commit and has a "Done when" condition.

**E1 — The set, loaded and validated.**
Scope: dataset format, loader, validation (exactly ten, ids present in the profile),
set version hash.
Done when: a valid set loads and reports its version; a set with nine postings, a
missing id, or an unknown profile is refused with a clear reason.

**E2 — Scoring, computed and tested.**
Scope: metrics over scored runs, threshold evaluation, referenced-text hash.
Done when: a fixture of known picks yields the expected valid count, role count, and
recall; a model that errs on three postings fails the threshold.

**E3 — The harness.**
Scope: runner over the pipeline with fallback and corpus disabled, error outcomes
counted, results archived.
Done when: a scripted model produces an archive with per-posting detail; a provider
error is recorded as a failure; the corpus file is unchanged; the master is unchanged.

**E4 — Admission.**
Scope: admission record, staleness detection, `eval status`, `eval admit`,
`eval withdraw`, settings reflection.
Done when: admitting after a pass clears the mark; changing the prompt, the set, or a
referenced item's text marks it stale; withdrawing marks it unadmitted; `.env` is
untouched by every command.

**E5 — The comparison view and the offline path.**
Scope: comparing two archived results, and running the whole harness against the fake
provider for CI.
Done when: two archives render side by side with their metrics; the harness completes
with the fake and no key.

**E6 — HTTP surface for the screen.**
Scope: read the set, add, annotate, and remove a posting, run asynchronously with
polling, admit and withdraw, and the settings profile parameter.
Done when: every route in the API contract passes a contract test with the fake model;
the settings response reports state and reason per chain entry for the requested
profile; no route or response carries a key or a posting text beyond the set itself.

**E7 — The evaluation screen.**
Scope: the fourth route, the list, capture by paste or run import, annotation, the
invalidation warning, replacement, the run with per-posting progress, metrics, and
admit/withdraw with confirmation.
Done when: `npm run typecheck`, Vitest, and the build pass and join `make check`; the
screen drives a full evaluation against the fake model without a terminal; admitting
requires a confirmation; a stale state is visible with its reason.

E7 depends on 001's frontend shell. In delivery order it comes after that shell, which
makes 003's last slice the last thing built.

## Complexity Tracking

| Item | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| A new command group and a stored admission record | The threshold has to be checked against something and remembered between sessions. | Re-running the evaluation every session would make admission meaningless; keeping the result only in chat loses it on context loss. |
| Hashing the prompt and the referenced item text | The spec requires precise invalidation. | Invalidating on any profile edit makes admission useless; invalidating on nothing makes it a lie. |
| One frontend route and an eval API | The operator asked for a training mode; annotating ten postings as JSON files is the friction that would keep the set from ever existing. | Files-only was rejected because the set would never be built. CLI-only capture was rejected because the final and most sensitive step, admitting, would still force a terminal. |
