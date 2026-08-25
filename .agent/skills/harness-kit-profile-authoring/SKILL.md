---
name: harness-kit-profile-authoring
description: Mine repository validation contracts and propose or audit Harness Kit hk profiles. Use when choosing an hk profile, when no exact repo/module profile exists, when a user asks to create or update a custom profile, or when inspecting CI, hooks, mise, package scripts, repo docs, or HK config diagnostics to draft profile checks/reviews.
allowed-tools: Read, Grep, Glob, Bash, Write
---

# Harness Kit Profile Authoring

Use this skill to decide whether an existing `hk` profile is good enough and, if
not, to propose a custom profile or targeted profile update for user approval.

Core boundary:

- HK profiles tell agents which native commands and independent reviews matter.
- HK config diagnostics can inspect, validate, audit, and explain deterministic joins.
- Skills propose create/update patches when judgment is required.
- Do **not** install or overwrite profile TOML silently.

## Mode selection

Choose one mode first:

1. **Create/author** — no exact repo/module profile exists, or the user asks for
   first-time HK profile adoption.
2. **Audit/update** — a profile already exists and the user asks whether it is
   stale, noisy, incomplete, over-broad, or should be updated.
3. **Pair with system map** — the request is about components, invariants,
   `system_map`, or check labels. Use this skill for profile policy and pair it
   with `hk-system-map-author` for component/invariant mapping.

If the user asks broadly for “HK config authoring,” prefer the `hk-config-authoring`
router skill when available.

## Deterministic HK diagnostics

Prefer deterministic HK facts before mining by hand:

```bash
hk profile resolve --target <repo-or-module> --json
hk checks --target <repo-or-module> --changed --json
hk brief --target <repo-or-module> --json
```

When available, also use:

```bash
hk config inspect --target <repo-or-module> --json
hk config validate --target <repo-or-module> --json
hk config explain --target <repo-or-module> --changed --json
hk config audit --target <repo-or-module> --json
```

Treat these diagnostics as evidence, not as an oracle. They explain existing
config and deterministic drift; they do not infer the correct validation policy.
Still inspect CI, task runners, docs, and repo conventions directly.

## Create/author workflow

1. Discover available profiles. Start with default config; only pass
   `--profiles-dir` for an ad hoc catalog that is not already declared by
   `harness.toml`:
   ```bash
   hk profile list --target <repo-or-module> --json
   hk profile resolve --target <repo-or-module> --json
   ```
2. Choose the closest profile by priority:
   - exact target/module profile
   - repo-specific profile
   - stack/task-runner profile
   - `generic`
3. If there is no exact repo/module profile and the repo has recurring CI or
   task-runner validation, treat built-ins as fallbacks and mine a custom
   profile proposal. See [profile-mining.md](references/profile-mining.md).
4. Draft profile TOML in the response or a temp file. Do **not** install it
   silently.
5. Ask the user to confirm, edit, or reject the profile.
6. Before writing, check whether the destination TOML already exists. Ask for
   explicit overwrite approval or use `hk profile create`, which refuses
   overwrites unless `--force` is passed.
7. Only after confirmation, write to the explicit catalog chosen by the user.
   If dots manages the user's HK config, write to the dots source tree under
   `config/harness-toolkit/profiles/`, not deployed `~/.config/...`, unless the
   user explicitly requests a runtime-only experiment.

## Audit/update workflow

Default to read-only.

1. Resolve the target and active profile:
   ```bash
   hk profile resolve --target <repo-or-module> --json
   hk profile show <profile> --json
   hk config inspect --target <repo-or-module> --json  # if available
   hk config validate --target <repo-or-module> --json # if available
   hk config audit --target <repo-or-module> --json    # if available
   ```
2. Compare deterministic diagnostics with repo truth:
   - CI workflows and pipeline files
   - pre-commit/pre-push/lefthook configs
   - `AGENTS.md` / `CLAUDE.md`
   - task runners (`mise`, `just`, `make`, `npm`, `pnpm`, `uv`, etc.)
   - docs, recent PR notes, and existing HK validation evidence when useful
