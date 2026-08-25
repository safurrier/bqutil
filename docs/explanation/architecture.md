---
id: bqutil-architecture
title: bqutil architecture
description: Module ownership and execution flows for the bqutil CLI.
index:
  - id: system-overview
    keywords: [modules, ownership, sdk, configuration]
  - id: primary-flows
    keywords: [query, dry-run, analyze, execution]
  - id: invariants
    keywords: [json, state, automation, adapter]
  - id: validation
    keywords: [tests, build, live-query]
---

# bqutil architecture

## System overview

bqutil is a single-process Click CLI. It owns local configuration and terminal
rendering. The Google BigQuery SDK and the caller's credentials continue to own
Google Cloud authentication, query execution, and job metadata.

| Module | Responsibility |
|---|---|
| `bqutil.cli` | Command parsing, project resolution, stdout/stderr contracts, and workflow order |
| `bqutil.config` | XDG Base Directory JSON state: default project and last submitted job identity, including location |
| `bqutil.gcp` | The one concrete `gcloud` and BigQuery SDK adapter |
| `bqutil.query` | Legacy macro preprocessing, query submission, dry-run setup, and bounded row access |
| `bqutil.analysis` | JSON-primitive query-plan summaries and exact comparison evidence |

## Primary flows

1. `query` resolves a project, reads and optionally preprocesses SQL, then either
   sends a BigQuery dry-run job or submits a real job.
2. A real query waits for completion and records its job identity and location before
   any local export or preview. This preserves recovery information if a filesystem
   operation fails.
3. `analyze` fetches an existing job through the concrete adapter. It accepts an
   explicit location or reuses the saved location for `--last`, then maps the SDK
   object to terminal text or JSON-safe records.
4. `compare` resolves baseline and candidate jobs independently through the same
   adapter. A fetch failure names the affected operand and resolved project/location.
   The analysis module retains both raw summaries, including all public query-plan
   stage evidence, and computes exact candidate minus baseline deltas without issuing
   an optimization verdict.

## Invariants

- CLI functions are the ingress seam. Domain modules stay independent of Click.
- The BigQuery adapter stays concrete because the package has one SDK integration,
  not a plugin or protocol framework. Tests replace calls at that module seam.
- JSON output never contains raw SDK objects.
- Dry runs are non-executing estimates that leave bqutil state unchanged.
- Query preprocessing runs before every dry run or submission. It remains a narrow
  legacy dbt macro adapter, not a general dbt implementation.
- Compare JSON includes cache state and all public query-plan stage evidence. Exact
  numeric deltas are an agent-facing machine consumer schema, not a quality label,
  score, or action gate. An unavailable query plan and its stage metrics remain null.
  An observed empty plan retains an empty list and zero stage metrics.
- Interactive selection isn't supported. Every automation input has an argument,
  flag, configuration value, or actionable error.

## Validation

```bash
mise run check
uv run pytest -q
uv run ruff check bqutil tests
uv build
```

A credentialed live query is an explicit operational smoke test, not a routine test
suite requirement, because it can create jobs and incur charges.
