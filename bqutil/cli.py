"""Click command surface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click
from google.api_core.exceptions import GoogleAPICallError
from google.auth.exceptions import GoogleAuthError
from rich.console import Console

from . import __version__
from .analysis import analyze_query_plan, compare_query_jobs, format_bytes
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


def resolve_job_reference(
    job_reference: str,
    explicit_project: str | None,
    shared_project: str | None,
    explicit_location: str | None,
    shared_location: str | None,
) -> tuple[str, str, str | None]:
    """Resolve one compare operand with qualified IDs taking project precedence."""
    if ":" in job_reference:
        project, job_id = job_reference.split(":", 1)
    else:
        project = resolve_project(explicit_project or shared_project)
        job_id = job_reference
    return project, job_id, explicit_location or shared_location


def fetch_comparison_job(
    operand: str, project: str, job_id: str, location: str | None
) -> Any:
    """Fetch one comparison operand with an actionable BigQuery failure."""
    try:
        return get_job(project, job_id, location)
    except (GoogleAPICallError, GoogleAuthError) as error:
        location_detail = location or "unspecified"
        raise click.ClickException(
            f"Unable to fetch {operand} job '{job_id}' in project '{project}' "
            f"at location '{location_detail}'. Check the job ID, location, and BigQuery permissions."
        ) from error


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


def format_signed_number(value: int | None, unit: str) -> str:
    """Render an exact signed numeric delta or an unavailable value."""
    if value is None:
        return "unavailable"
    return f"{value:+,} {unit}"


def format_signed_bytes(value: int | None) -> str:
    """Render a byte delta while preserving its sign."""
    if value is None:
        return "unavailable"
    sign = "+" if value >= 0 else "-"
    return f"{sign}{format_bytes(abs(value))}"


def render_comparison_text(comparison: dict[str, Any]) -> None:
    """Render a concise human delta summary without assigning a quality verdict."""
    click.echo("Candidate minus baseline: positive means candidate is greater.")
    click.echo("Missing values are unavailable; no optimization verdict is inferred.")
    units = {
        "duration_milliseconds": "ms",
        "bytes_processed": "bytes",
        "slot_milliseconds": "ms",
        "stage_count": "stages",
        "stage_records_read_sum": "stage records read",
        "stage_shuffle_output_bytes_sum": "stage shuffle bytes",
    }
    labels = {
        "duration_milliseconds": "Duration",
        "bytes_processed": "Bytes processed",
        "slot_milliseconds": "Slot milliseconds",
        "stage_count": "Query-plan stage count",
        "stage_records_read_sum": "Stage records read sum",
        "stage_shuffle_output_bytes_sum": "Stage shuffle output bytes sum",
    }
    for metric, evidence in comparison["metrics"].items():
        delta = evidence["absolute_delta"]
        if metric in {"bytes_processed", "stage_shuffle_output_bytes_sum"}:
            rendered_delta = format_signed_bytes(delta)
        else:
            rendered_delta = format_signed_number(delta, units[metric])
        percent = evidence["percent_change"]
        rendered_percent = "unavailable" if percent is None else f"{percent:+.2f}%"
        click.echo(f"{labels[metric]}: {rendered_delta} ({rendered_percent})")


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    epilog=(
        "\b\nAgent workflow:\n"
        "  bqutil query candidate.sql --project PROJECT --dry-run\n"
        "  bqutil query candidate.sql --project PROJECT\n"
        "  bqutil analyze --last --format json\n"
        "  bqutil compare BASELINE_JOB CANDIDATE_JOB --project PROJECT --format json\n\n"
        "Queries can incur BigQuery charges. Use --dry-run before unfamiliar SQL.\n"
        "Compare retains raw evidence and exact candidate-minus-baseline deltas; the caller\n"
        "decides what the evidence means."
    ),
)
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
            "last_job_location": None,
        }
        save_config(config)
    if project:
        config["default_project"] = project
        save_config(config)
    if show or not (project or reset):
        click.echo(json.dumps(config, indent=2))


@main.command(
    "analyze",
    epilog="Examples:\n  bqutil analyze PROJECT:JOB_ID --format json\n  bqutil analyze JOB_ID --project PROJECT --location asia-northeast1\n  bqutil analyze --last --format json",
)
@click.argument("job_id", required=False)
@click.option("--project", "project_option", metavar="PROJECT")
@click.option(
    "--location", "location_option", metavar="LOCATION", help="BigQuery job location."
)
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
    location_option: str | None,
    output_format: str,
    verbose: bool,
    llm: bool,
    debug: bool,
    last_job: bool,
) -> None:
    """Analyze JOB_ID; use PROJECT:JOB_ID to specify its project."""
    config = load_config()
    location = location_option
    if last_job:
        job_id, project_option = config["last_job_id"], config["last_job_project"]
        location = location or config["last_job_location"]
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
    job = get_job(resolve_project(project_option), job_id, location)
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
    "compare",
    epilog=(
        "\b\nExamples:\n"
        "  bqutil compare before-job after-job --project PROJECT --format json\n"
        "  bqutil compare PROJECT:before PROJECT:after --location US --format text\n"
        "  bqutil compare before after --baseline-location US "
        "--candidate-location asia-northeast1 --format json"
    ),
)
@click.argument("baseline_job", metavar="BASELINE_JOB")
@click.argument("candidate_job", metavar="CANDIDATE_JOB")
@click.option(
    "--project",
    "shared_project",
    metavar="PROJECT",
    help="Project fallback for both jobs.",
)
@click.option(
    "--baseline-project", metavar="PROJECT", help="Project fallback for BASELINE_JOB."
)
@click.option(
    "--candidate-project", metavar="PROJECT", help="Project fallback for CANDIDATE_JOB."
)
@click.option(
    "--location",
    "shared_location",
    metavar="LOCATION",
    help="Location fallback for both jobs.",
)
@click.option(
    "--baseline-location",
    metavar="LOCATION",
    help="Location fallback for BASELINE_JOB.",
)
@click.option(
    "--candidate-location",
    metavar="LOCATION",
    help="Location fallback for CANDIDATE_JOB.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="json",
    show_default=True,
    help="Output JSON evidence by default; use text for a concise delta summary.",
)
def compare(
    baseline_job: str,
    candidate_job: str,
    shared_project: str | None,
    baseline_project: str | None,
    candidate_project: str | None,
    shared_location: str | None,
    baseline_location: str | None,
    candidate_location: str | None,
    output_format: str,
) -> None:
    """Compare query jobs; every delta is CANDIDATE_JOB minus BASELINE_JOB."""
    baseline_project_id, baseline_job_id, baseline_location_id = resolve_job_reference(
        baseline_job,
        baseline_project,
        shared_project,
        baseline_location,
        shared_location,
    )
    candidate_project_id, candidate_job_id, candidate_location_id = (
        resolve_job_reference(
            candidate_job,
            candidate_project,
            shared_project,
            candidate_location,
            shared_location,
        )
    )
    baseline = fetch_comparison_job(
        "baseline", baseline_project_id, baseline_job_id, baseline_location_id
    )
    candidate = fetch_comparison_job(
        "candidate", candidate_project_id, candidate_job_id, candidate_location_id
    )
    if baseline.job_type != "query" or candidate.job_type != "query":
        raise click.UsageError(
            "compare only supports query jobs. Pass BigQuery query job IDs for both operands."
        )
    comparison = compare_query_jobs(baseline, candidate)
    if output_format == "json":
        click.echo(json.dumps(comparison, indent=2))
        return
    render_comparison_text(comparison)


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
    sql = replace_dbt_refs(query_file.read_text(), project)
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
    config.update(
        {
            "last_job_id": job.job_id,
            "last_job_project": project,
            "last_job_location": getattr(job, "location", None),
        }
    )
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
