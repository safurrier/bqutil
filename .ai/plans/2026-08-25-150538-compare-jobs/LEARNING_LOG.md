---
id: plan-learning-log
title: Learning Log
description: Implementation discoveries for compare-jobs.
---

# Learning Log

## 2026-08-25

- BigQuery job locations must travel with each comparison operand because jobs can
  reside outside default multi-regions.
- Stage sums are not query bytes or unique rows. The public metric names retain that
  distinction and preserve null when any stage source metric is unavailable.
- Exact deltas are useful machine evidence, but an optimized/regressed label would
  collapse context that the caller needs for the next SQL decision.
- An unavailable query plan differs from an observed empty plan. The comparison now
  retains null evidence and stage metrics for the former, rather than inventing zeroes.
- Public QueryPlanEntry fields beyond the common slot and shuffle metrics can explain
  optimization behavior. The comparison preserves them, including timing, spill, and
  execution-step evidence.
