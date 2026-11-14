# CV Tailor — v1 MVP (core pipeline)

**Feature Branch**: `001-cv-tailor-v1-mvp`
**Created**: 2026-11-14
**Status**: ready-for-agent

## Problem Statement

For now the manual process of tailoring a CV to each posting is acceptable — the user reads the job, picks role, bullets, and projects from their profile, and keeps the result to one page. This works for occasional applications but does not scale: swapping between profiles, remembering which selection went to which employer, and re-doing the same edits across English and Portuguese versions becomes tedious quickly.

The long-term goal is to let the user save and switch between named profiles (e.g., "software-engineer", "data-scientist", "leadership"), each with its own master profile, and re-render the CV for any posting without re-authoring every section. This spec builds the core pipeline (analyze → validate → render → report) so that when profiles are added, the same validation, one-page guarantee, and report generation apply automatically.

## Solution

A local, single-user application that turns a pasted job posting into a reviewable CV package. The posting is analyzed into a fixed job digest. A model proposes a selection drawn only from ids that already exist in the master profile. Code validates that selection, retries with the validation errors, and falls back to a deterministic selection when every model fails. The existing renderer produces a one-page PDF in the posting's language, and a separate report explains gaps, keyword coverage, red flags, model attempts, and layout warnings. The user reviews the PDF, adjusts the selection, and re-renders without another model call. Every run is stored and can be reopened. A command-line adapter exposes the same flow for automation. Profile support (named saves, profile switching) will be added in a follow‑up spec; the core pipeline is deliberately built so that profiles integrate without changing the validation, renderer, or report contract.

The product promise is narrower than a writing assistant and stronger: the model chooses and ranks master items, code decides what is allowed, and the user reviews what leaves the app.

## User Stories

### Analyze a posting

1. As a job seeker, I want to paste a job posting and receive a structured job digest, so that I can judge the match before spending time on a tailored CV.
2. As a job seeker, I want the digest to name the enterprise, posting date, job title, seniority level, and a short summary of the posting, so that I can confirm the analysis understood the role.
3. As a job seeker, I want the digest to separate hard skills from soft skills, so that I can compare technical requirements against my profile.
4. As a job seeker, I want level aliases such as "pleno", "mid level", and "mid-level" normalized to one stored value, so that filters and reports stay consistent.
5. As a job seeker, I want skills that the posting does not actually support dropped from the digest, so that the analysis does not hallucinate requirements.
6. As a job seeker, I want duplicate and empty skill entries removed, so that the report counts are meaningful.
7. As a job seeker, I want extra fields returned by a model discarded, so that the digest contract stays stable across providers.
8. As a job seeker, I want the posting language detected automatically and shown to me, so that I can catch a wrong detection before rendering.
9. As a job seeker, I want to override the detected language, so that a mixed-language or unusual posting still renders in the language I choose.
10. As a job seeker, I want analysis to work when the posting is pasted as plain text, so that I do not need to save a file first.

### Tailor a selection

11. As a job seeker, I want the system to propose a selection built only from ids in my master profile, so that the CV cannot claim anything I have not approved.
12. As a job seeker, I want the proposed selection to pick one role title from my approved options, so that the CV headline matches the posting.
13. As a job seeker, I want the proposed selection to choose one to four summary blocks with a lead block first, so that the summary reads as a coherent opening.
14. As a job seeker, I want the proposed selection to choose one to seven bullets per role, so that each role stays concise.
15. As a job seeker, I want the proposed selection to order my skill groups by relevance to the posting, so that the most relevant skills appear first.
16. As a job seeker, I want the proposed selection to include only the projects and research items that help this posting, so that the CV stays focused.
17. As a job seeker, I want the proposed selection to reflect the posting's emphasis, so that the same master profile produces a different CV for different roles.
18. As a job seeker, I want the system to retry a model when its output fails validation, so that a weak model can correct itself within a bounded budget.
19. As a job seeker, I want the validation errors fed back to the model on retry, so that the next attempt targets the actual problem.
20. As a job seeker, I want a deterministic fallback selection when every model fails, so that a bad provider day does not block me from producing a valid CV.
21. As a job seeker, I want the fallback to be built from keyword pre-ranking rather than model output, so that it is reproducible and explainable.
22. As a job seeker, I want to see which model answered each step, so that I can judge whether the result reflects the model I intended.
23. As a job seeker, I want retry counts and error messages recorded per run, so that I can diagnose repeated failures.
24. As a job seeker, I want a run to fail with a clear message when no valid selection can be produced, so that I never receive a CV built from unvalidated output.

