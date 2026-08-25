"""Tests for pure logic and the concrete GCP adapter's local failure mode."""

from types import SimpleNamespace

from bqutil.analysis import analyze_query_plan, format_bytes
from bqutil.gcp import current_project
from bqutil.query import replace_dbt_refs


def test_format_bytes() -> None:
    assert format_bytes(1024) == "1.00 KB"


def test_dbt_rewrite_preserves_legacy_destination() -> None:
    assert "`p.dbt_testing.orders`" in replace_dbt_refs(
        "select * from {{ ref('orders') }}", "p"
    )


def test_plan_analysis_returns_primitive_stage_records() -> None:
    stage = SimpleNamespace(
        entry_id="1",
        name="READ",
        status="DONE",
        input_stages=[],
        records_read=4,
        records_written=2,
        shuffle_output_bytes=3,
        slot_ms=80,
    )
    result = analyze_query_plan(SimpleNamespace(query_plan=[stage], slot_millis=100))
    assert result["top_time_steps"] == [
        {
            "entry_id": "1",
            "name": "READ",
            "status": "DONE",
            "input_stages": [],
            "records_read": 4,
            "records_written": 2,
            "shuffle_output_bytes": 3,
            "slot_ms": 80,
        }
    ]
    assert result["bottlenecks"][0]["type"] == "time"


def test_current_project_handles_missing_gcloud(monkeypatch) -> None:
    def missing(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr("bqutil.gcp.subprocess.run", missing)
    assert current_project() is None
