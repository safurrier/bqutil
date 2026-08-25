"""Tests for pure logic and the concrete GCP adapter's local failure mode."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from bqutil.analysis import (
    analyze_query_plan,
    compare_query_jobs,
    format_bytes,
    query_job_summary,
)
from bqutil.gcp import current_project, get_job
from bqutil.query import replace_dbt_refs


def test_format_bytes() -> None:
    assert format_bytes(1024) == "1.00 KB"


def test_dbt_rewrite_preserves_legacy_destination() -> None:
    assert "`p.dbt_testing.orders`" in replace_dbt_refs(
        "select * from {{ ref('orders') }}", "p"
    )


def test_dbt_rewrite_handles_whitespace_refs_and_date_only_macros() -> None:
    whitespace_ref = replace_dbt_refs("select * from {{  ref('orders') }}", "p")
    date_only = replace_dbt_refs("select {{ start_date() }}, {{ end_date() }}", "p")

    assert "`p.dbt_testing.orders`" in whitespace_ref
    assert "{{" not in date_only


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
    stage_record = result["top_time_steps"][0]
    assert stage_record["entry_id"] == "1"
    assert stage_record["name"] == "READ"
    assert stage_record["status"] == "DONE"
    assert stage_record["records_read"] == 4
    assert stage_record["shuffle_output_bytes"] == 3
    assert stage_record["slot_ms"] == 80
    assert stage_record["steps"] == []
    assert result["bottlenecks"][0]["type"] == "time"


def test_get_job_passes_location_to_bigquery_client(monkeypatch) -> None:
    captured: dict[str, str | None] = {}

    class FakeClient:
        def get_job(self, job_id: str, project: str, location: str | None) -> str:
            captured.update(job_id=job_id, project=project, location=location)
            return "job"

    monkeypatch.setattr("bqutil.gcp.client", lambda project: FakeClient())

    assert get_job("project", "job", "asia-northeast1") == "job"
    assert captured == {
        "job_id": "job",
        "project": "project",
        "location": "asia-northeast1",
    }


def test_compare_query_jobs_retains_evidence_and_exact_deltas() -> None:
    baseline = SimpleNamespace(
        job_id="before",
        project="project",
        location="US",
        state="DONE",
        error_result=None,
        job_type="query",
        query="SELECT 1",
        total_bytes_processed=100,
        slot_millis=200,
        cache_hit=False,
        started=None,
        ended=None,
        query_plan=[
            SimpleNamespace(
                entry_id="1",
                name="READ",
                status="DONE",
                input_stages=[],
                records_read=10,
                records_written=1,
                shuffle_output_bytes=20,
                slot_ms=200,
            )
        ],
    )
    candidate = SimpleNamespace(
        job_id="after",
        project="project",
        location="US",
        state="DONE",
        error_result=None,
        job_type="query",
        query="SELECT 1",
        total_bytes_processed=150,
        slot_millis=100,
        cache_hit=True,
        started=None,
        ended=None,
        query_plan=[
            SimpleNamespace(
                entry_id="2",
                name="READ",
                status="DONE",
                input_stages=[],
                records_read=25,
                records_written=1,
                shuffle_output_bytes=10,
                slot_ms=100,
            )
        ],
    )

    comparison = compare_query_jobs(baseline, candidate)

    assert comparison["semantics"] == "candidate_minus_baseline"
    assert comparison["baseline"]["cache_hit"] is False
    assert comparison["candidate"]["query_plan"][0]["entry_id"] == "2"
    assert comparison["metrics"]["bytes_processed"] == {
        "baseline": 100,
        "candidate": 150,
        "absolute_delta": 50,
        "percent_change": 50.0,
    }
    assert comparison["metrics"]["slot_milliseconds"]["absolute_delta"] == -100
    assert comparison["metrics"]["stage_records_read_sum"]["absolute_delta"] == 15
    assert (
        comparison["metrics"]["stage_shuffle_output_bytes_sum"]["absolute_delta"] == -10
    )


def test_compare_query_jobs_uses_duration_milliseconds() -> None:
    start = datetime(2026, 8, 25, tzinfo=UTC)
    baseline = SimpleNamespace(
        job_id="before",
        project="project",
        location="US",
        state="DONE",
        error_result=None,
        job_type="query",
        query="SELECT 1",
        total_bytes_processed=1,
        slot_millis=1,
        cache_hit=False,
        started=start,
        ended=start + timedelta(milliseconds=100),
        query_plan=[],
    )
    candidate = SimpleNamespace(
        job_id="after",
        project="project",
        location="US",
        state="DONE",
        error_result=None,
        job_type="query",
        query="SELECT 1",
        total_bytes_processed=1,
        slot_millis=1,
        cache_hit=False,
        started=start,
        ended=start + timedelta(milliseconds=250),
        query_plan=[],
    )

    comparison = compare_query_jobs(baseline, candidate)

    assert comparison["metrics"]["duration_milliseconds"] == {
        "baseline": 100,
        "candidate": 250,
        "absolute_delta": 150,
        "percent_change": 150.0,
    }


def test_compare_query_jobs_keeps_missing_metrics_null_and_zero_baseline_percent_null() -> (
    None
):
    empty_plan = SimpleNamespace(
        job_id="before",
        project="project",
        location=None,
        state="DONE",
        error_result=None,
        job_type="query",
        query="SELECT 1",
        total_bytes_processed=0,
        slot_millis=None,
        cache_hit=None,
        started=None,
        ended=None,
        query_plan=[],
    )
    missing_metrics = SimpleNamespace(
        job_id="after",
        project="project",
        location=None,
        state="DONE",
        error_result=None,
        job_type="query",
        query="SELECT 1",
        total_bytes_processed=None,
        slot_millis=10,
        cache_hit=None,
        started=None,
        ended=None,
        query_plan=[
            SimpleNamespace(
                entry_id="1",
                name="READ",
                status="DONE",
                input_stages=[],
                records_read=None,
                records_written=None,
                shuffle_output_bytes=None,
                slot_ms=None,
            )
        ],
    )

    comparison = compare_query_jobs(empty_plan, missing_metrics)

    assert comparison["metrics"]["bytes_processed"] == {
        "baseline": 0,
        "candidate": None,
        "absolute_delta": None,
        "percent_change": None,
    }
    assert comparison["metrics"]["slot_milliseconds"]["percent_change"] is None
    assert comparison["metrics"]["stage_count"] == {
        "baseline": 0,
        "candidate": 1,
        "absolute_delta": 1,
        "percent_change": None,
    }
    assert comparison["metrics"]["stage_records_read_sum"]["baseline"] == 0
    assert comparison["metrics"]["stage_records_read_sum"]["candidate"] is None
    assert query_job_summary(empty_plan)["query_plan"] == []


def test_query_job_summary_preserves_all_public_stage_evidence() -> None:
    start = datetime(2026, 8, 25, tzinfo=UTC)
    step = SimpleNamespace(kind="READ", substeps=["$1:project.table"])
    stage = SimpleNamespace(
        entry_id="1",
        name="READ",
        status="COMPLETE",
        start=start,
        end=start + timedelta(milliseconds=50),
        input_stages=[0],
        parallel_inputs=10,
        completed_parallel_inputs=9,
        wait_ms_avg=1,
        wait_ms_max=2,
        wait_ratio_avg=0.1,
        wait_ratio_max=0.2,
        read_ms_avg=3,
        read_ms_max=4,
        read_ratio_avg=0.3,
        read_ratio_max=0.4,
        compute_ms_avg=5,
        compute_ms_max=6,
        compute_ratio_avg=0.5,
        compute_ratio_max=0.6,
        write_ms_avg=7,
        write_ms_max=8,
        write_ratio_avg=0.7,
        write_ratio_max=0.8,
        records_read=11,
        records_written=12,
        shuffle_output_bytes=13,
        shuffle_output_bytes_spilled=14,
        slot_ms=15,
        steps=[step],
    )
    job = SimpleNamespace(
        job_id="job",
        project="project",
        location="US",
        state="DONE",
        error_result=None,
        query="SELECT 1",
        cache_hit=False,
        total_bytes_processed=16,
        slot_millis=17,
        started=start,
        ended=start + timedelta(milliseconds=100),
        query_plan=[stage],
    )

    summary = query_job_summary(job)

    assert summary["query_plan"] == [
        {
            "entry_id": "1",
            "name": "READ",
            "status": "COMPLETE",
            "start": "2026-08-25T00:00:00+00:00",
            "end": "2026-08-25T00:00:00.050000+00:00",
            "input_stages": [0],
            "parallel_inputs": 10,
            "completed_parallel_inputs": 9,
            "wait_ms_avg": 1,
            "wait_ms_max": 2,
            "wait_ratio_avg": 0.1,
            "wait_ratio_max": 0.2,
            "read_ms_avg": 3,
            "read_ms_max": 4,
            "read_ratio_avg": 0.3,
            "read_ratio_max": 0.4,
            "compute_ms_avg": 5,
            "compute_ms_max": 6,
            "compute_ratio_avg": 0.5,
            "compute_ratio_max": 0.6,
            "write_ms_avg": 7,
            "write_ms_max": 8,
            "write_ratio_avg": 0.7,
            "write_ratio_max": 0.8,
            "records_read": 11,
            "records_written": 12,
            "shuffle_output_bytes": 13,
            "shuffle_output_bytes_spilled": 14,
            "slot_ms": 15,
            "steps": [{"kind": "READ", "substeps": ["$1:project.table"]}],
        }
    ]


def test_query_job_summary_keeps_unavailable_plan_metrics_null() -> None:
    job = SimpleNamespace(
        job_id="running",
        project="project",
        location="US",
        state="RUNNING",
        error_result=None,
        query="SELECT 1",
        cache_hit=None,
        total_bytes_processed=None,
        slot_millis=None,
        started=None,
        ended=None,
        query_plan=None,
    )

    summary = query_job_summary(job)

    assert summary["query_plan"] is None
    assert summary["metrics"]["stage_count"] is None
    assert summary["metrics"]["stage_records_read_sum"] is None
    assert summary["metrics"]["stage_shuffle_output_bytes_sum"] is None


def test_current_project_handles_missing_gcloud(monkeypatch) -> None:
    def missing(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr("bqutil.gcp.subprocess.run", missing)
    assert current_project() is None
