---
id: plan-validation
title: Validation Log
description: Deterministic validation evidence for compare-jobs.
---

# Validation

## Commands

- `uv run pytest tests/test_logic.py tests/test_cli.py -q` — focused comparison,
  operand-failure, and help-contract tests passed.
- `mise run check` — formatting, Ruff, ty, and 47 pytest tests passed.
- `uv build` — source distribution and wheel built.
- Isolated `uv tool install --editable . --force` — root and compare help expose the
  agent workflow and candidate-minus-baseline semantics.
- Context contracts, frontmatter, references, and agent guidance checks passed.
- Source-bound writing checks ran for every changed authored document. README
  readability met the advisory target. Exact headings, normative terms, and technical
  identifiers retain source-bound dispositions.
- `mise run sync-check -- --plan-dir .ai/plans/2026-08-25-150538-compare-jobs` —
  reached the evidence contract, then correctly stopped because this delegated worker
  may not stage the new plan artifacts. The parent must stage them before rerunning.
- A credentialed comparison fetched two existing completed jobs from an approved
  development project. JSON parsing confirmed both raw summaries, exact
  candidate-minus-baseline metrics, zero-baseline null percentages, and unavailable
  candidate metrics. The command submitted no BigQuery work and changed no config.

## Evidence

Artifacts listed in `artifacts/manifest.yaml` summarize schema, validation, writing,
and review evidence.
