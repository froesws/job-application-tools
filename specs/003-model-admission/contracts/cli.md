# CLI Contract: Model Admission

A command group over the same service as the rest of the CLI. It owns argument parsing,
terminal output, and exit codes.

**Entry point**: `python -m cvtailor.cli` with the Makefile's `PYTHONPATH`.

## `eval run`

```text
eval run --model PROVIDER:MODEL
         [--set DIR]
         [--majority] [--json]
```

- `--model` is required and uses the same `provider:model` syntax as the chains.
- `--set` defaults to the data root's evaluation directory.
- The profile comes from the manifest. There is no override: the set's annotations are
  profile ids, so scoring it against another profile would mean scoring a different test.
- `--majority` runs three times per posting. At least two runs must produce a valid
  selection, and their ids merge by majority; fewer than two valid makes the posting a
  failure, and any error among the three is recorded. The mode is stored in the result.
- `--json` prints one object and nothing else.

Output: per-posting progress (`4/10 valid`), then the three metrics, the verdict, and the
archive path.

Exit codes: `0` run completed and passed, `1` run completed and failed the threshold,
`2` usage error, `3` invalid set, `4` unknown profile, `5` model unavailable,
`6` configuration error.

A run that completes always exits `0` or `1`; a failure to run exits with a higher code.
The archive is written in both cases, so a failing model still leaves evidence.

The archive file name sanitizes everything outside letters, digits, and hyphens, so a
model id such as `deepseek/deepseek-chat` becomes part of a flat name instead of a
directory. The model id itself is stored intact inside the file.

## `eval status`

```text
eval status [--model PROVIDER:MODEL] [--json]
```

Prints the admission state of every configured chain entry, or of one model:

```text
openrouter:deepseek/deepseek-chat   admitted   2026-11-14   10/10 valid   10/10 role   0.96 recall
gemini:gemini-2.5-flash             stale      prompt_changed
anthropic:claude-sonnet             unadmitted
```

Exit codes: `0` success, `2` usage error.

## `eval admit`

```text
eval admit --model PROVIDER:MODEL [--from RESULT_FILE] [--json]
```

Records an admission from a passing archive. `--from` defaults to the latest archive for
that model.

Refuses with exit `1` when the archive's verdict is false or when its hashes no longer
match the current set, prompt, or referenced text. It **never** edits the chain
configuration.

Exit codes: `0` admitted, `1` refused (stale or failed), `2` usage error,
`3` no matching archive.

## `eval withdraw`

```text
eval withdraw --model PROVIDER:MODEL [--json]
```

Removes the admission record. The model keeps running, marked unadmitted.

Exit codes: `0` withdrawn, `1` no record, `2` usage error.

## `eval compare`

```text
eval compare RESULT_A RESULT_B [--json]
```

Prints the two archives side by side: provider, model, mode, date, the three metrics, and
which postings differed.

Exit codes: `0` success, `2` usage error, `3` archive not found or unreadable.

## Secrets

There is no credential flag. A model's key comes from the environment or `.env`, exactly
as for normal runs. The harness never writes configuration.

## Non-interactive output

With `--json`, `eval run` prints:

```json
{
  "provider": "openrouter",
  "model": "deepseek/deepseek-chat",
  "profile": "software-engineer",
  "mode": "single",
  "metrics": {"valid": 10, "role_ok": 10, "mean_recall": 0.96, "errors": 0},
  "verdict": {"passed": true, "failed_on": []},
  "archive": "eval/results/20261114T160000Z-openrouter-deepseek.json"
}
```

`eval status` prints an array of `{provider, model, state, reason, admitted_at, metrics}`.
Nothing in any mode prints the posting texts, the profile content, or a credential.
