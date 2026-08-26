# Compare-jobs review summary

Two fresh-context specialists reviewed the comparison command. The agent-friendly
review required a copyable project fallback in root help and actionable errors for
baseline and candidate fetch failures. The heuristic-authority review required the
public comparison to retain all public query-plan-stage evidence and distinguish a
missing plan from an observed empty plan.

The repair adds `--project PROJECT` to root help, operand-specific `ClickException`
errors, complete JSON-safe stage records, and null-preserving unavailable plan metrics.
Focused tests cover each repair. The command still emits only raw operand summaries
and exact candidate-minus-baseline deltas; it has no optimization label, score,
threshold, recommendation, action gate, or regression exit code.

The final Codex review identified two follow-ups. Compare now catches both Google API
and credential failures at the same operand-specific error seam, and the ledger links
to the committed Markdown schema artifact. A GitHub review then found that default
text omitted raw evidence; JSON is now the default and text is explicitly concise.
