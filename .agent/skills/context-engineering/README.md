# Context Engineering

This repo vendors a lightweight context-engineering workflow so docs routing and
durable knowledge can evolve with the code.

## Quick Start

- Use `docs/AGENTS.md` as the routing index for agents
- Keep durable explanations in `docs/explanation/`
- Keep stable standards in `docs/reference/`
- Promote repeated lessons out of `.ai/plans/` and into docs

## Relationship To The Task Contract

This workflow helps satisfy `mise run spec-check` and `mise run sync-check`.
It does not replace them.
