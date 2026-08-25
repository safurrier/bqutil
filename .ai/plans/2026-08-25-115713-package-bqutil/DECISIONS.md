---
id: plan-decisions
title: Decision Notes
description: Slice-local decisions promoted to current documentation.
---

# Decisions — package-bqutil

## What Changed

- Extracted bqutil into a standalone Git-installable Click package.
- Replaced interactive fallback with explicit inputs and actionable errors.
- Added a BigQuery dry-run path and kept one concrete SDK adapter.

## Why

- The package needs reliable automation, isolated tests, and a rollback-capable Git
  pin.
- Interactive prompts and raw SDK objects made the predecessor difficult to invoke
  from scripts and agents.

## Where Reflected

- `SPEC.md`
- `README.md`
- `docs/explanation/architecture.md`
- `docs/explanation/decision-ledger.md`

## Promotion

Promoted to the correctness envelope, architecture explanation, and decision ledger.
