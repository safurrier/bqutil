---
name: slice-reviewer
description: >
  Compatibility wrapper for the review phase of the slice workflow. Use when
  preparing a slice handoff or validating review evidence.
allowed-tools: Read, Edit, Glob, Grep, Bash
---

# Slice Reviewer

Use the canonical `slice-workflow` skill.

Render the review prompt with:

```bash
mise run slice-review
```

Then follow the rendered prompt in the active plan's `prompts/reviewer.md`.
