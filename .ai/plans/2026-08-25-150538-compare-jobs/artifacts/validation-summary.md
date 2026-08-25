# Compare-jobs validation summary

Focused tests cover copyable root help, default parseable JSON with raw job evidence,
explicit concise text, project and location precedence, complete query-plan stage
evidence, unavailable-plan nulls, exact deltas, and baseline or candidate fetch
failures without tracebacks. The scaffold gate passes
formatting, Ruff, ty, and the full pytest suite. A source distribution, wheel, and
isolated editable installation expose root and compare help.

A credentialed smoke fetched two existing completed jobs from an approved development
project. The JSON result retained both summaries and exact deltas, including null
percentages for zero baselines and null candidate metrics when BigQuery omitted them.
The read-only command submitted no BigQuery work and changed no config.
