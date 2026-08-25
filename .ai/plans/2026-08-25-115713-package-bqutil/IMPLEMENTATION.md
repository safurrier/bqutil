---
id: plan-implementation
title: Implementation Plan
description: Compatibility-first extraction plan for the standalone bqutil package.
---

# Implementation — package-bqutil

## Approach

Preserve the predecessor command and config interfaces while moving SDK objects and
side effects behind cohesive modules. Keep Click as the ingress seam, return JSON
primitives from analysis, and make credentialed execution explicit and recoverable.

## Steps

1. Add characterization tests with fake BigQuery jobs and clients.
2. Extract configuration, Google Cloud access, query execution, and analysis modules.
3. Add dry-run, deterministic output, bounded previews, and actionable errors.
4. Rewrite durable docs around the verified public interface.
5. Validate locally, through an isolated install, and with an approved live query.
