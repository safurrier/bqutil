# bqutil correctness envelope

## Summary

bqutil is a Click CLI for BigQuery SQL files and query-job data. It can dry-run or
submit SQL. It stores project and job state so users can inspect a completed query
without submitting it again.

## Goals / Non-Goals

### Goals

- Provide explicit, automation-safe commands for query execution and job analysis.
- Preserve a recoverable job ID before local export or preview work.
- Keep machine-readable output free of terminal rendering and BigQuery SDK objects.

### Non-goals

- Authorize SQL or protect users from mutations contained in supplied SQL.
- Replace dbt, the BigQuery console, or Google Cloud authentication.
- Provide an interactive project or job browser.

## Requirements

### MUST

- The `bqutil` console entry point exposes `config`, `query`, `analyze`, and `compare`.
- Project resolution checks explicit `--project`, saved XDG Base Directory config,
  then `gcloud` config. If none is available, the command exits with a Click usage
  error that explains how to fix it. A missing `gcloud` executable never produces a
  traceback.
- Configuration remains `$XDG_CONFIG_HOME/bqutil/config.json` with
  `default_project`, `last_job_id`, `last_job_project`, and `last_job_location` keys.
- `query --dry-run` sends a `QueryJobConfig` with `dry_run=True` and
  `use_query_cache=False`. It doesn't wait for result rows or alter saved job state.
- A real query records its job ID, project, and BigQuery location before local export
  or preview work.
- `--preview-rows` reads at most the requested number of result rows.
- JSON and large language model output uses JSON primitives only. This includes
  query-plan summaries.
- Diagnostic output, SQL previews, and result previews use stderr. Structured
  `analyze` output uses stdout.
- Output selection is CSV, JSON Lines, or Parquet by suffix. The command records the
  job before reporting a Parquet or other local export failure.
- `compare BASELINE_JOB CANDIDATE_JOB` accepts query jobs only. It returns JSON-safe
  summaries with cache state and every public query-plan-stage field. It also returns
  exact candidate-minus-baseline deltas.
- Each metric keeps its baseline, candidate, absolute delta, and percent change. The
  metrics are duration, bytes processed, slot time, stage count, stage-records-read
  sum, and stage-shuffle-output-bytes sum.
- Missing values stay null. Percent change stays null when the baseline is zero. A
  missing query plan keeps its plan and stage metrics null, while an observed empty
  plan keeps zero stage metrics.
- Compare fetch errors name the baseline or candidate job, project, and location.
  They don't expose an SDK traceback.
- Compare doesn't return an optimization verdict, score, threshold, recommendation,
  or exit-code gate. Callers decide from the retained evidence.

### SHOULD

- `analyze --verbose` reports query-plan stage and bottleneck counts.
- `analyze --debug` renders only documented, stable source-job attributes.
- Every command help page includes a copyable example with an explicit project.
- Tests use fake BigQuery clients and jobs. Routine validation never submits a real
  BigQuery operation.

## Interfaces & Contracts

- `config --set-project/--show/--reset` owns persistent local state.
- `query QUERY_FILE` accepts `--project`, `--dry-run`, `--preview-rows`, `--output`,
  `--analyze`, `--verbose`, and `--set-default-project`.
- `analyze JOB_ID` accepts `PROJECT:JOB_ID`, `--project`, `--location`, `--last`,
  `--format json`, `--llm`, `--verbose`, and `--debug`.
- `analyze --last` reuses the saved job location. Callers can provide `--location`
  when inspecting a job that wasn't recorded locally.
- `compare` supports `PROJECT:JOB_ID`, shared project and location fallbacks, and
  per-job options. Qualified IDs override project fallbacks. Per-job options override
  shared fallbacks.
- Interactive selection isn't part of the package interface because it blocks
  non-interactive callers.
- Legacy dbt rewriting remains documented, opinionated preprocessing rather than a
  general dbt implementation. It runs for every submitted query so supported date-only
  macros and whitespace-form `ref()` calls aren't skipped.

## Invariants

- Dry runs don't create result rows or change bqutil state.
- JSON output never contains raw SDK objects or Rich terminal rendering.
- Compare preserves raw evidence alongside its exact numeric deltas. Stage aggregates
  remain explicitly named. They never claim to be unique rows or total query bytes.
- A completed real query's identity and location are durable before local export and
  preview work.
- The caller's credentials and supplied SQL retain authority over BigQuery access,
  billing, and table mutations.

## Acceptance

```bash
mise run check
uv run pytest -q
uv run ruff check bqutil tests
uv build
```

A release candidate also needs an isolated Git-source install smoke test. A live
`SELECT 1` is separate operational evidence because it creates a BigQuery job and can
incur charges.
