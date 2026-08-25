"""Click command surface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click
from rich.console import Console

from . import __version__
from .analysis import analyze_query_plan, format_bytes
from .config import load_config, save_config
from .gcp import client, current_project, get_job
from .query import dry_run_query, preview_rows, replace_dbt_refs, run_query

console = Console(stderr=True)


def resolve_project(project: str | None) -> str:
    """Resolve explicit, saved, then gcloud-configured project selection."""
    if project:
        return project
    config = load_config()
    if config["default_project"]:
        return str(config["default_project"])
    if discovered := current_project():
        return discovered
    raise click.UsageError(
        "A project is required. Pass --project or run 'bqutil config --set-project PROJECT'."
    )


def job_data(job: Any) -> dict[str, Any]:
    """Render public job information without exposing SDK objects."""
    data: dict[str, Any] = {
        "job_id": job.job_id,
        "project": job.project,
        "location": getattr(job, "location", None),
        "state": job.state,
        "error_result": getattr(job, "error_result", None),
        "job_type": job.job_type,
    }
    if job.job_type == "query":
        data["query_details"] = {
            "query": getattr(job, "query", None),
            "bytes_processed": getattr(job, "total_bytes_processed", None),
            "slot_ms": getattr(job, "slot_millis", None),
            "cache_hit": getattr(job, "cache_hit", None),
            "query_plan_analysis": analyze_query_plan(job),
        }
    return data


def debug_data(job: Any) -> dict[str, Any]:
    """Return a stable, documented diagnostic subset of source job attributes."""
    return {
        "created": str(getattr(job, "created", None) or ""),
        "started": str(getattr(job, "started", None) or ""),
        "ended": str(getattr(job, "ended", None) or ""),
        "user_email": getattr(job, "user_email", None),
        "destination": str(getattr(job, "destination", None) or ""),
        "total_bytes_billed": getattr(job, "total_bytes_billed", None),
    }


def render_preview(job: Any, limit: int) -> None:
    """Write a bounded query-result preview to stderr."""
    rows = preview_rows(job, limit)
    console.print(f"Preview (up to {limit} rows):")
    console.print_json(json.dumps(rows, default=str))


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__)
def main() -> None:
    """Execute BigQuery SQL files and inspect existing BigQuery jobs."""


@main.command(
    "config",
    epilog="Examples:\n  bqutil config --set-project my-project\n  bqutil config --show\n  bqutil config --reset",
)
@click.option(
    "--set-project",
    "project",
    metavar="PROJECT",
    help="Set the default Google Cloud project.",
)
@click.option("--show", is_flag=True, help="Show persistent configuration as JSON.")
@click.option("--reset", is_flag=True, help="Reset persistent configuration.")
def configure(project: str | None, show: bool, reset: bool) -> None:
    """Manage $XDG_CONFIG_HOME/bqutil/config.json."""
    config = load_config()
    if reset:
        config = {
            "default_project": None,
            "last_job_id": None,
            "last_job_project": None,
        }
        save_config(config)
    if project:
        config["default_project"] = project
        save_config(config)
    if show or not (project or reset):
        click.echo(json.dumps(config, indent=2))


@main.command(
    "analyze",
    epilog="Examples:\n  bqutil analyze PROJECT:JOB_ID --format json\n  bqutil query query.sql --project PROJECT\n  bqutil analyze --last --format json",
)
@click.argument("job_id", required=False)
@click.option("--project", "project_option", metavar="PROJECT")
@click.option(
    "--format", "output_format", type=click.Choice(["text", "json"]), default="text"
)
@click.option(
    "--verbose", is_flag=True, help="Include query-plan summary in text output."
)
@click.option("--llm", is_flag=True, help="Emit compact JSON for an LLM consumer.")
@click.option(
    "--debug",
    is_flag=True,
    help="Include stable source-job diagnostics in text output.",
)
@click.option(
    "--last",
    "last_job",
    is_flag=True,
    help="Analyze the job recorded by the last successful query.",
)
def analyze(
    job_id: str | None,
    project_option: str | None,
    output_format: str,
    verbose: bool,
    llm: bool,
    debug: bool,
    last_job: bool,
) -> None:
    """Analyze JOB_ID; use PROJECT:JOB_ID to specify its project."""
    config = load_config()
    if last_job:
        job_id, project_option = config["last_job_id"], config["last_job_project"]
        if not job_id or not project_option:
            raise click.UsageError(
                "No last job is recorded. Pass JOB_ID and --project."
            )
    if job_id and ":" in job_id and not project_option:
        project_option, job_id = job_id.split(":", 1)
    if not job_id:
        raise click.UsageError(
            "JOB_ID is required unless --last is used; interactive selection was removed for reliable automation."
        )
    job = get_job(resolve_project(project_option), job_id)
    data = job_data(job)
    if llm:
        click.echo(
            json.dumps(
                {
                    "query": data.get("query_details", {}).get("query", ""),
                    "performance_data": data.get("query_details", {}),
                },
                indent=2,
            )
        )
        return
    if output_format == "json":
        click.echo(json.dumps(data, indent=2))
        return
    click.echo(f"Job {data['job_id']} ({data['state']}) in {data['project']}")
    details = data.get("query_details")
    if details:
        click.echo(f"Bytes processed: {format_bytes(details['bytes_processed'])}")
        if verbose:
            summary = details["query_plan_analysis"]
            click.echo(
                f"Query-plan stages: {summary['steps_count']}; bottlenecks: {len(summary['bottlenecks'])}"
            )
    if debug:
        click.echo(
            "Diagnostics: " + json.dumps(debug_data(job), default=str, sort_keys=True)
        )


@main.command(
    "query",
    epilog="Examples:\n  bqutil query query.sql --project PROJECT --dry-run\n  bqutil query query.sql --project PROJECT --preview-rows 10\n  bqutil query query.sql --project PROJECT --output results.parquet\n  bqutil query query.sql --project PROJECT && bqutil analyze --last --format json",
)
@click.argument(
    "query_file", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--project", "project_option", metavar="PROJECT")
@click.option(
    "--analyze",
    "analyze_after",
    is_flag=True,
    help="Print JSON analysis after a completed query.",
)
@click.option("--verbose", is_flag=True, help="Print processed SQL to stderr.")
@click.option(
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Write CSV, JSON Lines, or Parquet based on suffix.",
)
@click.option(
    "--preview-rows",
    type=click.IntRange(1),
    default=5,
    show_default=True,
    help="Render at most this many result rows to stderr.",
)
@click.option(
    "--set-default-project",
    is_flag=True,
    help="Save the resolved project as the default.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Validate and estimate SQL without executing it or changing saved job state.",
)
def query(
    query_file: Path,
    project_option: str | None,
    analyze_after: bool,
    verbose: bool,
    output: Path | None,
    preview_rows: int,
    set_default_project: bool,
    dry_run: bool,
) -> None:
    """Execute SQL from QUERY_FILE. Queries can incur BigQuery charges."""
    project = resolve_project(project_option)
    sql = query_file.read_text()
    if "{{ ref(" in sql:
        sql = replace_dbt_refs(sql, project)
    if verbose:
        console.print(sql)
    if dry_run:
        context = click.get_current_context()
        preview_set = (
            context.get_parameter_source("preview_rows")
            != click.core.ParameterSource.DEFAULT
        )
        if output or analyze_after or set_default_project or preview_set:
            raise click.UsageError(
                "--dry-run cannot be combined with --output, --analyze, --preview-rows, or --set-default-project."
            )
        job = dry_run_query(sql, client(project))
        click.echo(
            json.dumps(
                {
                    "project": project,
                    "dry_run": True,
                    "bytes_processed": getattr(job, "total_bytes_processed", None),
                    "bytes_processed_human": format_bytes(
                        getattr(job, "total_bytes_processed", None)
                    ),
                },
                indent=2,
            )
        )
        return
    bq_client = client(project)
    job, elapsed = run_query(sql, bq_client)
    config = load_config()
    config.update({"last_job_id": job.job_id, "last_job_project": project})
    if set_default_project:
        config["default_project"] = project
    save_config(config)
    job_status = f"Job ID: {job.job_id} ({elapsed:.2f}s)"
    if analyze_after:
        console.print(job_status)
    else:
        click.echo(job_status)
    if output:
        frame = job.to_dataframe()
        suffix = output.suffix.lower()
        if suffix == ".parquet":
            frame.to_parquet(output, index=False)
        elif suffix == ".json":
            frame.to_json(output, orient="records", lines=True)
        else:
            frame.to_csv(
                output if suffix == ".csv" else output.with_suffix(".csv"), index=False
            )
    render_preview(job, preview_rows)
    if analyze_after:
        click.echo(json.dumps(job_data(job), indent=2))
