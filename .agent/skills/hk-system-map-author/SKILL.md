---
name: hk-system-map-author
description: This skill creates, updates, audits, and validates Harness Kit system maps, including repo-local .harness/system.toml files and target-level user-managed system_map overlays. Use when authoring agent-facing component/invariant maps, connecting touched paths to relevant HK profile check labels, dogfooding system-map candidates, or preparing Harness Kit CLI integration trials.
---

# hk-system-map-author

Author Harness Kit system maps: compact, deterministic path-to-component/invariant maps for agents. Maps may live repo-locally at `.harness/system.toml` or as user-managed target-level overlays referenced by `harness.toml` with `system_map = "..."`. Treat the file as a narrow preflight contract for agents, not as architecture documentation.

Core distinction:

- `AGENTS.md` tells agents how to work in a repo.
- HK profiles tell agents how and when to validate work.
- System maps tell agents which component/invariant a path touches and which existing check labels are relevant.

## Use cases

- Create the first repo-local `.harness/system.toml` or target-level user-managed system map for a repo or scoped module.
- Audit an existing system map for schema, path, invariant, and check-label quality.
- Refresh a component or invariant after a codebase change.
- Dogfood candidate maps before adding or changing Harness Kit CLI integration.

## Non-negotiable principles

1. Keep the canonical source as TOML, either repo-local `.harness/system.toml` or an explicit target-level map referenced from `harness.toml`.
2. Paths inside maps are repo-root-relative even when the map file lives outside the repo.
3. Keep the map compact. Reject architecture prose disguised as config.
4. Treat invariants as must-preserve constraints unless explicitly superseded.
5. Reference check labels only. Do not put command templates or requiredness in the system map.
6. Keep profiles authoritative for commands, required/suggested semantics, and readiness.
7. Mark system-map labels as relevant/advisory, not required checks.
8. Prefer observed evidence from code/docs/profiles. Mark uncertainty in comments or leave fields out rather than inventing claims.
9. Validate mechanically after creation or edits.

## Reference loading

Load references as needed:

- `references/system-toml-schema.md` — canonical schema, JSON contract, and validation findings.
- `references/authoring-rubric.md` — quality rubric and anti-patterns.
- `references/hk-integration.md` — how system maps relate to HK brief/checks/profiles/readiness.
- `references/trial-matrix.md` — dogfood trial set and promotion gates.

## Mode selection

Choose one mode first:

1. **Create/author** — create a first system map or a new target-level overlay.
2. **Audit/update** — inspect an existing map for stale references, unresolved labels, noisy components, or invariant drift.
3. **Paired profile/system-map work** — when validation policy and component/invariant context both need updates, pair this skill with `harness-kit-profile-authoring` or use the `hk-config-authoring` router skill when available.

Prefer deterministic HK diagnostics when available:

```bash
hk config inspect --target <repo-or-module> --json
hk config validate --target <repo-or-module> --json
hk config explain --target <repo-or-module> --changed --json
hk config audit --target <repo-or-module> --json
```

Use these diagnostics as evidence, not an oracle. They validate joins and explain matches; they do not infer architecture truth.

## Workflow: create or update a map

1. Determine the target repo root and map location:
   - repo-local: `<repo-root>/.harness/system.toml`;
   - target-level overlay: a user-managed map referenced by `harness.toml` with `system_map = "..."`.
2. Read existing HK surfaces:
   - `harness.toml`, `.harness/harness.toml`, `.harness/profiles/*.toml`, or user-provided profile files;
   - `AGENTS.md`, README, docs/architecture, ADRs;
   - source entrypoints, tests, configs, and changed paths.
3. Select only components with real edit-routing value:
   - distinct responsibility boundary;
   - state/data/artifact/protocol/lifecycle ownership;
   - invariant future edits could violate;
   - focused validation check or profile review label.
4. Write small component entries with concrete paths, docs, invariants, relations, and relevant check labels.
5. Avoid command templates, setup instructions, generic gotchas, historical narrative, and directory tours.
6. For high-risk invariants, suggest a profile-owned required review/check rather than embedding requiredness in the system map.
7. Run the bundled validator:

```bash
python <skill-dir>/scripts/validate_system_toml.py --repo <repo-root>
```

8. If a profile file is available, validate check-label linkage:

```bash
python <skill-dir>/scripts/validate_system_toml.py --repo <repo-root> --profile <profile.toml>
```

9. When available, run `hk config validate --target <target> --json` and `hk config explain --target <target> --path <representative-path> --json` to verify the map/profile joins.
10. Report validation findings and human review points separately. Structural validation does not prove architecture truth.

## Invariant conflict protocol

When a user request, plan, or diff contradicts a surfaced invariant:

1. State the invariant and the requested change.
2. Stop and ask whether the invariant is intentionally superseded unless the user has already made that explicit.
3. If superseded, record or recommend a loud invariant decision with `hk decide --kind invariant-supersession`, including invariant id, previous invariant, reason, replacement or removal rationale, and docs/system-map paths.
4. Update `.harness/system.toml`, related docs, or tests in the same change when practical.
5. If not superseded, adjust implementation and tests to preserve the invariant.
6. If the invariant is high-risk, recommend a profile-owned required review/check for that path.

Do not silently implement around an invariant and only mention it at the end. The supersession must appear in HK status, handoff/PR source material, review prompts, and commit message guidance.

## Workflow: audit

Default to read-only. Start with `hk config inspect/validate/audit` when available, then check:

- parseability and `version = 1`;
- unique kebab-case component ids;
- unique invariant ids within each component;
- relation endpoints reference existing components;
- referenced paths/docs/evidence exist or are intentional globs;
- check labels are non-empty and resolve to profile checks when a profile is provided;
  (unresolved labels are **advisory warnings, not readiness blockers** — the fix is to
  remove or update the stale label in the map, never to add a matching check to the
  profile just to satisfy the reference; labels are advisory/relevant pointers only)
- no command templates or requiredness semantics are present;
- fields are concise enough to be a narrow contract.

Use `--json` for structured output and `--strict` to fail on warnings.

## Workflow: dogfood candidate maps

Use temp repos/copies. Do not commit maps into real repos until the user approves.

1. Generate maps for at least `foreman` and `harness-toolkit` before HK implementation.
2. Validate each map structurally.
3. Query representative paths manually or with a matcher once available.
4. Judge whether the map changes edit routing or validation choice.
5. Kill or revise the concept if output is obvious, noisy, or prose-heavy.

Promotion gate before HK code changes:

- `foreman` map validates and has expected matches for at least three representative changed paths.
- `harness-toolkit` map validates and references real profile labels or records unresolved labels as warnings.
- Both maps stay compact and do not read like architecture docs in TOML.
