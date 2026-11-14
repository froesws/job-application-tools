<!--
Sync Impact Report
==================
Version change: 1.1.0 -> 2.1.0
Bump rationale: the change carries one MAJOR amendment and one MINOR addition, and both
land together, so the version is 2.1.0. MAJOR: Principle V is redefined — the evaluation
threshold now governs admission to the default chain instead of blocking every use of a
configured model, and an unevaluated model runs marked `model_unadmitted`, visible in the
report, the settings response, and the UI. MINOR: Principle I gains a narrow carve-out for
translation proposals, making the principle consistent with the Localization Contract
that already authorized them during ingestion. Principle IV's "reproduce" clause is
narrowed to match the storage model: a run keeps its selection, digest, and artifacts,
and re-renders only while its profile still contains the selected ids. Profiles become
first-class: the master moves to `profile/<slug>/master.json` with a per-profile
`blocklist.txt`, and a run records the profile it used. A corpus record is appended per
successful analyze, holding the digest and a posting hash but never the posting text.
The Layers constraint now names the shared service modules at the package root so the
six-layer enumeration stays intact.

Amended sections:
- Core Principle I (translation carve-out)
- Core Principle IV (reproduce clause)
- Core Principle V (admission redefined)
- Technology and Architecture Constraints (Layers, Data)
- Development Workflow and Quality Gates (evaluation set no longer blocks use)

Delivery notes: profile ingestion from uploaded files is specified in a follow-up spec
and is still a constitutional requirement; it is delivered before the frontend.

Adopted principles (unchanged in substance except IV and V):
- I. Master Profile Is the Single Source of Candidate Facts (NON-NEGOTIABLE)
- II. Code Owns Validation and Deterministic Decisions (NON-NEGOTIABLE)
- III. Untrusted Input, Isolated Secrets
- IV. Human Review Before Any Artifact Leaves the App
- V. Provider-Agnostic LLM Layer with Graceful Degradation
- VI. Fixed Pipeline and Deliberate Scope

Removed sections: none

Deferred TODOs: profile ingestion and the market-statistics reader are specified in
follow-up specs. Open product decisions (storage engine, UI language, repository
visibility, first provider chains) MUST be resolved in the relevant feature specs. CLI
flag names and the exact review-loop keys are spec details, not constitution placeholders.
-->

# CV Tailor Constitution

## Core Principles

### I. Master Profile Is the Single Source of Candidate Facts (NON-NEGOTIABLE)

Every positive claim about the candidate in any generated artifact MUST trace to an item in
the master profile. Models select and rank master items; they MUST NOT author new CV text.
The sole exception is the ingestion draft: a proposed item MAY enter the draft only when
it carries an exact quote verified in code against the uploaded file and is marked for
review, and it MAY enter the master only after the user approves that item. Within that
draft, a translation proposal MAY enter only when it carries the exact source text of an
item the user has already approved in the same draft, introduces no claim absent from
that source, and is marked `translated` for separate review. The validator MUST reject
unknown ids, skills absent from the master, and summaries without a lead block. A rendered CV MUST fit on one page; when auto-fit trims content, the trim MUST
surface as a warning.

Rationale: the PDF is sent to employers under the user's name. One invented claim
destroys trust and cannot be recalled after sending.

### II. Code Owns Validation and Deterministic Decisions (NON-NEGOTIABLE)

Every model output MUST pass a code validator before it can influence a render, a stored
run, or a later step. Language detection, pre-ranking, keyword matching, gap computation,
the blocklist check, the page-fit check, and the deterministic fallback live in pure
Python core and MUST run without a model. On invalid output, the pipeline MUST feed the
validation errors back for bounded retries and then fall back. Gaps, keyword coverage, red
flags, model notes, and layout warnings MUST appear only in the report, never in the PDF.

Rationale: free and weak models return malformed JSON and plausible but wrong picks.
Deterministic code is the only part of the system that can be tested exhaustively, so it
must own every decision that can be made without a model.

### III. Untrusted Input, Isolated Secrets

Job postings, uploaded CVs, and model output are untrusted data.

- Prompt construction MUST delimit posting and CV text as data and MUST instruct the model
  to ignore instructions embedded in that text.
- Model output MUST be constrained to validated ids and short text, so injected
  instructions cannot add claims or commands.
- API keys MUST live only in backend environment variables or a git-ignored `.env`, and
  MUST NOT appear in the browser, logs, API responses, or the repository. The settings
  API MUST report only whether a key is set.
- The backend MUST bind to localhost and allow only the frontend development origin.
- Uploads MUST be limited by size and type, and extracted text MUST never be executed.
- Prompt and answer logging MUST be off by default and MUST show an explicit warning when
  enabled.
- Personal data MUST remain in git-ignored folders. The raw job description and the API
  key MUST NOT be logged or exposed.
