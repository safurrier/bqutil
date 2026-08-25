---
id: plan-spec
title: Task Specification
description: Requirements and constraints for extracting bqutil from Dots.
---

# Specification — package-bqutil

## Problem

The Dots repository owned bqutil as a 1,192-line PEP 723 script with a manual smoke
driver. It lacked an installable package seam, isolated tests, and a stable Git pin.

## Requirements

### MUST

- Preserve the supported commands, XDG config path and keys, project-qualified job
  IDs, and `--last` workflow.
- Keep structured output JSON-safe and noninteractive failures actionable.
- Validate without network or credentials in the routine test suite.
- Support a pinned Git-source installation and a recoverable real query workflow.

### SHOULD

- Keep one concrete BigQuery adapter rather than introducing a plugin framework.
- Document authentication, billing, dry-run, output, and compatibility behavior.

## Constraints

A live query requires an explicitly approved project. Routine tests must not create
BigQuery jobs or incur charges.
