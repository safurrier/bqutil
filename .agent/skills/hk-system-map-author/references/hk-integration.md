# HK integration rules

System maps are additive advisory context for Harness Kit.

## Ownership split

Profiles own:

- check and review names;
- command templates;
- `applies_when` and `required_when`;
- profile instructions;
- readiness semantics.

System maps own:

- components;
- must-preserve invariants;
- relations;
- read-before-editing references;
- relevant check labels.

## Normal agent loop

Do not introduce a new required command for normal use. Surface the map through existing commands:

```bash
hk brief --target . --json
hk checks --target . --changed --json
hk status --target . --json
```

V1 should only integrate `brief` and `checks`.

## `hk brief`

`brief` discovers whether a repo has a system contract:

```json
"system_map": {
  "path": ".harness/system.toml",
  "version": 1,
  "status": "valid",
  "components": 4,
  "invariants": 9,
  "warnings_count": 0,
  "errors_count": 0,
  "label_resolution": "skipped"
}
```

No map should be `null`. Invalid maps should be summarized, not crash ordinary brief.

## `hk checks --changed`

`checks` is the main integration point. It should add concise `system_context` for touched components and invariants.

Text output must make invariant semantics strong:

```text
System invariants for changed paths:
Policy: must preserve surfaced invariants unless the user explicitly supersedes them.
- app-state matched src/app/reducer.rs.
  Must preserve app-state.reducer-owns-mutation: UI rendering observes state but does not mutate app state directly.
  Relevant check labels: runtime-dashboard
If the requested change contradicts an invariant, stop and resolve the conflict: confirm supersession with the user, record a decision, and update the system map/docs or run the required invariant review.
```

Machine output must make both facts explicit:

- `advisory = true` so readiness does not consume system maps directly;
- `invariant_policy = "must_preserve_unless_superseded"`;
- `conflict_protocol = "stop_confirm_record_decision"`;
- `relevant_check_labels`, not `required_checks`;
- `required_by_profile` computed only from selected profile data.

## Readiness safety

V1 readiness must not import or consume `system_map`. A system-map label can appear as required only when the selected profile already requires that check through `required_when`.

## Debug commands

Defer these until `brief` and `checks` dogfood well:

```bash
hk system validate --target .
hk system path src/app/reducer.rs --target . --json
hk system preflight --changed --target . --json
hk system component app-state --target . --json
```

These commands are for authoring/debugging, not the normal lifecycle.
