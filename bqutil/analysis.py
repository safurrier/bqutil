"""BigQuery job-analysis helpers with JSON-safe output."""

from __future__ import annotations

from typing import Any


def format_bytes(value: int | None) -> str:
    """Render a byte count for terminal output."""
    amount = float(value or 0)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if amount < 1024:
            return f"{amount:.2f} {unit}"
        amount /= 1024
    return f"{amount:.2f} PB"


def timestamp_record(value: Any) -> str | None:
    """Convert an SDK timestamp to an ISO string without leaking the SDK value."""
    return value.isoformat() if value is not None else None


def step_record(step: Any) -> dict[str, Any]:
    """Return a JSON-safe representation of one public query-plan step."""
    return {
        "kind": getattr(step, "kind", None),
        "substeps": list(getattr(step, "substeps", None) or []),
    }


def stage_record(stage: Any) -> dict[str, Any]:
    """Preserve every public QueryPlanEntry field as JSON-safe comparison evidence."""
    return {
        "entry_id": getattr(stage, "entry_id", None),
        "name": getattr(stage, "name", None),
        "status": getattr(stage, "status", None),
        "start": timestamp_record(getattr(stage, "start", None)),
        "end": timestamp_record(getattr(stage, "end", None)),
        "input_stages": list(getattr(stage, "input_stages", None) or []),
        "parallel_inputs": getattr(stage, "parallel_inputs", None),
        "completed_parallel_inputs": getattr(stage, "completed_parallel_inputs", None),
        "wait_ms_avg": getattr(stage, "wait_ms_avg", None),
        "wait_ms_max": getattr(stage, "wait_ms_max", None),
        "wait_ratio_avg": getattr(stage, "wait_ratio_avg", None),
        "wait_ratio_max": getattr(stage, "wait_ratio_max", None),
        "read_ms_avg": getattr(stage, "read_ms_avg", None),
        "read_ms_max": getattr(stage, "read_ms_max", None),
        "read_ratio_avg": getattr(stage, "read_ratio_avg", None),
        "read_ratio_max": getattr(stage, "read_ratio_max", None),
        "compute_ms_avg": getattr(stage, "compute_ms_avg", None),
        "compute_ms_max": getattr(stage, "compute_ms_max", None),
        "compute_ratio_avg": getattr(stage, "compute_ratio_avg", None),
        "compute_ratio_max": getattr(stage, "compute_ratio_max", None),
        "write_ms_avg": getattr(stage, "write_ms_avg", None),
        "write_ms_max": getattr(stage, "write_ms_max", None),
        "write_ratio_avg": getattr(stage, "write_ratio_avg", None),
        "write_ratio_max": getattr(stage, "write_ratio_max", None),
        "records_read": getattr(stage, "records_read", None),
        "records_written": getattr(stage, "records_written", None),
        "shuffle_output_bytes": getattr(stage, "shuffle_output_bytes", None),
        "shuffle_output_bytes_spilled": getattr(
            stage, "shuffle_output_bytes_spilled", None
        ),
        "slot_ms": getattr(stage, "slot_ms", None),
        "steps": [step_record(step) for step in getattr(stage, "steps", None) or []],
    }


def duration_milliseconds(job: Any) -> int | None:
    """Return completed job duration in milliseconds when both timestamps exist."""
    started = getattr(job, "started", None)
    ended = getattr(job, "ended", None)
    if started is None or ended is None:
        return None
    return round((ended - started).total_seconds() * 1000)


def stage_sum(stages: list[dict[str, Any]], metric: str) -> int | None:
    """Sum a stage metric without treating unknown stage values as zero."""
    values = [stage[metric] for stage in stages]
    if any(value is None for value in values):
        return None
    return sum(values)


