---
id: plan-decisions
title: Decision Notes
description: Comparison schema and authority-boundary decisions.
---

# Decisions — compare-jobs

## What Changed

- Added a noninteractive comparison command with raw job summaries and exact numeric
  deltas.
- Added project and location precedence for independently resolved job references.
- Preserved every public query-plan-stage field and distinguish unavailable plans from
  observed empty plans.
- Added operand-specific, actionable errors for BigQuery job fetch failures.

## Why

- Agents need comparable evidence without reading SDK objects or manually recreating
  job-plan aggregates.
- A derived optimization verdict would hide query-specific context and wrongly claim
  authority over an agent decision.
- An agent needs timing, spill, and execution-step evidence that a selected stage subset
  would discard. Missing plan metadata must remain distinguishable from an empty plan.

## Where Reflected

- `SPEC.md`
- `README.md`
- `docs/explanation/architecture.md`
- `AGENTS.md`
- `.ai/plans/2026-08-25-150538-compare-jobs/artifacts/review-summary.md`

## Promotion

Promote the public schema and authority boundary to current contracts and architecture
docs. The heuristic-authority decision is explicit: exact machine metrics plus raw job
summaries serve a named agent consumer, retain source evidence, and control no action.
