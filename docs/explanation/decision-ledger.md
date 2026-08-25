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

Append-only record for durable slice decisions.

## Entry Format

Each entry should include:

- date + slice slug
- plan path
- what changed
- why
- where reflected
- evidence

## Notes

- Append new entries; do not rewrite history in normal agent flows.
- Use ADRs under `decisions/` when a change needs a fuller record.
