---
id: plan-implementation
title: Implementation Plan
description: Exact job comparison without optimization verdicts.
---

# Implementation — compare-jobs

## Approach

Keep Click responsible for argument parsing and adapter calls. Place comparison shape,
raw job summaries, metric aggregation, and candidate-minus-baseline arithmetic in
`bqutil.analysis`. The schema retains raw evidence and uses null for unavailable
values; it never converts evidence into an optimization verdict.

## Steps

1. Characterize helper and CLI behavior with fake query jobs.
2. Add exact summaries, null-preserving metrics, and text/JSON rendering.
3. Document precedence, unit semantics, and agent workflow.
4. Validate with the scaffold gate, source checks, isolated install, and review.
