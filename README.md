# bqutil

A bqutil project

## Quick Start

```bash
# Install dependencies
mise run setup

# Run quality checks
mise run check
mise run sync-check

# Start development
mise run dev```

## Starting New Work

```bash
git checkout -b feat/<slug>
mise run plan -- <slug>
mise run slice-plan -- --task path/to/task.md
mise -q run slice-status -- --json
```

## Task Reference

| Command | Purpose |
|---------|---------|
| `mise run setup` | Install dependencies and prepare the environment |
| `mise run fmt` | Auto-format code |
| `mise run lint` | Run lint checks (non-modifying) |
| `mise run typecheck` | Run static type analysis |
| `mise run test` | Run unit tests |
| `mise run build` | Build artifacts |
| `mise run check` | Fast quality gate (fmt + lint + typecheck + test) |
| `mise run plan-check` | Validate the active plan and metadata |
| `mise run spec-check` | Validate decision promotion and reflected docs |
| `mise run evidence-check` | Validate declared evidence artifacts |
| `mise run review-check` | Validate external review artifacts |
| `mise run sync-check` | Aggregate handoff readiness checks |
| `mise run slice-plan` | Render the planner prompt for the active slice |
| `mise run slice-implement` | Render the implementer prompt for the active slice |
| `mise run slice-review` | Render the reviewer prompt for the active slice |
| `mise run slice-status` | Show active slice state; use `mise -q run slice-status -- --json` for automation |
| `mise run dev` | Start local development || `mise run ci` | CI entrypoint (= check) |
| `mise run plan -- <slug>` | Create a plan directory for a unit of work |
| `mise run verify` | Heavy validation (integration, docker, security) |

## Project Structure

```
bqutil/
├── bqutil/          # Source code
├── tests/                  # Test suite
├── .mise.toml              # Task runner config
├── pyproject.toml          # Python project config
└── README.md
```

## Development

This project uses [mise](https://mise.jdx.dev/) as the task runner. All quality gates
are accessible via `mise run <task>`.

CI calls mise entrypoints: `mise run ci` and `mise run sync-check`.
Pull request CI uses changed-plan mode so completed plan directories are
validated after handoff.
Slice prompts are rendered separately via `mise run slice-*`; slice completion
is enforced via the same `mise run sync-check` handoff gate.
