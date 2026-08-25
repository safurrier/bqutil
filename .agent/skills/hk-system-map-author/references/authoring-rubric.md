# Authoring rubric

A good `.harness/system.toml` is a narrow interface, not a document.

## A-level map

- Names components by ownership boundary, not folder name.
- Routes changed paths to the component an agent must understand before editing.
- States must-preserve invariants future edits can violate.
- Links to concise read-before-editing files.
- References existing HK profile check labels where possible.
- Stays compact enough that `hk checks --changed` can render a terse advisory.

## B-level map

- Valid TOML and mostly useful paths.
- Components are somewhat folder-shaped but still help edit routing.
- Invariants are true but too broad or too obvious.
- Check labels need profile cleanup.

## Failing map

- Reads like `docs/architecture.md` translated into TOML.
- Contains commands, setup instructions, readiness policy, or workflow gotchas.
- Lists every directory as a component.
- Uses vague components such as `backend`, `frontend`, `misc`, or `utils` without ownership semantics.
- Has invariants that cannot be validated or tied to evidence.
- Invents check labels with no profile plan.

## Component selection heuristic

Add a component only when it has at least two of:

- distinct responsibility boundary;
- owned state, data, resource, protocol, lifecycle, or artifact;
- input/output messages, commands, events, side effects, or model artifacts;
- invariant future edits often violate;
- focused validation or profile review label;
- separate docs or domain vocabulary.

Skip components that are:

- arbitrary folders;
- generated/vendored code;
- obvious thin wrappers;
- one-file utilities with no invariant;
- better represented as a profile check only.

## Field quality

- `summary`: one sentence.
- `title`: short noun phrase.
- `kind`: 1-3 words, kebab-case preferred.
- `statement`: one sentence; concrete, testable, and ownership-oriented.
- `rule`: one sentence boundary rule.
- `read_before_editing`: only files worth opening before touching the component.
- `validation_checks`: labels, never commands.

## Evidence discipline

Prefer observed facts from code, tests, config, docs, and profiles. If uncertain, either omit the field or add a short TOML comment near the candidate. Do not turn speculation into invariants.

## Review questions

- Would `hk checks --changed` output from this map change an agent's next action?
- Is every invariant phrased as a must-preserve constraint with evidence or a relevant check label?
- Is any field trying to teach workflow rather than model ownership?
- Could a profile alone express this just as well? If yes, remove it.
- For high-risk invariants, should the profile require an invariant-conflict review?
- Is the map stable enough to maintain after normal code changes?
