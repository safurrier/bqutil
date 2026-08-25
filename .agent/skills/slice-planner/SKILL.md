---
name: slice-planner
description: >
  Compatibility wrapper for the planning phase of the slice workflow. Use when
  shaping a slice before coding or when asked to plan a task with the generated
  slice workflow.
allowed-tools: Read, Edit, Glob, Grep, Bash
---

# Slice Planner

Use the canonical `slice-workflow` skill.

Render the planning prompt with:

```bash
mise run slice-plan -- --task path/to/task.md
```

Then follow the rendered prompt in the active plan's `prompts/planner.md`.
