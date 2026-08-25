# Harness Kit Workflow Reference

Use this reference when a session is not already familiar with Harness Kit (`hk`)
or when adding `hk` guidance to a user-level `AGENTS.md`.

## Baseline Loop

Use Harness Kit for meaningful code changes unless stronger repo-specific
instructions supersede it.

Start by resolving the repo/module workflow:

```bash
hk profile resolve --target <repo-or-module> --json
```

Use the repo or module that owns the work as `--target`. During implementation,
use focused profile checks and targeted validation; do not chase final readiness
after every edit. Once the implementation is stable, run required closeout gates,
reviews, sync/export checks, and `hk ready`. Then run discovery and lifecycle
commands explicitly:

```bash
hk checks --target <repo-or-module> --changed --json
hk start <slug> --plan 'Adopted implementation intent' --target <repo-or-module> --json
hk status --target <repo-or-module> --json
hk validate --check <check-name> --why 'Why this proves the change' -- <native command>
hk review prompt <review-name> --target <repo-or-module>
hk review add --review <review-name> ...
hk sync --target <repo-or-module> --json
hk ready --target <repo-or-module> --json
```

For meaningful PR-sized work in HK-native repos, generate a compact review/handoff
package near handoff time:

```bash
WORK_ID=$(hk status --target <repo-or-module> --json | python3 -c 'import json,sys; print(json.load(sys.stdin)["active_work"])')
hk export --format handoff-dir --output ".ai/hk/$WORK_ID" --target <repo-or-module>
hk export --format handoff-dir --output ".ai/hk/$WORK_ID" --target <repo-or-module> --check
```

The default export shape is intentionally compact:

```text
.ai/hk/<work-id>/
  README.md
  meta.json
  artifacts/
    README.md
```

The HK ledger is canonical. Generated Markdown is a review/handoff projection,
not a second ledger and not something to hand-edit.

Only pass `--profiles-dir` for an ad hoc catalog not already declared by user
config. User-level `harness.toml` can declare `profiles_dir = "profiles"` or
`profiles_dirs = [...]` so standalone profile files load by default.

## Rules

- `hk` manages planning and handoff state. It does **not** run validation commands.
- Run profile-suggested validation commands directly in the shell.
- Record exact command/result evidence with `hk validate --why`; use
  `hk validate --check NAME --why` when satisfying a named profile check.
- Use `hk profile resolve` first to find the configured profile for the target.
- Use `hk checks --changed` to see path-based check/review suggestions.
- Keep profile flags on discovery commands (`hk profile`, `hk checks`, repo-scope
  `hk instructions`). Lifecycle commands do not accept `--profile` or
  `--profiles-dir` unless the command help explicitly says so.
- Path rules in `applies_when` / `required_when` can be repo-root-relative or
  relative to the selected `--target`; HK reports matched paths as repo-root-relative.
- Do not commit `.harness-local/` or raw agent-local state. Commit generated
  `.ai/hk/<work-id>/` exports only when the repo/user wants durable review artifacts.
- For repos that still have committed scaffold/task-contract infrastructure and
  repo-local plans are expected, follow that stronger repo-specific workflow until
  the repo migrates.

## Profile Selection

1. Run:
   ```bash
   hk profile resolve --target <repo-or-module> --json
   ```
2. Inspect suggestions when useful:
   ```bash
   hk checks --target <repo-or-module> --changed --json
   hk profile show <resolved-profile> --json
   ```
3. Tell the user once which profile was resolved and why when it affects the
   validation/review plan.

Built-in language profiles are fallbacks, not authoritative contracts, when a
repo has recurring CI or task-runner validation.

## Custom Profiles

If no exact module/repo profile exists and the repo has a recurring validation
contract, ask the user whether to create one. Do not silently create profiles.

```bash
hk profile create <repo-or-module-name> \
  --target <repo-or-module-path> \
  --preset <generic|python|go|rust|rust-mise> \
  --profiles-dir ~/.config/harness-toolkit/profiles
```

After creating a profile template, have the user confirm or edit TODOs and
command templates before treating it as authoritative.

If a good profile does not exist, use this skill to mine CI workflows, hooks,
task runners, repo docs, and recent validation evidence before proposing TOML.

## User-Level AGENTS.md Snippet

Append a compact version like this to a user-level `AGENTS.md` when the user
wants agents to default to Harness Kit across arbitrary repos:

````markdown
## Harness Kit

For meaningful code changes, use Harness Kit (`hk`) for planning, validation
evidence, review, sync, and handoff unless stronger repo-specific instructions
supersede it.

Start by resolving the repo/module workflow:

```bash
hk profile resolve --target . --json
```

Use the repo or module that owns the work as `--target`. Profile flags are only
for discovery commands such as `hk profile`, `hk checks`, and repo-scope
`hk instructions`; do not pass `--profile` or `--profiles-dir` to lifecycle
commands unless that command's help shows those options. Then start work with
`hk start <slug> --plan "..."`, record validation with `hk validate --why`, and
follow `hk status --target .`. Use `hk summary --target .` when a human-readable
readiness digest is useful.

Rules to remember:

- `hk` manages planning/handoff state; it does not run validation commands.
- Run validation directly and record exact command/result evidence with `hk validate --why`.
- Use `hk checks --changed` to see path-based check/review suggestions when profiles define them.
- Treat broad profile gates as final closeout evidence unless the profile says they are cheap inner-loop checks; use focused checks while iterating.
- After small review fixes, prefer targeted validation and `hk review add --path ...` coverage for changed paths instead of rerunning the full review stack.
- Keep profile flags on discovery commands (`hk profile`, `hk checks`, repo-scope `hk instructions`); lifecycle commands do not accept `--profile` or `--profiles-dir`.
- Path rules in `applies_when` / `required_when` can be repo-root-relative or relative to the selected `--target`.
- If no good profile exists, use the profile-authoring workflow to propose one;
  do not create profiles silently.
````
