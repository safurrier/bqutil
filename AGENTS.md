# bqutil

A bqutil project

## WHY

<!-- Describe the problem this project solves in 2-3 sentences -->

**Done means**: `mise run check` passes, `mise run sync-check` proves the slice
is fully documented/evidenced/reviewed, and intended behavior is covered by the
appropriate test layer.

Correctness invariants live in [`SPEC.md`](SPEC.md). Durable system design and
decision history live under [`docs/explanation/`](docs/explanation/README.md).

## WHAT

```
bqutil/
├── bqutil/          # Source code
├── tests/                  # Test suite
├── .mise.toml              # Task runner config
├── pyproject.toml          # Python project config
└── README.md
```

Key steering files:
- `AGENTS.md` — this file (steering index)
- `SPEC.md` — correctness envelope (requirements, contracts, invariants)
- `docs/AGENTS.md` — docs routing index
- `docs/explanation/architecture.md` — system description, principles, decisions
- `docs/explanation/decision-ledger.md` — append-only durable decision history
- `docs/reference/review-rubrics/` — reusable review standards
- `.agent/skills/` — vendored workflow helpers

## HOW

```bash
mise run setup      # install tools and dependencies (one-time)
mise run check      # fast quality gate: fmt + lint + typecheck + test  ← before committing
mise run sync-check # plan/spec/evidence/review handoff gate            ← before handing off or pushing
mise run verify     # heavier validation: integration, security, docker  ← before merging
mise run dev        # start local development```

CI calls `mise run ci` (= `check`) and `mise run sync-check`. Pull request CI
uses changed-plan mode so completed plan directories are still validated.
`sync-check` is a handoff completion gate, not a replacement for code/test
validation.

## Stack: python

- Formatter: ruff format (line-length 88)
- Linter: ruff check (E, W, F, I, B, C4, UP, N, S, PTH, RUF)
- Type checker: ty (error-on-warning)
- Tests: pytest with coverage

## Starting Work

```bash
git checkout -b feat/demo-work
mise run plan -- demo-work    # creates .ai/plans/YYYY-MM-DD-HHmmSS-demo-work/
mise run slice-plan -- --task path/to/task.md # renders prompts/planner.md
mise -q run slice-status -- --json # inspect active slice state as JSON
```

`mise run plan` refuses to run on the default branch. Slugs must be lowercase
kebab-case and unique within `.ai/plans/`.

The task scaffolds META.yaml, TODO.md, LEARNING_LOG.md, VALIDATION.md,
REVIEW.md, DECISIONS.md, and `artifacts/manifest.yaml`. Add SPEC.md or
IMPLEMENTATION.md if the work is complex.

See `.ai/plans/AGENTS.md` for the full plan structure and `_example/` for a reference.

## Before Handoff Or Push

1. `mise run check` — must pass
2. Update the active plan: TODO, LEARNING_LOG, DECISIONS, VALIDATION, REVIEW, artifacts
3. Render phase prompts if useful: `mise run slice-implement`, then `mise run slice-review`
4. Use vendored skills if helpful: `slice-workflow`, `/plan-sync`, `/spec-sync`, `/context-engineering update`, `/docs-workflow update`
5. `mise run sync-check` — repo-enforced handoff gate
6. `mise run verify` — when the slice needs heavier validation before merge

The skills above are helpers. The hard contract is the `mise` task surface.

## Skills

Vendored workflow helpers live in `.agent/skills/`. Each `SKILL.md` describes
when to load it and what workflow it encodes. Skills help satisfy the repo
contract, but canonical truth stays in `docs/` and the active plan.

`.claude/skills` is symlinked to `.agent/skills` for Claude Code discovery. Other
harnesses can create `<harness-config>/skills → ../.agent/skills` similarly.

## Further Reading

| Document | Purpose |
|---|---|
| `SPEC.md` | Correctness envelope — requirements, contracts, invariants |
| `.ai/plans/` | Plan directories for units of work (see `.ai/plans/AGENTS.md`) |
| `docs/explanation/architecture.md` | System description, principles, decisions |
| `docs/explanation/decision-ledger.md` | Append-only durable decision trail |
| `docs/reference/review-rubrics/` | Review standards for external review |
| `README.md` | Human-oriented quick start |
