---
name: plan-sync
description: >
  Bring the active plan up to date before running sync-check. Focuses on META,
  TODOs, learning log coverage, and required slice-local files.
allowed-tools: Read, Edit, Glob, Grep, Bash
---

Prepare the active plan for `mise run plan-check`.

## What "current" means now

The active plan is not just TODOs. It should have:

- current `META.yaml` contract fields
- current `TODO.md`
- at least one learning-log entry once work is in progress
- `VALIDATION.md`, `REVIEW.md`, `DECISIONS.md`
- `artifacts/manifest.yaml`

## Process

1. Find the active plan in `.ai/plans/` (prefer `status: in-progress`)
2. Compare `META.yaml` to current reality:
   - branch matches
   - status matches the actual slice state
   - `contract_change`, `decision_record`, `review_rubrics`, `evidence_required` are filled
3. Tighten `TODO.md` so it matches the work that actually happened
4. Ensure `LEARNING_LOG.md` has timestamped progress notes once implementation started
5. Ensure the required slice-local files exist and are no longer empty placeholders

## Output

Propose or apply targeted updates so `mise run plan-check` can pass.
