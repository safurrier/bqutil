# Review summary

Fresh-context agent-friendly CLI and architecture-polish reviewers initially blocked
the extraction on non-serializable query-plan objects, no-op options, missing gcloud
handling, lack of dry-run/recovery behavior, and placeholder documentation. The
repaired implementation addressed every blocking finding and added focused tests.
A later exact-scope Codex review found mixed stdout for `query --analyze` and early
credential construction for invalid dry runs; both received focused repairs.
GitHub review then identified missing non-US/EU job locations and conditional legacy
macro preprocessing. This repair adds the location contract and unconditional
preprocessing with focused coverage.