### Render the CV

25. As a job seeker, I want a one-page PDF in the language of the posting, so that I can send it without further editing.
26. As a job seeker, I want the renderer to shrink spacing before removing content, so that the CV keeps as many of my chosen items as possible.
27. As a job seeker, I want a warning when auto-fit shrinks the layout, so that I know the result differs from the standard template.
28. As a job seeker, I want a warning that names the bullets removed by auto-fit, so that I can decide whether to cut something else instead.
29. As a job seeker, I want the render blocked when a selected item matches my blocklist, so that a client or product name never leaves the app.
30. As a job seeker, I want a run rejected when it still exceeds one page after every auto-fit attempt, with the offending counts shown, so that the one-page promise is never silently broken.
31. As a job seeker, I want to preview the PDF in the app, so that I can review the actual artifact before downloading it.
32. As a job seeker, I want to download the PDF, so that I can attach it to an application.
33. As a job seeker, I want to download the report separately from the PDF, so that private analysis never ships with the CV.
34. As a job seeker, I want the PDF to contain no gaps, red flags, model notes, or layout warnings, so that internal reasoning stays out of the employer's copy.

### Review the result

35. As a job seeker, I want the report to repeat the digest, so that I can confirm the CV targets the posting I intended.
36. As a job seeker, I want the report to list hard skills from the posting that my selection does not cover, so that I can see real gaps before applying.
37. As a job seeker, I want keyword coverage expressed as a proportion of posting requirements, so that I can compare selections quickly.
38. As a job seeker, I want red flags such as a seniority mismatch or an uncovered must-have skill, so that I can decide whether the role is worth pursuing.
39. As a job seeker, I want selected item counts per section, so that I can spot an unbalanced selection.
40. As a job seeker, I want a short review checklist, so that I know what to verify before sending the CV.
41. As a job seeker, I want the models used, retry counts, and fallback status in the report, so that I can interpret the result's reliability.
42. As a job seeker, I want every layout warning recorded in the report, so that the review record matches the artifact I downloaded.

### Adjust and re-render

43. As a job seeker, I want to remove a bullet from the proposed selection, so that I can drop something I do not want to emphasize.
44. As a job seeker, I want to reorder bullets within a role, so that the strongest point comes first.
45. As a job seeker, I want to swap summary blocks, so that the opening matches my judgment.
46. As a job seeker, I want to change skill priority, so that a skill the model underrated moves up.
47. As a job seeker, I want to toggle projects and research items, so that I control what appears.
48. As a job seeker, I want to change the role title and language before re-rendering, so that I can correct the model's read of the posting.
49. As a job seeker, I want re-rendering to skip the model entirely, so that manual edits are fast, free, and reproducible.
50. As a job seeker, I want a manual re-render to keep the original run intact, so that I can compare the model's proposal with my edit.
51. As a job seeker, I want a re-rendered run linked back to the run it came from, so that I can trace how the CV evolved.

### Manage runs

52. As a job seeker, I want to list previous runs with date, enterprise, title, and language, so that I can find an earlier application.
53. As a job seeker, I want to reopen a run and see its digest, selection, report, and PDF, so that I can resume review where I stopped.
54. As a job seeker, I want every run to persist enough state to reproduce the same selection and artifact, so that I can trust the record.
55. As a job seeker, I want run artifacts stored locally and excluded from version control, so that my personal data is not committed.

### Use the command line

56. As a CLI user, I want to tailor a CV from a posting file, so that I can script the flow.
57. As a CLI user, I want to read the posting from standard input, so that I can pipe text without creating a file.
58. As a CLI user, I want a non-interactive mode that emits machine-readable output and run artifacts, so that tests and automation can rely on it.
59. As a CLI user, I want to re-render an existing selection without a model call, so that edits are as cheap on the command line as in the UI.
60. As a CLI user, I want an interactive review loop that shows the digest summary, selected counts, gaps, page count, and artifact paths, so that I can review without opening the UI.
61. As a CLI user, I want to open the PDF in my operating system viewer, so that I can inspect it quickly.
62. As a CLI user, I want to edit the selection in my editor and re-render after validation, so that manual changes stay in one flow.
63. As a CLI user, I want a CLI run to be reopenable in the web UI, so that I can switch tools mid-review.
64. As a CLI user, I want secrets read only from the environment or a git-ignored environment file, so that keys never appear in shell history or process listings.

### Configure and operate