- Client and product names MUST NOT appear in any output; a blocklist check MUST run on
  every render.

Rationale: prompt injection and credential leakage are the two ways this app can harm its
user. Isolating both at the boundary keeps a local, single-user tool safe by default.

### IV. Human Review Before Any Artifact Leaves the App

Generated artifacts MUST be reviewable before they leave the app. The UI MUST show the
PDF, page count, layout warnings, the models that answered, computed gaps, and the review
checklist; the report MUST be downloadable separately from the PDF. Manual selection and
ordering changes MUST re-render through `POST /api/render` without an LLM call. Ingestion
MUST require per-item approval and MUST NOT auto-commit proposed items. Every run MUST
persist enough state (analysis, selection, models, retries, file paths, and the profile
it used) to reopen and inspect it, and to re-render it while that profile still contains
the selected ids.

Rationale: the user is accountable for what is sent. Review is the last line of defense
when a model, a validator, or a prompt fails.

### V. Provider-Agnostic LLM Layer with Graceful Degradation

All model access MUST go through the single `LLMClient` interface, which MUST support any
OpenAI-compatible provider. Per-step model chains MUST be configuration, not code. The
layer MUST provide transient retries, JSON extraction from messy output, validation
retries with error feedback, and a run log that records the model, retries, and errors.
Tailoring MUST narrow the model's job: pre-ranked candidates, one question per call, and
three-run majority voting per id where configured. When every model fails, a deterministic
selection built from pre-ranking scores MUST produce a valid CV. A model that passes the
evaluation threshold is admitted to the default chain. A configured model that has not
been evaluated MAY run, but every surface that records or displays it MUST mark it
`model_unadmitted`: the run report, the settings response, and the UI. Free model ids MUST
be replaceable without a code change. Weak-model correctness takes priority over prompt
elegance.

Rationale: free tiers change or disappear, and weak models fail in predictable ways. The
product must keep working when the best available model is bad.

### VI. Fixed Pipeline and Deliberate Scope

The version 1 core pipeline MUST be a fixed, explicit sequence of validated steps
(normalize, analyze, pre-rank, tailor, compute gaps, validate, render, report) behind the
`AgentStep` interface. Version 1 MUST NOT use CrewAI or any other agent framework; the
pipeline is plain `LLMClient` calls. Reconsidering an agent framework requires a
constitutional amendment, a new evaluation against the plain implementation (valid
selections, agreement with expected picks, run time, calls per run), and a recorded
verdict with scores. New product surface MUST start as a disabled Labs entry with its own
short plan before it becomes an enabled tab. New dependencies and directories MUST have a
concrete, documented need.

Rationale: the pipeline is fixed, so a planner-and-tools framework adds dependency churn
and hides retries and validation. Keeping it out of version 1 removes a moving part from
the critical path. Scope discipline keeps a single-user tool shippable.

## Technology and Architecture Constraints

- Runtime: Python 3.14 managed with `uv`; FastAPI with uvicorn; Pydantic v2 for every
  schema; ReportLab for PDF; pytest and ruff. `LLMClient` MUST stay dependency-free.
- Renderer: `backend/src/cvtailor/core/render_pdf.py` is the only PDF renderer. The API
  and agents MUST call its `render_pdf(master, selection, out_path)` function with a
  validated selection and the master; they MUST NOT reimplement layout. Its one-page
  auto-fit, font scaling, bullet caps, selection validation, and page-count result MUST
  be preserved.
- Layers: `backend/src/cvtailor/api` (HTTP), `core` (pure Python domain, validator,
  keywords, gaps, and the relocated renderer), `llm` (client, config, evals), `agents`
  (thin prompt builders), `storage` (files or SQLite per the storage decision), and
  `settings`. Core MUST NOT import FastAPI, the LLM client, or any web module. The
  application service shared by the HTTP API and the CLI sits above the layers as
  package-root modules (`service.py`, `pipeline.py`); it is not a seventh layer, and
  `core` MUST NOT import it.
- Frontend: React, TypeScript, Vite, Material UI, React Router, TanStack Query, a typed
  client generated from the backend OpenAPI schema, Vitest, and Testing Library. The
  browser MUST NOT hold API keys.
- Contract: the OpenAPI schema FastAPI generates is the API contract. The generated
  frontend client and the checked-in schema MUST change together, and CI MUST fail on
  drift.
- CLI: the backend MUST expose a command-line adapter over the same application service as
  the HTTP API. It MUST support reading a job description from a file, building or updating
  the profile from one or more CV files, tailoring and rendering a CV, and re-rendering an
  existing selection without an LLM call. It MUST offer a non-interactive mode for tests
  and automation and write the same run artifacts as the HTTP path.
