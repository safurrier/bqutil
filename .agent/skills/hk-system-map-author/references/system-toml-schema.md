# system.toml schema

## Contents

- [Minimal example](#minimal-example)
- [Required fields](#required-fields)
- [Hard boundaries](#hard-boundaries)
- [Public HK JSON contract](#public-hk-json-contract)
- [Validation findings](#validation-findings)

Canonical v1 path:

```text
<repo-root>/.harness/system.toml
```

V1 uses repo-root-relative paths only. Do not create nested system maps until Harness Kit dogfood proves they are needed.

## Minimal example

```toml
version = 1

[system]
name = "foreman"
summary = "Rust TUI for monitoring and controlling agent sessions."

[[components]]
id = "app-state"
title = "App state and reducer"
kind = "state-machine"
paths = ["src/app/state.rs", "src/app/reducer.rs"]
read_before_editing = ["docs/architecture.md"]
validation_checks = ["runtime-dashboard"]

[[components.invariants]]
id = "reducer-owns-mutation"
statement = "UI rendering observes state but does not mutate app state directly."
evidence = ["src/app/reducer.rs", "src/ui/render.rs"]
validation_checks = ["runtime-dashboard"]

[[relations]]
from = "ui-rendering"
to = "app-state"
kind = "observes"
rule = "UI observes app state and emits actions; reducer owns mutation."
```

## Required fields

Top level:

- `version = 1`
- `[system].name`
- `[system].summary`
- `[[components]]` with at least one component

Component fields:

- `id` — globally unique kebab-case id
- `title` — short human title
- `kind` — concise freeform category, e.g. `state-machine`, `cli`, `validation`, `data-model`
- `paths` — non-empty repo-root-relative paths or globs

Optional component fields:

- `read_before_editing` — repo-root-relative docs/source files worth reading first
- `validation_checks` — relevant HK profile check labels, not commands and not requiredness
- `invariants` — nested `[[components.invariants]]`

Invariant fields:

- `id` — unique within component; machine id is `<component_id>.<invariant_id>`
- `statement` — short invariant statement
- `evidence` — paths/globs proving or exercising the invariant
- `validation_checks` — relevant HK profile check labels

Relation fields:

- `from` — existing component id
- `to` — existing component id
- `kind` — concise freeform relation, e.g. `observes`, `owns`, `calls`, `validates`
- `rule` — short boundary rule

## Hard boundaries

Do not put these in `system.toml`:

- command templates;
- setup instructions;
- generic workflow rules;
- `required = true` or readiness policy;
- long architecture prose;
- broad directory tours;
- claims not grounded in read evidence.

## Public HK JSON contract

`hk brief --json`:

```json
{
  "system_map": null
}
```

or:

```json
{
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
}
```

`hk checks --changed --json`:

```json
{
  "system_context": {
    "advisory": true,
    "source": ".harness/system.toml",
    "label_resolution": {
      "status": "resolved",
      "profile": "foreman",
      "unresolved_check_labels": []
    },
    "matched_components": [],
    "warnings": []
  }
}
```

Use `relevant_check_labels` in rendered system context. Profiles remain authoritative for `required_when` and command templates.

System-context JSON should also expose:

```json
{
  "advisory": true,
  "invariant_policy": "must_preserve_unless_superseded",
  "conflict_protocol": "stop_confirm_record_decision"
}
```

`advisory` means system maps do not create readiness blockers directly. The invariant policy still means touched invariants are normative and should be preserved unless explicitly superseded.

## Validation findings

Use a shared finding shape:

```json
{
  "code": "duplicate-component-id",
  "severity": "error",
  "message": "duplicate component id 'app-state'",
  "field_path": "components[1].id",
  "related_path": null,
  "check_label": null
}
```

Severity:

- `error` — invalid map; strict/debug validation exits nonzero.
- `warning` — usable map with an authoring problem.
- `info` — low-priority note, omitted from normal text output.