65. As a job seeker, I want the settings surface to report only whether an API key is set, so that the key itself never reaches the browser.
66. As a job seeker, I want to change provider, base URL, model ids, timeouts, and per-step chains through configuration, so that switching providers needs no code change.
67. As a job seeker, I want transient provider errors retried, so that a brief network failure does not fail the run.
68. As a job seeker, I want a total time budget per run, so that a slow provider cannot hang the app.
69. As a job seeker, I want the backend bound to localhost and limited to my frontend development origin, so that no other machine can call it.
70. As a job seeker, I want posting text and keys kept out of logs, API responses, and the browser, so that private data stays private.
71. As a maintainer, I want the OpenAPI schema to be the single API contract and a drift check in CI, so that the typed client cannot silently diverge.
72. As a maintainer, I want the evaluation set of real postings to gate model admission to a chain, so that a model is not promoted on vibes.

## Implementation Decisions

### Architecture

- The version 1 pipeline is the fixed sequence from the constitution: normalize, analyze, pre-rank, tailor, compute gaps, validate, render, report. Each step implements the `AgentStep` interface; no agent framework is introduced.
- Code is split into seven layers: HTTP API, pure domain core, LLM client layer, thin prompt builders, storage, settings, and a frontend. The core layer must not import FastAPI, the LLM client, or any web module.
- Both the HTTP API and the CLI call one application service. Neither adapter owns pipeline logic.
- FastAPI with uvicorn serves the API; Pydantic v2 defines every request, response, and stored schema; ReportLab remains the only PDF renderer; pytest and ruff are the Python toolchain.
- The frontend is React, TypeScript, Vite, Material UI, React Router, TanStack Query, and a typed client generated from the backend OpenAPI schema, tested with Vitest and Testing Library.

### API contract

| Method and route | Purpose |
| --- | --- |
| `POST /api/jobs/analyze` | Turn posting text into a validated digest. |
| `POST /api/tailor` | Run analyze, pre-rank, tailor, validate, render, and report; return the run summary. |
| `POST /api/render` | Validate and render a supplied selection with no model call; persist a derived run. |
| `GET /api/runs` | List run summaries. |
| `GET /api/runs/{id}` | Return digest, selection, analysis, model log, warnings, and artifact availability. |
| `GET /api/runs/{id}/cv.pdf` | Serve the rendered PDF. |
| `GET /api/runs/{id}/report.md` | Serve the report. |
| `GET /api/profile` | Return the master profile so the UI can resolve labels and offer valid edits. |
| `GET /api/settings` | Return key-set booleans, active chains, limits, and version info only. |

- Errors serialize as an object with `code` and `message`. Stable codes cover invalid posting, digest failure, invalid selection, blocklist hit, page overflow, model unavailable, fallback exhaustion, and configuration error.
- `POST /api/tailor` accepts posting text plus an optional language override. It never returns the posting text it received.
- `POST /api/render` accepts a full selection and, optionally, the id of the run it derives from. It copies the base run's digest and analysis, records the origin, and writes a new run. It never mutates the base run.
- Listing and detail responses omit the raw posting. The posting is stored server-side only to make a run reproducible.
- The OpenAPI schema is generated from the Pydantic models and checked into the repository; CI fails when the generated client and the checked-in schema drift.

### Master profile and selection

- The master profile keeps the schema the renderer already consumes: person, role options, summary blocks, skill groups with core and extra items, experience entries with roles and bullets, research, projects, education, and certifications, with EN and PT text on every item.
- The profile moves to the constitution's profile root. The renderer's default master path changes accordingly, but the `render_pdf` contract — master and selection in, one-page-fitting PDF plus a result object out — is preserved.
- Selection validation remains the authority: unknown ids, skills absent from the master, duplicate bullets, out-of-range counts, and a non-lead first summary block are rejected before any render.
- Selection counts are fixed: one to four summary blocks, one to seven bullets per role or research item, and any number of projects, matching the renderer's validator.

### LLM layer

- All model access goes through a single dependency-free `LLMClient` interface. One OpenAI-compatible adapter implements it.
- Provider, base URL, model ids, timeouts, retry counts, and per-step chains come from environment configuration read by the backend only. A git-ignored environment file at the repository root supplies development values; a committed example file documents names without values.
- Validation retries are bounded. The default budget is two retries per step, with validation errors included in the follow-up prompt.
- Three-run majority voting per id is supported as per-step configuration and is off by default.
- Transient provider errors are retried with backoff inside the per-run time budget.
- Model output is constrained to ids from the master catalog plus short enumerations. Free text that could add claims is rejected.
- Posting and profile text are delimited as data in prompts, with an explicit instruction to ignore embedded instructions.

