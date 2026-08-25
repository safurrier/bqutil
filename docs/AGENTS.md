# Documentation

**When a user corrects you or provides tribal knowledge or gotchas—something you
could not have known from reading the code or your prompt—you MUST document it in
the nearest AGENTS.md before continuing.**

This directory owns durable explanation, decisions, and review references. Current
behavioral obligations belong in `../SPEC.md`; temporary implementation evidence
belongs in the active plan or Harness Kit ledger.

## Commands

- **Validate frontmatter and indexes:** `mise run docs`
- **Full repository gate:** `mise run check`

## Gotchas

- **DO** list every documentation file individually in the index below. **NOT** rely
  only on a directory-level entry. **BECAUSE** deterministic reference validation
  checks file-level discoverability.
- **DO** make every frontmatter index ID match a real second-level heading. **NOT**
  use approximate topic labels. **BECAUSE** indexed navigation resolves exact heading
  identifiers.
- **DO** keep current obligations in `SPEC.md` and explanations here. **NOT** copy
  plan-local evidence into durable docs without a lasting reader need. **BECAUSE**
  each fact should have one canonical owner.

## Related Context

| Path | What's there |
|---|---|
| `README.md` | Documentation reading order |
| `explanation/architecture.md` | Module ownership, execution flows, and invariants |
| `explanation/decision-ledger.md` | Append-only summary of durable decisions |
| `explanation/decisions/0001-stack-choice.md` | Python stack choice decision |
| `reference/review-rubrics/core-quality.md` | Correctness and maintainability review criteria |
| `reference/review-rubrics/docs-info-architecture.md` | Durable documentation review criteria |
| `reference/review-rubrics/performance.md` | Performance evidence criteria |
| `reference/review-rubrics/ui-ux.md` | CLI interaction and clarity criteria |

<!-- generated-by: context-engineering@2.6.3 | last-updated: 2026-08-25 -->