def metric_comparison(
    baseline: int | None, candidate: int | None
) -> dict[str, int | float | None]:
    """Return exact candidate-minus-baseline evidence for one numeric metric."""
    if baseline is None or candidate is None:
        return {
            "baseline": baseline,
            "candidate": candidate,
            "absolute_delta": None,
            "percent_change": None,
        }
    absolute_delta = candidate - baseline
    return {
        "baseline": baseline,
        "candidate": candidate,
        "absolute_delta": absolute_delta,
        "percent_change": (absolute_delta / baseline * 100) if baseline else None,
    }


def query_job_summary(job: Any) -> dict[str, Any]:
    """Return raw JSON-safe query job evidence and exact comparable metrics."""
    query_plan = getattr(job, "query_plan", None)
    stages = (
        [stage_record(stage) for stage in query_plan]
        if query_plan is not None
        else None
    )
    return {
        "job_id": job.job_id,
        "project": job.project,
        "location": getattr(job, "location", None),
        "state": job.state,
        "error_result": getattr(job, "error_result", None),
        "query": getattr(job, "query", None),
        "cache_hit": getattr(job, "cache_hit", None),
        "query_plan": stages,
        "metrics": {
            "duration_milliseconds": duration_milliseconds(job),
            "bytes_processed": getattr(job, "total_bytes_processed", None),
            "slot_milliseconds": getattr(job, "slot_millis", None),
            "stage_count": len(stages) if stages is not None else None,
            "stage_records_read_sum": stage_sum(stages, "records_read")
            if stages is not None
            else None,
            "stage_shuffle_output_bytes_sum": (
                stage_sum(stages, "shuffle_output_bytes")
                if stages is not None
                else None
            ),
        },
    }


def compare_query_jobs(baseline_job: Any, candidate_job: Any) -> dict[str, Any]:
    """Retain both raw job summaries and exact candidate-minus-baseline deltas."""
    baseline = query_job_summary(baseline_job)
    candidate = query_job_summary(candidate_job)
    baseline_metrics = baseline["metrics"]
    candidate_metrics = candidate["metrics"]
    return {
        "semantics": "candidate_minus_baseline",
        "baseline": baseline,
        "candidate": candidate,
        "metrics": {
            metric: metric_comparison(
                baseline_metrics[metric], candidate_metrics[metric]
            )
            for metric in baseline_metrics
        },
    }


def analyze_query_plan(job: Any) -> dict[str, Any]:
    """Summarize a query plan using only JSON primitives."""
    stages = [stage_record(stage) for stage in getattr(job, "query_plan", None) or []]
    timed = sorted(
        (stage for stage in stages if stage["slot_ms"]),
        key=lambda stage: stage["slot_ms"] or 0,
        reverse=True,
    )
    records = sorted(
        (stage for stage in stages if stage["records_read"]),
        key=lambda stage: stage["records_read"] or 0,
        reverse=True,
    )
    shuffled = sorted(
        (stage for stage in stages if stage["shuffle_output_bytes"]),
        key=lambda stage: stage["shuffle_output_bytes"] or 0,
        reverse=True,
    )
    bottlenecks: list[dict[str, Any]] = []
    total = getattr(job, "slot_millis", 0) or 0
    for stage in timed[:3]:
        percentage = (stage["slot_ms"] or 0) / total * 100 if total else 0
        if percentage > 25:
            bottlenecks.append(
                {
                    "type": "time",
                    "step_id": stage["entry_id"],
                    "name": stage["name"],
                    "percentage": percentage,
                }
            )
    for stage in records[:2]:
        bottlenecks.append(
            {
                "type": "data",
                "step_id": stage["entry_id"],
                "name": stage["name"],
                "records": stage["records_read"],
            }
        )
    for stage in shuffled[:2]:
        bottlenecks.append(
            {
                "type": "shuffle",
                "step_id": stage["entry_id"],
                "name": stage["name"],
                "bytes": stage["shuffle_output_bytes"],
            }
        )
    return {
        "steps_count": len(stages),
        "bottlenecks": bottlenecks,
        "top_time_steps": timed[:3],
        "top_data_steps": records[:3],
        "top_shuffle_steps": shuffled[:3],
    }
