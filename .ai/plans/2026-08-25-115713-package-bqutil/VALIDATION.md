---
id: plan-validation
title: Validation Log
description: Deterministic, writing, package-install, and live BigQuery evidence.
---

# Validation

## Commands

- `mise run check` — format, Ruff, ty, and 36 pytest tests passed.
- `uv build` — source distribution and wheel built.
- Isolated `uv tool install --editable . --force` — version and command help passed.
- Context contracts, frontmatter, references, and AGENTS depth checks passed after
  repairing scaffold-generated indexes.
- Writing checks ran on README, SPEC, and architecture. Remaining findings are exact
  product headings, normative MUST/SHOULD terms, and defined XDG terminology.
- `bqutil query select1.sql --project <approved-development-project> --dry-run` —
  passed with zero bytes processed.
- `bqutil query select1.sql --project <approved-development-project> --preview-rows 1`
  — real job completed and returned `validation_value = 1`.
- `bqutil analyze --last --format json` — returned the real completed job and a
  JSON-safe nonempty query plan.
- Focused regression tests prove `query --analyze` leaves one JSON document on stdout
  and dry-run conflicts fail before credentialed client construction.
- The GitHub repair tests prove explicit and saved BigQuery locations reach job
  lookups, old configs normalize the missing location key, project-qualified IDs still
  work, and date-only or whitespace-form macros are preprocessed before submission.
- A final credentialed `SELECT 1` saved `last_job_location = "US"`, and
  `analyze --last --format json` retrieved the completed job through that location.

## Evidence

Artifacts listed in `artifacts/manifest.yaml` summarize review and validation.
