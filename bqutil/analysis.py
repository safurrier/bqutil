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


def stage_record(stage: Any) -> dict[str, Any]:
    """Return the stable primitive fields used from a BigQuery query-plan stage."""
    return {
        "entry_id": getattr(stage, "entry_id", None),
        "name": getattr(stage, "name", None),
        "status": getattr(stage, "status", None),
        "input_stages": list(getattr(stage, "input_stages", None) or []),
        "records_read": getattr(stage, "records_read", None),
        "records_written": getattr(stage, "records_written", None),
        "shuffle_output_bytes": getattr(stage, "shuffle_output_bytes", None),
        "slot_ms": getattr(stage, "slot_ms", None),
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
