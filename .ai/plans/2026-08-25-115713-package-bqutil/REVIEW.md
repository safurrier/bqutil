---
id: plan-review
title: Review Log
description: Agent-friendly CLI and architecture-polish review evidence.
---

# Review — package-bqutil

## Review Context

- Mode: external
- Backend: subagent
- Reviewer: Pi subagents `866455be` (agent-friendly CLI) and `fd1e6645` (architecture polish)

## Rubrics

- core-quality
- docs-info-architecture
- agent-friendly CLI behavior
- architecture polish

## Findings

- P1: Query-plan SDK objects made real JSON paths non-serializable.
- P1: Missing `gcloud` could bypass the actionable project error with a traceback.
- P1: Real SQL lacked a dry-run and retry-safe recovery path.
- P1: Compatibility options were accepted without behavior.
- P1: The public CLI and migration contract remained generic scaffold text.
- P1: `query --analyze` mixed a human job line with its stdout JSON document.
- P2: Invalid dry-run option combinations constructed a credentialed client before
  local validation.

## Disposition

- Addressed every blocking finding with focused tests for nonempty plan
  serialization, missing `gcloud`, dry-run state safety, previews, verbose/debug
  output, and recovery state.
- Replaced scaffold placeholders in README, SPEC, architecture, and AGENTS files with
  the verified tool contract.
- Verified the repaired paths with a real dry run, real `SELECT 1`, and
  `analyze --last --format json` against the approved project.
- Routed the `query --analyze` job line to stderr and moved dry-run conflict checks
  before client construction. Focused regression tests cover both Codex findings.
