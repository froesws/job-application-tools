# CLI Contract: Profile Ingestion

A thin adapter over the same ingestion service. It owns argument parsing, terminal
output, and exit codes.

**Entry point**: `python -m cvtailor.cli` with the Makefile's `PYTHONPATH`.

## Commands

### `ingest`

```text
ingest --profile SLUG --file PATH [--file PATH ...]
       [--create] [--non-interactive] [--json]
       [--decisions FILE]
```

- `--profile SLUG` is required. The slug names an existing profile unless `--create`
  is given.
- `--file` is repeatable; 1 to 5 files, PDF or DOCX.
- `--create` allows committing into a profile directory that does not exist yet.
- `--non-interactive` suppresses prompts and the review loop.
- `--json` prints one JSON object on stdout and nothing else.
- `--decisions FILE` supplies explicit per-item decisions as a JSON array of
  `{item_id, action, text?}`. The command applies them and then commits. Without this
  flag, nothing is committed: the draft is built and its id is printed, so the
  approvals happen in `ingest review` or the UI.

There is no auto-approval: the constitution requires an explicit decision per item
before anything enters the master.

The command uploads, then polls the draft, printing one line per section as it
settles (`person ok`, `experience failed: budget_exhausted`). It returns when the
draft reaches `complete` or `failed`.

Without `--non-interactive`, the command enters the review loop after the draft is
built.

Exit codes: `0` success, `2` usage error, `3` unsupported or unreadable file
(every file rejected), `4` file too large, `5` no text layer in every file,
`6` extraction limit exceeded, `7` every section failed, `8` configuration error,
`9` unknown profile without `--create`, `10` master not renderable.

A file skipped inside an otherwise successful upload is a warning line on stderr and
does not change the exit code.

### `ingest show`

```text
ingest show DRAFT_ID [--json] [--section NAME]
```

Prints the draft: per-section status, item counts, readiness, and each item with its
quote and verification result. `--section` narrows the output.

Exit codes: `0` success, `1` draft not found, `2` usage error.

### `ingest review`

```text
ingest review DRAFT_ID
```

Interactive loop. For each item it shows the section, both language variants with the translated one
marked, the quote, the verification result, and the duplicate state. Accepted actions:

- `approve` — approve the current item
- `reject` — reject the current item
- `edit` — open `$EDITOR` on the item text, then re-validate
- `approve-verified` — approve every pending, verified, non-duplicate item
- `retry SECTION` — re-run a failed section from the stored text
- `next`, `prev` — move through items
- `show SECTION` — print the items of one section
- `commit` — validate, write the master, and exit
- `discard` — delete the draft and exit
- `quit` — leave the draft in place

`commit` prints the commit summary plus the profile path. `discard` asks for
confirmation unless `--non-interactive` is set.

## Non-interactive output

With `--json`, stdout carries exactly one object. After a commit:

```json
{
  "draft_id": "20261114T150000Z-1a2b",
  "profile": "software-engineer",
  "created": true,
  "added": 12,
  "skipped": 5,
  "skipped_breakdown": {"pending": 1, "rejected": 2, "unverified": 0, "duplicates": 2},
  "readiness": {"ready": true, "missing": []},
  "master_path": "software-engineer/master.json"
}
```

Without `--decisions`, the object stops at the draft and carries no commit fields:

```json
{
  "draft_id": "20261114T150000Z-1a2b",
  "state": "complete",
  "profile": "software-engineer",
  "counts": {"pending": 18, "approved": 0, "rejected": 0, "duplicate": 2, "unverified": 1},
  "readiness": {"ready": false, "missing": ["a summary block with lead"]}
}
```

Diagnostics go to stderr. Nothing prints the extracted text, the file content, or a
credential.

## Artifacts

A draft lives under the git-ignored data root until it is committed or discarded.
The command never stores the uploaded file.
