# bqutil

`bqutil` runs BigQuery SQL files and reads query-job metadata from the terminal. Use
it when you want a repeatable command-line workflow rather than the BigQuery console.
It doesn't replace dbt.

## Install

Install a reviewed Git commit with uv:

```bash
uv tool install git+https://github.com/safurrier/bqutil.git@<commit-sha>
bqutil --version
```

Before use, authenticate with Application Default Credentials or an active `gcloud`
login. The account must be able to create and read BigQuery jobs in the selected
project.

bqutil chooses a project in this order:

1. The `--project` option.
2. The default saved by `bqutil config --set-project`.
3. The result of `gcloud config get-value project`.

If no project is available, the command exits with instructions instead of opening a
prompt.

## Configure a default project

bqutil stores JSON at `$XDG_CONFIG_HOME/bqutil/config.json`. The default path is
`~/.config/bqutil/config.json`. The file stores `default_project`, `last_job_id`, and
`last_job_project`.

```bash
bqutil config --set-project my-project
bqutil config --show
bqutil config --reset
```

## Check SQL before running it

Start with a dry run. It validates the SQL and estimates processed bytes without
executing the query or changing saved job state.

```bash
bqutil query report.sql --project my-project --dry-run
```

Dry runs reject `--output`, `--analyze`, `--preview-rows`, and
`--set-default-project`. Those options require a real query or result rows.

## Run and inspect a query

```bash
# Run SQL and print at most ten preview rows to stderr.
bqutil query report.sql --project my-project --preview-rows 10

# Analyze a known job as JSON.
bqutil analyze my-project:job_id --format json

# Analyze the last query recorded in this config file.
bqutil analyze --last --format json
```

`query` submits real BigQuery work and can incur query charges. It won't mutate a
table unless the supplied SQL does. Use `--dry-run` before costly or unfamiliar SQL.

After a real query completes, bqutil records its job ID before local exports or
previews. If an export fails, recover with `bqutil analyze --last` or
`bqutil analyze PROJECT:JOB_ID`. Don't resubmit a query only to recover its ID.

## Output

Human summaries and job IDs use stdout. SQL shown by `--verbose` and result previews
use stderr. Structured analysis therefore remains safe to capture from stdout.
`analyze --format json`, `analyze --llm`, and `query --analyze` emit JSON-safe values
and never expose BigQuery SDK objects.

Output file formats follow the suffix:

- `.csv` writes CSV.
- `.json` writes JSON Lines.
- `.parquet` writes Parquet through the packaged `pyarrow` dependency.
- An unknown or missing suffix becomes `.csv`.

An export can fail after BigQuery finishes because of a local filesystem or
serialization error. The saved job ID remains available for recovery.

## Compatibility limits

The package omits the predecessor script's interactive project and job picker. Pass
an explicit project and job ID for automation-safe behavior.

The legacy dbt macro replacement is narrow. `ref()` resolves to
`PROJECT.dbt_testing.TABLE`. The `start_date()` and `end_date()` macros use local
calendar dates. Review transformed SQL with `--verbose` before executing it.

## Development

```bash
mise run check
mise run sync-check
uv build
```

See `SPEC.md` for the public correctness contract and
`docs/explanation/architecture.md` for module ownership.
