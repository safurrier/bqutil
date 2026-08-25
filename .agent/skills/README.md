---
id: agent-skills-index
title: Skills
description: >
  Index of optional opinionated workflow plugins for this repo. Each skill encodes
  a repeatable workflow that agents or humans can load on demand.
index:
  - id: adding-a-skill
    keywords: [add-skill, skill-md, references, scripts, structure]
  - id: policy
    keywords: [policy, optional, preference, ci-enforcement, canonical-truth]
---

# Skills

Vendored workflow helpers for agents and humans working in this repo.

Most skills are helpers rather than canonical source of truth. A workflow skill
may be canonical for prompt policy when its deterministic command surface lives
in `mise` tasks. These skills exist to help satisfy the repo's hard contract:

- `mise run plan-check`
- `mise run spec-check`
- `mise run evidence-check`
- `mise run review-check`
- `mise run sync-check`

Each skill follows this structure:

```
.agent/skills/<skill-name>/
├── SKILL.md          # When to use this skill and the workflow it encodes
├── references/       # Reference materials: context, docs, examples
└── scripts/          # Automation scripts used by the skill
```

## Adding a Skill

A starter template is in `example-skill/SKILL.md`. Copy it:

```bash
cp -r .agent/skills/example-skill/ .agent/skills/<your-skill-name>/
```

Then edit `SKILL.md` to describe:
- When to load this skill (activation signals)
- The opinionated workflow it encodes
- Any references or scripts alongside it

Reference the skill from `AGENTS.md` if it applies broadly.

## Policy

Skills are workflow helpers. System truth stays in `docs/` and the active plan;
repeatable prompt policy can live in a skill when the `mise` task contract is
the deterministic interface.

- If a workflow is universally agreed and objective → encode it in `mise` tasks
- If a workflow is repeatable but harness-specific → vendor it here as a skill
- If a standard becomes durable repo knowledge → move it into `docs/`

## Bundled Skills

- `slice-workflow` - canonical plan/implement/review workflow and prompt policy
- `slice-planner` - shape or update the active slice before coding
- `slice-implementer` - keep plan, validation, and evidence current while coding
- `slice-reviewer` - perform external-enough review and write `REVIEW.md`
- `plan-sync` - helper for getting the active plan ready for `sync-check`
- `spec-sync` - helper for promoting decisions into the ledger or ADRs
- `context-engineering` - helper for keeping docs routing and repo context current
- `harness-kit-profile-authoring` - helper for mining validation contracts and proposing custom `hk` profiles
