---
id: plan-spec
title: Task Specification
description: Comparison command requirements and evidence boundaries.
---

# Specification — compare-jobs

## Problem

An agent can inspect jobs individually but cannot reliably compare before and after
runs without reconstructing metric semantics and job locations itself.

## Requirements

### MUST

- Compare baseline and candidate query jobs without interactive prompts.
- Preserve raw JSON-safe summaries and raw query-plan stages for both jobs.
- Compute only exact candidate-minus-baseline metric deltas.
- Keep unavailable metrics and zero-baseline percentage changes null.
- Never emit an optimization label, score, recommendation, threshold, or action gate.

### SHOULD

- Include concise text output and progressive command help for human and agent use.
- Accept shared or per-job project and location fallbacks.

## Constraints

Comparison uses existing job metadata and does not submit SQL or create a BigQuery
job in routine validation.