- CLI review and safety: the review loop MUST show the digest summary, selected item
  counts, gaps, page count, and artifact paths; it MUST allow opening the PDF in the
  operating system viewer, editing the selection in `$EDITOR`, and re-rendering after
  validation. It MUST NOT render or edit the PDF inside the terminal. Secrets MUST come
  from `.env` or environment variables, never from command-line arguments, and a CLI run
  MUST be reopenable in the web UI.
- Development configuration: LLM API keys and provider connection settings (base URLs,
  model ids, timeouts) live in a git-ignored `.env` at the repository root and are read by
  the backend only. `.env.example` documents variable names without values. The values are
  not immutable: changing providers or models MUST NOT require code changes. Using `.env`
  is a development-stage choice and MAY later be replaced by a settings UI or OS keyring
  without changing `LLMClient`. Per-step model chains remain configuration, and no secret
  or connection value may be committed or returned by the API.
- Data: profiles are directories under `profile/<slug>/`. Each holds a human-readable
  `master.json`, a timestamped backup created on every save, and its own `blocklist.txt`;
  a missing blocklist is treated as empty. The slug is the profile's identity and display
  name, and profiles MUST be listed in slug order. Each run MUST persist `digest.json`,
  `analysis.json`, `selection.json`, `cv.pdf`, and `report.md`, plus `llm_log.jsonl` when
  logging is on, under a per-run directory in `data/runs/<id>/`, and MUST record the
  profile it used. Each successful analyze MUST append one record to `data/corpus.jsonl`
  holding the digest, a hash of the normalized posting, and the run date; the posting text
  MUST NOT be stored there. Whether run metadata moves to SQLite is an open decision;
  SQLite MUST NOT become the only copy of any master. Real profile data stays in
  git-ignored `profile/`; run and corpus data stay in git-ignored `data/`.
- Languages: every master text item carries EN and PT. The output language is an explicit
  run parameter, `pt-BR` (default) or `en-US`, exposed as a CLI flag and a frontend toggle.
  It maps to the master's `pt` or `en` variant. All internal artifacts, field names,
  prompts, and pipeline steps are English; only the final CV, report, and localized output
  labels change. UI chrome remains English in version 1. The renderer MUST NOT translate,
  humanize, or correct CV text at render time; it uses the approved master variant. Missing
  variants follow the Localization Contract.
- Privacy: real profile data, runs, and logs are git-ignored. Only `data.example/` and
  sample postings are committed, and CI MUST check that no real master file is committed.
- Out of scope for version 1: automatic applications, scraping LinkedIn or job boards,
  generating claims absent from the master, hosting for other users, and agent frameworks
  such as CrewAI. The app runs on the user's machine.

## Job Digest Contract

The analyze step produces one JSON object, the job digest. It MUST contain these fields
with these names and types; no field may be renamed or omitted:

| Field | Type | Rule |
| --- | --- | --- |
| `enterprise_name` | string | Company or organization named in the posting. |
| `date` | string | ISO 8601 date; posting date when stated, else the run date. |
| `job_title` | string | Title as stated in the posting. |
| `level` | string | `trainee`, `junior`, `mid_level`, or `senior`. |
| `resume` | string | Short summary of the posting, not the candidate CV. |
| `hard_skills` | array of strings | Technical skills and requirements. |
| `soft_skills` | array of strings | Interpersonal skills. |

`pleno`, `mid level`, and `mid-level` are accepted as input aliases for `mid_level` and
MUST be normalized before storage. Every skill item MUST be checked against the posting
text or a documented alias and dropped when unsupported. Items MUST be non-empty and
deduplicated. Extra fields returned by a model MUST be discarded. An invalid digest
follows the retry and fallback rules in Principle II.

`POST /api/jobs/analyze` MUST return the digest, and each run MUST store it as
`digest.json`. A richer analysis MAY be stored alongside it, but it MUST NOT rename or
omit these fields. The digest is an internal artifact and MUST be produced in English
regardless of output language; the output language applies only to the CV, report, and
localized output labels.

## Localization Contract

- Output languages: `pt-BR` (default) and `en-US`. The CLI MUST expose the choice as a
  parameter; the frontend MUST expose it as a toggle. There is no silent auto-switch based
  on the posting language.
- Mapping: `pt-BR` uses the master's `pt` variants; `en-US` uses the master's `en`
  variants. The selection and run MUST record both the requested output language and the
  render language used.
- Internal English: prompts, logs, JSON field names, digest text, analysis, selection,
  gaps, and other run artifacts are English. Only the final CV, report, and localized
  output labels change with the output language.
- No render-time rewriting: the renderer MUST use the approved master variant. It MUST NOT
  translate, humanize, paraphrase, or correct spelling at render time. Such a change would
  be new CV text and violates Principle I.
