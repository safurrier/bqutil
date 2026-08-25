---
id: plan-validation
title: Validation Log
description: Deterministic, writing, package-install, and live BigQuery evidence.
---

# Validation

## Commands

- `mise run check` — format, Ruff, ty, and 30 pytest tests passed.
- `uv build` — source distribution and wheel built.
- Isolated `uv tool install --editable . --force` — version and command help passed.
- Context contracts, frontmatter, references, and AGENTS depth checks passed after
  repairing scaffold-generated indexes.
- Writing checks ran on README, SPEC, and architecture. Remaining findings are exact
  product headings, normative MUST/SHOULD terms, and defined XDG terminology.
- `bqutil query select1.sql --project discord-pada-analytics --dry-run` — passed with
  zero bytes processed.
- `bqutil query select1.sql --project discord-pada-analytics --preview-rows 1` — real
  job completed and returned `validation_value = 1`.
- `bqutil analyze --last --format json` — returned the real completed job and a
  JSON-safe nonempty query plan.
- Focused regression tests prove `query --analyze` leaves one JSON document on stdout
  and dry-run conflicts fail before credentialed client construction.

## Evidence

Artifacts listed in `artifacts/manifest.yaml` summarize review and validation.
