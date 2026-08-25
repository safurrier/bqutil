---
id: plan-learning-log
title: Learning Log
description: Implementation adaptations and verified surprises from the extraction.
---

# Learning Log

## 2026-08-25

- The installed Harness Scaffold wheel omitted its template files. Running from a
  source checkout generated the repository, but the generated project also omitted
  `.mise/tasks/` and `scripts/lib.py`; those task-contract files were restored from
  the same reviewed source checkout.
- The first extraction leaked BigQuery query-plan objects into JSON and retained
  no-op options. Specialist reviews found both before live validation.
- A real dry run and `SELECT 1 AS validation_value` completed in
  `discord-pada-analytics`; `analyze --last --format json` then serialized the real
  nonempty query plan successfully.