- Profile localization: translation, fluency edits, and typo fixes MAY be proposed by a
  dedicated model step, but only during ingestion or profile review. It produces proposed
  items with source text, target text, and a reason, marked `needs_review`; the user
  approves each item. The step MUST NOT run during tailoring or rendering. Proposals MUST
  preserve numbers, named entities, technologies, scope, and meaning, and MUST NOT add
  claims. The validator SHOULD flag changed numbers or named entities; human review is the
  final gate.
- Missing variants: a target-language variant that is missing or unapproved MUST NOT be
  machine-translated during the run. The run MUST either fail validation with a list of
  missing items or fall back to the other complete language as a whole with a visible
  warning. It MUST NOT mix languages in one CV.
- Report: labels and computed sections are localized in code. Free-text model notes MAY be
  machine-translated only with a visible label; they MUST NOT feed back into the CV or
  master.

## Development Workflow and Quality Gates

- The milestone sequence in the project plan is the delivery sequence, with M7 (CrewAI
  spike) removed. A milestone is done only when its stated "Done when" condition is
  demonstrated. M0 starts the test suite in the new repository layout; M0 also
  ensures each completed task produces a commit, so that unreviewed work is not
  considered complete.
- Tests are required for new behavior and its failure path. The suite MUST cover the
  validator, the renderer (one page for every profile, including the worst case), keyword
  matching, gap computation, the blocklist, the LLM layer against a local fake provider,
  agents with scripted fake models (success, bad JSON, invalid ids, total failure with
  deterministic fallback), API contract tests (including the digest schema and level
  normalization), frontend component tests for the tailoring panel and ingestion stepper,
  and end-to-end verification of the paste-tailor-download flow before M4 is declared done
  (automated once Playwright is introduced).
- CLI adapter tests MUST cover the full path from arguments to run artifacts with a fake
  LLM: profile ingestion, tailor, render without an LLM call, validation failure,
  deterministic fallback, review-mode input handling, and non-interactive mode.
- Localization tests MUST cover the `pt-BR` default, the `en-US` override, CLI and frontend
  mapping to master variants, missing-variant behavior, and proof that rendering makes no
  LLM call and does not rewrite text.
- The evaluation set MUST hold 8 to 10 real postings with an expected role title and
  must-include bullets. Every candidate model MUST be scored against it before it is
  admitted to a default chain, and a posting MUST be added whenever a model makes a
  mistake that is noticed. The passing threshold MUST be chosen before a model is
  admitted. Until the set exists, configured models run marked `model_unadmitted` as
  Principle V requires; the mark disappears only when a model passes the threshold.
- Required checks before merge: backend tests, frontend tests and build, type checks, lint,
  and the OpenAPI drift check, run through the `make` targets. Until the frontend and the
  checked-in OpenAPI schema exist, only the applicable backend targets run; the frontend
  and drift gates MUST be introduced in the same change that introduces them. No check may
  be stubbed as a no-op green. Report exactly which checks ran and which could not run.
- CI MUST run backend tests, frontend tests and build, the OpenAPI drift check, and the
  committed-data check. The frontend and OpenAPI drift jobs join CI in the same change
  that introduces the frontend and the checked-in schema; they MUST NOT be added as
  placeholder no-op passes before then.
- Decisions made during delivery MUST be recorded as short notes in `docs/`, including the
  decision to exclude CrewAI from version 1.
- A change that weakens a principle in this document MUST be proposed as a constitutional
  amendment, not slipped in as implementation detail.

## Governance

This constitution supersedes `AGENTS.md`, `.opencode/rules/*.md`, and ad hoc practice.
Where they conflict, this document wins and they MUST be amended.

**Amendment procedure**: changes are proposed as a pull request that (1) states the
principle or section affected and the reason, (2) updates this file together with a Sync
Impact Report, (3) updates dependent documentation and rules in the same change, and (4) is
reviewed by the project owner. Amendments that remove or redefine a principle require an
explicit migration note for in-flight specs.

**Versioning policy**: semantic versioning. MAJOR for backward-incompatible governance
changes, principle removals, or redefinitions. MINOR for a new principle, a new section, or
materially expanded guidance. PATCH for clarifications, wording, typo fixes, or
non-semantic refinements. The version line and the Sync Impact Report MUST agree.

**Compliance review**: every spec, plan, task list, and pull request MUST verify compliance
with the Core Principles, and a reviewer MUST reject work that violates a NON-NEGOTIABLE
principle. Complexity, new dependencies, and new directories MUST be justified in the pull
request. Evaluation and model-retention decisions MUST be recorded with data, not asserted.

**Runtime guidance**: `AGENTS.md` and `.opencode/rules/*.md` hold day-to-day conventions
and MUST remain consistent with this constitution.

**Version**: 2.1.0 | **Ratified**: 2026-11-14 | **Last Amended**: 2026-11-14