### Deterministic decisions

- Language detection, keyword pre-ranking, coverage, gap computation, red-flag detection, blocklist checking, and page-fit checking are pure Python and run without a model.
- The deterministic fallback builds a valid selection from pre-ranking scores: role by title overlap, summary blocks by digest overlap with a lead block first, bullets by keyword coverage, skill priority by posting overlap, and projects and research by overlap. If the fallback cannot satisfy the validator, the run fails rather than rendering.
- Gaps are digest hard skills with no mapped master item. Coverage is the proportion of digest hard skills present in the selection. Red flags are level mismatch, uncovered must-have skills, blocklist-adjacent items, and auto-fit trimming.
- The blocklist is a user-owned local file with a committed example. Every render, including manual re-renders, checks every selected string. A hit blocks the render and names the offending item by id, not by content.
- The renderer's auto-fit sequence is preserved. If every attempt still exceeds one page, the API rejects the render and returns the section counts that must shrink.

### Job digest

- The digest keeps the constitution's exact field set and names: `enterprise_name`, `date`, `job_title`, `level`, `resume`, `hard_skills`, `soft_skills`. No field is renamed or omitted.
- `level` is constrained to `trainee`, `junior`, `mid_level`, or `senior`; input aliases normalize before storage.
- Every digest skill is checked against the posting text or a documented alias and dropped when unsupported. Empty and duplicate entries are removed. Unknown model fields are discarded.
- An invalid digest follows the same bounded retry and fallback rule as the selection: retry with errors, then fail the run with a stable error code.

### Persistence

- The master profile lives in the constitution's profile root as human-readable JSON, with a timestamped backup on every save. This release does not add a profile editor, so saves happen through the file or CLI-compatible tooling only.
- Each run owns a directory under the constitution's run root containing run metadata, the digest, the analysis, the selection, the PDF, the report, and the model log when logging is enabled. The raw posting is stored beside them but is never returned by the API.
- Run metadata records schema version, creation time, origin run, language, digest hash, models per step, retry counts, fallback status, and artifact paths.
- Run ids are UTC-timestamped and sortable. Directory writes are atomic enough that an interrupted run leaves no readable half-run.
- SQLite is not introduced. The run index is derived by scanning run directories, which keeps one copy of the truth and satisfies the constitution's open storage decision for v1.
- The profile root, run root, blocklist, and environment file are git-ignored. Only example files and sample postings are committed, and a check fails if a real master profile is committed.

### Frontend

- One application shell with three routes: tailoring, run history, and settings.
- The tailoring view holds the posting text, analysis result, selection editor, warnings, PDF preview, and download actions. It does not hold the API key or the raw posting after submission.
- The selection editor covers role title, language, summary blocks, per-role bullet order, skills priority, research, and projects, and always posts to the render endpoint rather than re-running the model.
- Warnings, gaps, coverage, and red flags render from the run detail response, with the report available as a separate download.
- The UI is English-only in v1; CV output remains EN/PT. A Portuguese UI translation is deferred.
- Server state goes through the generated typed client and TanStack Query. No direct `fetch` calls from components, and no additional data library.

### CLI

- Commands: tailor from a posting file or stdin, render an existing selection, list and show runs, and an interactive review mode.
- Every command supports a non-interactive mode that emits machine-readable output and writes the same run artifacts as the HTTP path.
- Review mode prints the digest summary, selected counts, gaps, page count, and artifact paths; can open the PDF in the operating system viewer; can edit the selection in the user's editor; and re-renders only after validation.
- Secrets are read from the environment or the environment file and never from command-line arguments.
- A CLI-created run uses the same storage layout, so the web UI can reopen it.

### Model admission

- A candidate model enters a chain only after scoring against the evaluation set of eight to ten real postings with expected role titles and must-include bullets.
- The threshold is fixed before evaluation: valid selection in ten of ten runs, expected role title in at least nine of ten, and mean must-include recall of at least 0.9. A model that misses the threshold is not admitted.
- The evaluation set grows by one posting whenever a model mistake is noticed.

### Operational limits

- Posting text is capped at a documented size, and requests over the cap fail with the invalid-posting code.
- Each model call has a timeout, and each run has a total time budget; exceeding either fails the run with the model-unavailable code.
- The server binds to localhost and allows only the frontend development origin.
- Prompt and answer logging is off by default and warns explicitly when enabled.

## Testing Decisions

