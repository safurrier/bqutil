---
name: spec-sync
description: >
  Promote slice-local decision notes into durable repo docs. Uses the active
  plan's decision_record to decide between no-op, decision-ledger, or ADR.
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
---

Prepare the repo for `mise run spec-check`.

## Core rule

The active plan stages decisions in `DECISIONS.md`. Durable records are then:

- `decision_record: none` → keep the note slice-local only
- `decision_record: ledger` → append an entry to `docs/explanation/decision-ledger.md`
- `decision_record: adr` → create or update an ADR under `docs/explanation/decisions/`

## Process

1. Read `SPEC.md`, `docs/explanation/architecture.md`, and the active plan's `DECISIONS.md`
2. Check the active plan's `contract_change` and `decision_record`
3. Promote durable changes:
   - update `SPEC.md` if contracts/invariants changed
   - update architecture docs if boundaries or workflows changed
   - append to the decision ledger or author an ADR based on `decision_record`
4. Update the active plan's `Where Reflected` and `Promotion` sections so the
   path from slice-local note to durable doc is obvious

## Rules

- Prefer the decision ledger over ADRs for ordinary slice-level choices
- Use ADRs when a larger invariant, boundary, or long-lived tradeoff changed
- Do not rewrite the whole architecture doc or SPEC; make targeted edits