3. Report focused findings:
   - stale or missing command templates
   - missing final gate or missing focused iteration check
   - missing/broken review prompt files
   - required checks that are too broad or expensive for every path
   - advisory reviews that are unbounded or accidentally readiness-blocking
   - generated handoff/export paths triggering source validation too broadly
   - system-map labels that do not resolve to profile check names
     → fix direction: a stale map label is a **system-map finding**, not a profile gap. Do
       not propose adding a new profile check to satisfy a stale map reference. Report the
       finding and escalate it to `hk-system-map-author` to remove or correct the label
       in the map.
4. Propose the smallest safe patch. Do **not** rewrite the whole profile unless
   the profile is structurally obsolete.
5. Ask before applying. If applying to mirrored skills/config, list every file
   that will change.

## Profile Mining Sources

Treat sources by authority:

1. CI workflows are merge-blocking truth.
2. Pre-commit, pre-push, lefthook, and other hook configs are local commit/push truth.
3. Repo `AGENTS.md` / `CLAUDE.md` usually identifies the fastest useful agent loop.
4. Task runners (`mise`, `just`, `make`, `npm`, `uv`) expose validation surfaces.
5. Docs and recent PR notes reveal heavier, apply, deploy, or release checks.

Read [profile-mining.md](references/profile-mining.md) before drafting anything
non-trivial.

## Drafting Rules

- Keep `hk` as planning/handoff state only. Profiles describe checks; they do
  not make `hk` run validation.
- Use concrete command templates copied from the repo or clearly marked as
  proposed.
- Include at least one fast gate, one focused-test pattern when available, and a
  handoff check.
- Classify checks by lifecycle role: focused checks are for iteration, broad
  gates are for final closeout, CI/heavy checks are for parity or risky paths,
  and handoff checks validate HK/export state rather than source behavior.
- Add heavy/CI parity checks as optional checks with notes explaining when to run
  them.
- Avoid `required_when = ["*"]` for expensive broad gates unless the command is
  genuinely cheap and must block every changed path. Prefer explicit meaningful
  source/config/doc path globs, and let `.ai/hk/**` be covered by handoff/export
  checks instead of full source validation.
- Prefer repo-native wrappers (`mise run check`, `mise run lint`) over expanding
  them unless CI directly uses raw commands.
- For mixed-language repos, keep separate language or CI-job checks instead of
  collapsing everything into a single built-in language profile.
- Use stable profile names such as `<repo>-root` or `<repo>-<module>`.
- Do not write profile files without user approval.
- `applies_when` and `required_when` may use repo-root-relative paths or paths
  relative to the chosen `--target`; HK reports matched paths as repo-root-relative.
- Use `required_when` only for checks/reviews that should block readiness for
  matching paths. Use `applies_when` for suggestions and advisory reviews.
- Write timing guidance into profile `instructions` and review `dispatch_hint`s:
  do not chase final readiness after every edit; use focused checks while
  iterating; run broad final gates once implementation is stable; after small
  review fixes, prefer targeted validation/review for changed paths instead of
  rerunning the full review stack unless behavior or design changed.
- Bound advisory reviews. A polish/readability review should run near handoff,
  at most one follow-up pass unless the user asks for more, and should not become
  an implicit readiness blocker.
- Do not overwrite an existing profile unless the user explicitly approves the
  overwrite after seeing the existing path.

## Output: create/author

````markdown
## Profile recommendation

Chosen existing profile: `<profile>` / none
Reason: <one sentence>

## Mined validation contract

- Fast gate: `<command>` from <source>
- Focused tests: `<command>` from <source>
- CI parity: `<command>` from <source>
- Heavy/apply checks: `<command>` from <source>

## Proposed profile

```toml
...
```

Write this profile to `<path>`?
````

## Output: audit/update

```markdown
## Profile audit

Profile: `<profile>`
Target: `<target>`
Sources checked: <commands/files>

### Findings

| Severity | Finding | Evidence | Proposed fix |
|---|---|---|---|
| warning | ... | ... | ... |

### Proposed patch

<summary or diff>

Apply this patch to `<path>`?
```

## References

- [harness-kit-workflow.md](references/harness-kit-workflow.md) — baseline `hk`
  loop, profile selection, custom profile rules, and user-level `AGENTS.md`
  snippet.
- [profile-mining.md](references/profile-mining.md) — source authority, mining
  commands, and check taxonomy.
- [examples.md](references/examples.md) — generic examples for a scaffolded repo,
  a Rust mise repo, and a dotfiles repo.
