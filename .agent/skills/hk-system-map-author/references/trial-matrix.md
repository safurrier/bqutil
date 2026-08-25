# Trial matrix

Use temp copies or worktrees. Do not commit candidate maps into source repos unless approved.

## Minimum pre-HK gate

Required before implementing Harness Kit integration:

1. `foreman`
   - validates structurally;
   - has expected path matches for at least three representative edits;
   - includes concrete state/UI/tmux or lifecycle invariants.
2. `harness-toolkit`
   - validates structurally;
   - references real profile check labels where possible;
   - demonstrates profile/system-map separation.

## Extended trial set

- `sample-cli` — small CLI; map should be tiny or explicitly unnecessary.
- `ml/models/relevance_v1` — narrow ML leaf; model artifact/config invariants.
- `workflow_control` — workflow module; agent/control-plane boundaries.
- `api` — large application module; should produce only a routing/index-style map unless nested maps are later justified.

## Path-query checks

For each map, choose three representative paths and verify:

- matched component is expected;
- matched invariants are relevant;
- read-before-editing files are useful;
- relevant check labels either exist in profile or are recorded as unresolved warnings.

## Behavioral dogfood gate

After HK integration, use the HK PR-sized dogfood pattern:

- temp snapshots only;
- HK logging wrapper;
- minimal worker guidance;
- realistic task touching mapped paths;
- worker report and HK command log retained.

A trial passes only if:

- worker notices `system_map` in `hk brief` or `system_context` in `hk checks --changed` without being explicitly taught a new command;
- context changes edit routing, docs reading, or validation choice;
- worker does not confuse relevant labels with required checks;
- text output remains terse.

## Kill criteria

Stop or park if:

- maps are architecture prose in TOML;
- `hk checks --changed` becomes noisy;
- agents ignore the context;
- profiles alone cover the useful guidance;
- maps are too expensive to maintain.
