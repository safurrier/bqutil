---
name: hk-config-authoring
description: Router skill for Harness Kit config authoring and maintenance. Use when a user asks to create, audit, update, or repair HK profiles, system maps, target bindings, or user-level harness.toml config. Delegates to profile and system-map authoring skills instead of duplicating their logic.
allowed-tools: Read, Grep, Glob, Bash, Write
---

# HK Config Authoring Router

Use this skill when the request is about Harness Kit configuration rather than a normal HK lifecycle work item.

This is a router. It decides which specialized workflow to run and keeps profile/system-map work coordinated. It does **not** replace the specialized skills.

## Core boundary

- HK config diagnostics inspect, validate, audit, and explain deterministic config joins.
- `harness-kit-profile-authoring` owns profile checks/reviews/requiredness guidance.
- `hk-system-map-author` owns component/invariant/read-before-editing/check-label maps.
- Humans or explicit agent instructions approve writes.
- Do not edit deployed runtime `~/.config` files directly when a managed config source exists.

## Route the request

Ask or infer:

1. Is this **create/author** or **audit/update**?
2. Is the target problem about:
   - validation/review policy? → `harness-kit-profile-authoring`
   - components/invariants/system-map labels? → `hk-system-map-author`
   - target binding/profile/system_map wiring? → this router plus both skills as needed
   - all of the above? → paired flow
3. Where should changes live?
   - repo-local `.harness/`
   - user-managed `config/harness-toolkit/`
   - generated template skill/config
   - proposal only / temp file

## Start with deterministic diagnostics

When a target exists, run what is available:

```bash
hk profile resolve --target <repo-or-module> --json
hk brief --target <repo-or-module> --json
hk checks --target <repo-or-module> --changed --json
hk config inspect --target <repo-or-module> --json
hk config validate --target <repo-or-module> --json
hk config audit --target <repo-or-module> --json
```

If `hk config ...` commands are unavailable, use the profile/brief/checks commands and direct TOML reads.

## Paired create flow

1. Resolve target root and desired config location.
2. Use `harness-kit-profile-authoring` to draft the profile first, because system maps reference profile check labels.
3. Use `hk-system-map-author` to draft the map against that profile.
4. Propose the target binding:

```toml
[[targets]]
name = "<target-name>"
path = "<repo-or-module-path>"
profile = "<profile-name>"
system_map = "system-maps/<target-name>.toml"
```

5. Validate the proposed joins with `hk config validate` when available.
6. Ask before writing.

## Paired audit/update flow

1. Run deterministic diagnostics.
2. Split findings by owner:
   - profile issues: stale commands, prompt files, requiredness, review scope
   - system-map issues: missing paths/docs/evidence, unresolved labels (system-map
     `validation_checks` referencing profile check names that no longer exist — fix
     direction is to remove or correct the label in the map, not to add a new profile
     check to match it), noisy components, stale invariants
   - binding issues: missing target path, missing profile, missing map, surprising override
3. Delegate profile findings to `harness-kit-profile-authoring` audit/update mode.
4. Delegate system-map findings to `hk-system-map-author` audit/update mode.
5. Produce a small combined patch plan. Avoid broad rewrites unless the config is structurally obsolete.
6. Ask before writing and list every file to change.

## Output format

```markdown
## HK config authoring route

Mode: create | audit/update
Target: `<target>`
Config location: repo-local | user-managed | template | proposal-only

### Diagnostics used

- `<command>`: summary

### Delegation

- Profile work: `harness-kit-profile-authoring` because ...
- System-map work: `hk-system-map-author` because ...

### Proposed changes

1. `<file>` — <reason>
2. `<file>` — <reason>

Proceed with these writes?
```

## Guardrails

- Do not promote generative profile/system-map drafting to top-level HK lifecycle commands.
- Do not let system-map labels become readiness policy; profiles own requiredness.
- Do not run native validation commands through `hk config`; use lifecycle `hk validate -- <command>` for evidence.
- Keep deterministic diagnostics separate from judgment-heavy proposals.
