---
id: bqutil-decision-ledger
title: bqutil Decision Ledger
description: >
  Append-only ledger for durable slice decisions in bqutil.
index:
  - id: ledger
    keywords: [decision-ledger, append-only, slice-history, audit-trail]
  - id: format
    keywords: [entry-format, reflected, evidence, plan]
---

# Decision Ledger

## Ledger

### 2026-08-25 — compare-jobs

- Plan: `.ai/plans/2026-08-25-150538-compare-jobs/`
- Change: Add a noninteractive comparison command with raw query-job summaries and
  exact candidate-minus-baseline deltas.
- Reason: Agents can compare before and after runs without recreating job-plan metrics
  or losing cache and stage evidence.
- Reflected in: `SPEC.md`, `README.md`, and `docs/explanation/architecture.md`.
- Evidence: `.ai/plans/2026-08-25-150538-compare-jobs/artifacts/validation-summary.md`
  and `.ai/plans/2026-08-25-150538-compare-jobs/artifacts/schema-example.json`.

### 2026-08-25 — package-bqutil

- Plan: `.ai/plans/2026-08-25-115713-package-bqutil/`
- Change: Extract the original script into a Git-installable Click package with
  explicit noninteractive inputs, JSON-safe analysis, and a BigQuery dry-run path.
- Reason: Package ownership, isolated tests, and a pinned install make the tool easier
  to validate and roll back without keeping two executable implementations.
- Reflected in: `SPEC.md`, `README.md`, and `docs/explanation/architecture.md`.
- Evidence: `.ai/plans/2026-08-25-115713-package-bqutil/artifacts/validation-summary.md`
  and `.ai/plans/2026-08-25-115713-package-bqutil/artifacts/review-summary.md`.

Append new durable slice decisions here. Don't rewrite prior entries during normal
agent work. Use ADRs under `decisions/` when a decision needs a fuller record.

## Format

Each entry includes:

- date and slice slug
- plan path
- what changed and why
- where the decision appears in current documentation
- supporting evidence
