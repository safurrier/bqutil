---
id: plan-review
title: Review Log
description: External review record for compare-jobs.
---

# Review — compare-jobs

## Review Context

- Mode: external
- Backend: subagent
- Reviewer: Pi subagents `b82b5acd` (agent-friendly CLI), `25b0ab78` (heuristic authority), and `1e49b0d2` (focused follow-up)

## Rubrics

- core-quality
- docs-info-architecture
- agent-friendly CLI behavior
- heuristic-authority boundary

## Findings

- P1: The root agent workflow used bare job IDs without a project fallback.
- P1: Compare leaked SDK fetch failures instead of naming the failed operand and
  remediation.
- P1: A selected query-plan stage subset dropped timing, spill, and execution-step
  evidence while public docs called it raw.
- P1: Missing query-plan metadata became known zero stage metrics.
- P2: Credential refresh failures bypassed compare's operand-specific error path.
- P3: The decision ledger referenced a non-existent JSON schema artifact.
- P2: Default text output omitted raw baseline and candidate evidence.

## Disposition

- Added `--project PROJECT` to the copyable root workflow.
- Added an operand-specific compare fetch helper that translates
  `GoogleAPICallError` into a `ClickException` with job, project, location, and
  ID/location/permission remediation. Baseline and candidate failure tests confirm no
  traceback reaches callers.
- Preserved every public QueryPlanEntry field as JSON-safe stage evidence and added
  timing, spill, and step fixtures.
- Retained null plan evidence and stage metrics for unavailable plans. Explicit empty
  plans remain empty lists with zero stage metrics.
- The heuristic-authority finding is resolved: the schema retains source evidence and
  computes exact deltas for a named machine consumer. It has no score, label,
  threshold, recommendation, action gate, or nonzero regression exit.
- A fresh focused follow-up verified every repair against code, tests, and docs. It
  returned `NO FINDING`, found no new bug, and marked the change ready to merge.
- The final Codex review found credential errors outside the caught Google API class
  and a stale schema artifact suffix. Compare now catches `GoogleAuthError` with the
  same operand-specific `ClickException`, tests both operands, and links the Markdown
  schema artifact.
- The GitHub review found that default text omitted raw summaries. Compare now defaults
  to JSON, and `--format text` explicitly selects the concise delta-only rendering.
