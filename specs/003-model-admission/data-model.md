# Phase 1 Data Model: Model Admission

Pydantic v2 models. The evaluation set and its records are personal data and live under
the git-ignored data root; only the example directory is committed.

## EvalManifest

| Field | Type | Rules |
| --- | --- | --- |
| `profile` | string | Slug the set is measured against. Required. |
| `postings` | string[] | Exactly ten posting ids. Any other count refuses to score. |
| `version` | string | `sha256` over the sorted tuples described in research decision 3. Recomputed on load; a stored value that disagrees is an error. |

## EvalPosting

One JSON file per posting under `eval/postings/`.

| Field | Type | Rules |
| --- | --- | --- |
| `id` | string | Stable, referenced by the manifest. |
| `text` | string | The posting as the user saw it. Untrusted text. |
| `expected_role_id` | string | Must exist in the profile's role options. |
| `must_include_ids` | string[] | 1 to 7 ids that exist in the profile. |
| `added_at` | string | ISO 8601 date. |

**Validation on load**: the set is refused when the manifest does not list exactly ten
postings, when a listed file is missing, when a role or bullet id is absent from the
profile, or when the stored version disagrees with the computed one.

## PostingOutcome

| Field | Type | Rules |
| --- | --- | --- |
| `posting_id` | string | The posting scored. |
| `outcome` | enum | `valid`, `invalid`, or `error`. |
| `role_ok` | boolean | True when the model's role equals `expected_role_id`; false on invalid or error. |
| `must_include_hit` | string[] | Expected ids the selection contained. |
| `must_include_missing` | string[] | Expected ids it did not. |
| `recall` | number | `len(hit) / len(expected)`, 0 to 1. |
| `error_code` | string \| null | The stable code when the outcome is `error`. |
| `retries` | integer | Validation retries used. |

A posting whose model output fails validation is `invalid`; a provider failure is
`error`. Both count exactly like a wrong answer.

## EvalMetrics

| Field | Type | Rules |
| --- | --- | --- |
| `valid` | integer | Postings with outcome `valid`. |
| `role_ok` | integer | Postings with `role_ok` true. |
| `mean_recall` | number | Mean of per-posting recall, 0 to 1. |
| `errors` | integer | Postings with outcome `error`, included in `valid`'s denominator. |

## Threshold verdict

| Field | Type | Rules |
| --- | --- | --- |
| `passed` | boolean | `valid == 10`, `role_ok >= 9`, `mean_recall >= 0.9`. |
| `failed_on` | string[] | Which of the three conditions failed, empty when passed. |

## EvalRun

The in-flight state exposed while the API runs an evaluation.

| Field | Type | Rules |
| --- | --- | --- |
| `run_id` | string | `YYYYMMDDTHHMMSSZ-xxxx`, same scheme as runs. |
| `state` | enum | `running`, `complete`, or `failed`. |
| `progress` | object | `{scored, total}`, updated per posting. |
| `outcomes` | PostingOutcome[] | Grows as postings finish; in manifest order once complete. |
| `metrics`, `verdict`, `archive` | optional | Present only when `state` is `complete`. |

The archive is written when the run reaches `complete`, whether the verdict passed or
not. A run never reports `complete` with fewer than ten outcomes.

## EvalRunResult

Archived as `eval/results/<UTC timestamp>-<provider>-<model>.json`.

| Field | Type | Rules |
| --- | --- | --- |
| `provider` | string | Provider name from the chain. |
| `model` | string | Model id. |
| `profile` | string | Profile slug. |
| `set_version` | string | The manifest version that was scored. |
| `prompt_hash` | string | Hash of the prompts and output schema used. |
| `referenced_text_hash` | string | Hash of the text of the referenced items. |
| `mode` | enum | `single` or `majority`. |
| `started_at`, `finished_at` | string | ISO 8601 UTC. |
| `metrics` | EvalMetrics | Computed in code. |
| `verdict` | Threshold verdict | See above. |
| `postings` | PostingOutcome[] | One per posting, in manifest order. |

## AdmissionRecord

Stored in `eval/admitted.json`.

| Field | Type | Rules |
| --- | --- | --- |
| `provider` | string | Part of the key. |
| `model` | string | Part of the key. |
| `profile` | string | Part of the key. |
| `set_version` | string | From the passing run. |
| `prompt_hash` | string | From the passing run. |
| `referenced_text_hash` | string | From the passing run. |
| `admitted_at` | string | ISO 8601 UTC. |
| `metrics` | EvalMetrics | The numbers shown in settings. |

## AdmissionState

Derived at read time; never stored.

| Value | Meaning |
| --- | --- |
| `admitted` | A record exists and all three hashes still match the current set, prompt, and referenced text. |
| `stale` | A record exists but one hash differs; `reason` names which. |
| `unadmitted` | No record exists. |

`reason` is one of `prompt_changed`, `set_changed`, `referenced_text_changed`, or
`model_changed`. The settings response reports the state per chain entry, and the
report marks a run `model_unadmitted` unless its state is `admitted`.

## Validation rules that live in code

- `valid` counts only selections that pass the validator; an invalid output is never
  silently repaired.
- `role_ok` compares ids, never labels.
- `recall` divides by the number of expected ids, not by the number selected.
- The threshold is evaluated after the run, never during it, and never adjusted to fit.
- Admitting is refused when the archived run's verdict is false, or when any hash no
  longer matches the current state.
