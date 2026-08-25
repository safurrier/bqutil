# Profile Mining Reference

## Goal

Extract the validation contract a competent maintainer already follows, then
encode it as `hk` profile checks. A profile should tell an agent what to run and
when, while leaving execution in the normal shell loop.

## Source Authority

1. **CI workflows** — merge-blocking truth. Mine `.github/workflows/*`,
   Buildkite config, GitLab CI, or equivalent.
2. **Hooks** — local commit/push truth. Check `.pre-commit-config.yaml`,
   `lefthook.yml`, Husky config, tracked hook installers, and documented local
   pre-push commands.
3. **Agent/context docs** — fastest useful loop. Read root and nested
   `AGENTS.md`, `CLAUDE.md`, `README.md`, and module docs.
4. **Task runners** — available validation surfaces. Inspect `.mise.toml`,
   `justfile`, `Makefile`, `package.json`, `pyproject.toml`, `tox.ini`, and
   language-specific task definitions.
5. **Recent evidence** — what actually worked. Check recent PR descriptions,
   existing validation logs, release docs, or CI debug docs when available.

When sources conflict, report the conflict and prefer CI for merge parity, then
repo AGENTS for the local fast loop. When a repo spans multiple stacks, preserve
that shape in the profile with separate checks per language, CI job, or task
wrapper instead of forcing the repo into one built-in profile.

## Mining Commands

Use targeted reads and searches; do not run heavy checks just to discover them.

```bash
find .github -maxdepth 3 -type f -print 2>/dev/null | sort
find . -maxdepth 3 \( -name '.pre-commit-config.yaml' -o -name 'lefthook.yml' -o -name 'justfile' -o -name 'Makefile' -o -name 'package.json' -o -name 'pyproject.toml' -o -name '.mise.toml' \) -print
rg -n "mise run|uv run|pytest|cargo test|go test|ruff|mypy|ty|pre-commit|lint|typecheck|verify|validate|test" AGENTS.md README.md docs .github .mise.toml pyproject.toml package.json justfile Makefile 2>/dev/null
```

Add ecosystem-specific searches only when the repo needs them.

## Check Taxonomy

Use names that describe the decision the agent must make. Separate iteration
checks from final closeout gates so agents do not chase full readiness after every
edit.

| Check | Use |
|---|---|
| `fast-gate` | Default final pre-handoff validation; should be practical in most sessions, but not the repeated inner-loop check. |
| `focused-tests` | Smallest test path/selector for the touched area; use repeatedly while iterating. |
| `lint` / `format-check` | Static style/format validation. |
| `typecheck` | Static type validation. |
| `ci-parity` | Commands matching merge-blocking CI; may be heavier than fast-gate. |
| `heavy-gate` | Broad confidence before merge, release, or risky runtime changes. |
| `apply` | Applies generated/local config when source changes need deployment. |
| `drift-check` | Detects generated/config drift after template changes. |
| `handoff` | Runs `hk sync && hk ready` for Harness Kit lifecycle state; verifies recorded evidence, not validation execution. |

## Closeout Loop Guardrails

A profile should help agents distinguish three moments:

1. **Iteration**: run focused checks and targeted validation; do not chase final
   `hk ready` after every edit.
2. **Closeout**: when implementation is stable, run required broad checks,
   required reviews, sync/export checks, and `hk ready`.
3. **Post-review fix**: after a small fix, run focused validation and targeted
   follow-up review for changed paths instead of rerunning the whole review stack
   unless the fix changed the main design or behavior.

Guardrails:

- Avoid `required_when = ["*"]` for expensive checks such as full test suites,
  generated-project smokes, or broad CI parity gates. Use explicit meaningful
  source/config/doc globs and notes explaining that the gate is final closeout
  evidence.
- Keep `.ai/hk/**` and other generated handoff packages on handoff/export checks
  rather than forcing full source validation just because the package changed.
- Make advisory/polish reviews suggested (`applies_when`) instead of required,
  bound them to one near-handoff pass plus at most one follow-up, and put that
  limit in `dispatch_hint`.
- Required reviews should be risk-specific. Their instructions should encourage
  broad review near handoff and targeted `hk review add --path ...` follow-up for
  small later fixes.

## TOML Draft Pattern

```toml
name = "<repo-or-module>-root"
title = "<Repo Or Module> Root"
summary = "Validation contract for <repo/module>."
target_hint = "Use --target <repo-or-module-path>."

instructions = "Use this profile for work under <repo/module>. Run validation commands directly and record exact command/result evidence with hk validate --why before handoff. Do not chase final readiness after every edit: use focused checks while iterating, run broad final gates once implementation is stable, and after small review fixes prefer targeted validation/review for changed paths unless behavior or design changed."

[[checks]]
name = "fast-gate"
purpose = "Run the repo's final local validation gate before handoff; not the repeated inner-loop check."
command_template = "<command>"
run_from = "repo-root"
notes = ["Source: <file or CI job>.", "Use focused checks while iterating; run this once implementation is stable and before handoff."]
applies_when = ["src/**", "tests/**"]
# Use required_when only when this check must block readiness for matching paths.
# Avoid required_when = ["*"] for expensive gates unless every path truly needs it.
required_when = ["src/**"]

[[checks]]
name = "focused-tests"
purpose = "Run the smallest focused test that covers the change."
command_template = "<command with placeholder>"
run_from = "repo-root"
required_inputs = ["test_path_or_selector"]
applies_when = ["src/<area>/**", "tests/<area>/**"]

[[reviews]]
name = "domain-review"
purpose = "Review changes from a repo-specific risk perspective."
backend = "fresh-context-subagent"
dispatch_hint = "Run near handoff after implementation stabilizes. For small later fixes, prefer targeted follow-up review for changed paths instead of rerunning the full broad review."
applies_when = ["src/<area>/**"]
# Use required_when only for review perspectives that must be recorded.
required_when = ["src/<area>/critical/**"]

[reviews.instructions]
type = "file"
path = "prompts/domain-review.md"

[[checks]]
name = "handoff"
purpose = "Validate portable workflow evidence and review state."
command_template = "hk sync --target <target> --json && hk ready --target <target> --json"
run_from = "current-directory"
notes = ["This checks recorded evidence; it does not rerun validation."]
```

## Proposal Guardrails

- Label uncertain commands as proposed and cite why they seem appropriate.
- Do not invent repo-specific wrappers that do not exist.
- Do not choose a language built-in profile as authoritative when repo-specific
  CI or task contracts exist.
- For Python/Rust, Python/Node, or other mixed-stack repos, cite the closest
  built-in profile only as a fallback and draft a repo-specific profile when CI
  or task runners define recurring checks for more than one stack.
- Prefer `[reviews.instructions] type = "file"` for non-trivial review instructions; keep TOML concise.
- Use `applies_when` for suggestions and `required_when` only for checks/reviews
  that readiness should require when matching files change. Path rules may be
  repo-root-relative or relative to the selected `--target`; HK reports matched
  paths as repo-root-relative.
- Do not make expensive broad checks or advisory reviews required just because
  they are useful before a PR. Encode them as final closeout guidance with notes
  and bounded dispatch hints unless they must block readiness for specific paths.
- For custom profiles, prefer declaring `profiles_dir = "profiles"` or
  `profiles_dirs = [...]` in `harness.toml` so normal discovery commands load
  them. Use `--profiles-dir <profiles-dir>` only for ad hoc catalogs; lifecycle
  commands resolve user config and do not accept profile flags.
- Do not silently create profiles. Ask before writing the TOML file.
- If the user declines profile creation, continue with the closest built-in
  profile and note the limitation once.
