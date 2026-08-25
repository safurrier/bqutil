# Validation summary

The scaffold-native check passed with 36 tests plus Ruff, formatting, and ty. Package
build and isolated editable installation passed. A final credentialed
`SELECT 1 AS validation_value` saved the `US` job location, and
`analyze --last --format json` retrieved that completed job. The GitHub repair also
adds fake-client coverage for explicit and persisted locations, legacy config
normalization, and unconditional legacy macro preprocessing.
