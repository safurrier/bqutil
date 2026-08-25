---
name: slice-implementer
description: >
  Compatibility wrapper for the implementation phase of the slice workflow. Use
  when implementing an active slice while keeping validation and evidence current.
allowed-tools: Read, Edit, Glob, Grep, Bash
---

# Slice Implementer

Use the canonical `slice-workflow` skill.

Render the implementation prompt with:

```bash
mise run slice-implement
```

Then follow the rendered prompt in the active plan's `prompts/implementer.md`.
