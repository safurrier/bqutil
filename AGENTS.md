# bqutil

**When a user corrects you or provides tribal knowledge or gotchas—something you
could not have known from reading the code or your prompt—you MUST document it in
the nearest AGENTS.md before continuing.**

bqutil is a Click CLI for submitting BigQuery SQL files and analyzing query jobs.
The entry point is `main` in `bqutil/cli.py`; public correctness contracts live in
`SPEC.md`.

## How to Work Here

Add or update fake-client tests before changing command behavior. Run the fast gate,
then update the active scaffold plan and run the sync contract before handoff.

## Commands

- **Setup:** `mise run setup`
- **Fast gate:** `mise run check`
- **Focused tests:** `uv run pytest -q`
- **Build:** `uv build`
- **Handoff contract:** `mise run sync-check`

## Gotchas

- **DO** use fake BigQuery clients in routine tests. **NOT** submit a live query as
  part of the normal suite. **BECAUSE** live jobs require credentials and can incur
  charges.
- **DO** keep JSON output limited to primitives and send previews or diagnostics to
  stderr. **NOT** expose SDK objects or Rich rendering on structured stdout.
  **BECAUSE** scripts consume these output contracts.
- **DO** preserve the XDG config path and its three state keys. **NOT** change or
  discard saved state without an explicit migration. **BECAUSE** `--last` and project
  fallback depend on that compatibility surface.
- **DO** require flags, arguments, or saved configuration for every automation input.
  **NOT** add mandatory interactive prompts. **BECAUSE** noninteractive callers must
  fail with actionable errors instead of hanging.
- **DO** use `--dry-run` before unfamiliar SQL and an explicitly approved project for
  a live smoke test. **NOT** treat dry-run proof as permission to execute arbitrary
  SQL. **BECAUSE** caller-supplied SQL retains authority over billing and mutations.
- **DO** preserve both jobs' raw summaries and explicit candidate-minus-baseline
  deltas in comparisons. **NOT** add optimization labels, thresholds, or exit-code
  gates. **BECAUSE** agents need the source evidence to make context-specific choices.

## Related Context

| Path | What's there |
|---|---|
| `README.md` | Human installation, authentication, and command workflows |
| `SPEC.md` | Public behavior and output invariants |
| `docs/explanation/architecture.md` | Module ownership and execution flow |

<!-- generated-by: context-engineering@2.6.3 | last-updated: 2026-08-25 -->