A good test asserts observable behavior at the outermost boundary that can express the rule. It does not reach into private functions, assert call order, or mock the domain. The domain is deterministic and fast, so the tests keep it real and replace only the external, nondeterministic edge: the `LLMClient`.

### Seams

- **Primary seam: the HTTP API.** Tests build the FastAPI app with temporary profile and run roots and a scripted fake `LLMClient`, then exercise requests and responses. This single seam covers analysis, pre-ranking, tailoring, validation, retries, fallback, rendering, report generation, persistence, artifact serving, error serialization, and secret redaction.
- **Existing seam: the renderer.** `render_pdf` keeps its pure-function contract and is tested directly for the one-page guarantee, language variants, font fallback, bullet trimming, and the worst-case profile. The constitution requires this coverage, and the seam already exists.
- **Adapter boundaries: CLI and UI.** The CLI is verified through its process boundary and the UI through rendered components with the generated client mocked. Both are thin adapters over the same service, so these tests check wiring, exit codes, empty and error states, and re-render behavior — never domain rules already covered at the API seam.

### Coverage

- **API tests**: the digest contract and level normalization; unsupported and duplicate skills dropped; invalid model output retried with errors fed back; unknown ids rejected; fallback produces a valid selection; blocklist hit blocks the render; page overflow returns the overflow code; manual re-render makes no model call and derives a run; run listing and reopening; posting text absent from every response; key value absent from every response and log.
- **Prompt-injection tests**: postings containing instructions to add claims, plus fake models returning unknown ids or invented text, must never produce a PDF or selection containing the invented material.
- **Renderer tests**: exactly one page for every profile in the fixture set, including the worst case; trimming warnings name removed bullets; both languages render.
- **CLI tests**: tailor from file and stdin; non-interactive mode; render without a model call; validation failure; deterministic fallback; review-mode input handling; artifacts match the HTTP path.
- **Frontend tests**: the tailoring panel from empty to analysis to selection; warnings and gap display; selection edits triggering a render-only call; download actions; error and loading states; history reopening a run.
- **Evaluation harness**: the committed posting set scores a candidate model against the admission threshold and records the result.

### Prior art

The repository has no test suite yet, so this spec establishes the pattern. The renderer's pure functions are the first unit-level seam; the API contract tests become the reference for feature tests, and the CLI and frontend tests follow the same boundary rule. The constitution's M0 requirement that 43 existing tests keep passing cannot be met in this repository because those tests are not present; the new suite starts from this spec.

## Out of Scope

- Profile ingestion from uploaded CV files, including quote verification and per-item approval. The master profile is authored as JSON in this release; ingestion is a follow-up spec.
- Scraping LinkedIn or any job board, and automatic applications.
- Multi-user hosting, accounts, and authentication.
- Agent frameworks, including CrewAI.
- SQLite or any database. Runs are directories, and the index is derived.
- A Portuguese translation of the UI.
- Editing the PDF inside the terminal.
- Cover letters, portfolios, or any artifact other than the CV and its report.
- OCR, document conversion, or parsing non-text postings.
- Model fine-tuning and prompt marketplaces.

## Further Notes

- **Rules conflict to resolve during implementation.** `.opencode/rules/rules.md` forbids adding React Query, but the constitution mandates TanStack Query and React Router. The constitution supersedes the rules, so the rules file must be amended in the same change that adds the frontend.
- **Renderer relocation.** The renderer currently sits beside the profile and defaults to a file there. Moving it into the core layer must preserve `render_pdf`, and the default master path must follow the constitution's profile root.
- **Missing baseline.** The constitution references a project plan with milestones and 43 existing tests. Neither is in this repository, so the milestone sequence and the baseline suite cannot be verified here. This spec starts the suite from zero.
- **Tracker.** No issue tracker is configured and no git remote exists. The spec is published as a file under `specs/`, and `ready-for-agent` is recorded in the status line rather than as a tracker label. Moving it to issues later needs a tracker setup.
- **Open decisions this spec resolves.** Storage stays on the filesystem for v1; the UI is English-only; the first chains are a single OpenAI-compatible model per step with optional fallbacks; the model admission threshold is fixed above. Repository visibility remains a product-owner decision and does not affect the code.
- **Constitutional compliance.** The spec keeps the master profile as the single source of candidate facts, code-owned validation and deterministic fallback, untrusted input handling, human review, provider-agnostic model access, and the fixed pipeline.
- **Profile support (follow-up).** This spec assumes one master profile. Named profiles with switchable `profile/<name>/master.json` and a profile selector in the UI/CLI are deferred to a separate spec so that the core pipeline stabilizes first.