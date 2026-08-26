"""Command-level compatibility and output-contract tests."""

import json
from types import SimpleNamespace

from click.testing import CliRunner
from google.api_core.exceptions import GoogleAPICallError
from google.auth.exceptions import GoogleAuthError

from bqutil.cli import main, resolve_project
from bqutil.config import load_config


def query_job() -> SimpleNamespace:
    stage = SimpleNamespace(
        entry_id="1",
        name="READ",
        status="COMPLETE",
        input_stages=[],
        records_read=4,
        records_written=2,
        shuffle_output_bytes=3,
        slot_ms=80,
    )
    return SimpleNamespace(
        job_id="job",
        project="project",
        location="US",
        state="DONE",
        error_result=None,
        job_type="query",
        query="SELECT 1",
        total_bytes_processed=1024,
        total_bytes_billed=1024,
        slot_millis=100,
        cache_hit=False,
        query_plan=[stage],
        created=None,
        started=None,
        ended=None,
        user_email="test@example.com",
        destination=None,
    )


def test_version_and_command_examples() -> None:
    runner = CliRunner()
    assert "0.1.0" in runner.invoke(main, ["--version"]).output
    assert "--dry-run" in runner.invoke(main, ["query", "--help"]).output
    analyze_help = runner.invoke(main, ["analyze", "--help"]).output
    assert "--location LOCATION" in analyze_help
    assert "analyze --last" in analyze_help
    assert "config --set-project" in runner.invoke(main, ["config", "--help"]).output


def test_root_help_includes_agent_comparison_workflow() -> None:
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "Agent workflow" in result.output
    assert "query candidate.sql --project PROJECT --dry-run" in result.output
    assert (
        "compare BASELINE_JOB CANDIDATE_JOB --project PROJECT --format json"
        in result.output
    )


def test_config_round_trip(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    runner = CliRunner()
    assert (
        runner.invoke(main, ["config", "--set-project", "test-project"]).exit_code == 0
    )
    assert load_config()["default_project"] == "test-project"
    assert (
        '"default_project": "test-project"'
        in runner.invoke(main, ["config", "--show"]).output
    )


def test_analyze_passes_explicit_location_with_project_qualified_job(
    monkeypatch,
) -> None:
    job = query_job()
    captured: dict[str, str | None] = {}

    def fetch(project: str, job_id: str, location: str | None) -> SimpleNamespace:
        captured.update(project=project, job_id=job_id, location=location)
        return job

    monkeypatch.setattr("bqutil.cli.get_job", fetch)
    result = CliRunner().invoke(
        main,
        [
            "analyze",
            "project:job",
            "--location",
            "asia-northeast1",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0, result.output
    assert captured == {
        "project": "project",
        "job_id": "job",
        "location": "asia-northeast1",
    }


def test_analyze_last_uses_saved_location_and_old_config_defaults_to_none(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    config_path = tmp_path / "bqutil" / "config.json"
    config_path.parent.mkdir()
    config_path.write_text('{"last_job_id": "old-job", "last_job_project": "project"}')
    assert load_config()["last_job_location"] is None

    captured: dict[str, str | None] = {}
    monkeypatch.setattr(
        "bqutil.cli.get_job",
        lambda project, job_id, location: (
            captured.update(project=project, job_id=job_id, location=location)
            or query_job()
        ),
    )
    result = CliRunner().invoke(main, ["analyze", "--last", "--format", "json"])

    assert result.exit_code == 0, result.output
    assert captured["location"] is None


def test_analyze_last_reuses_persisted_location(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    config_path = tmp_path / "bqutil" / "config.json"
    config_path.parent.mkdir()
    config_path.write_text(
        '{"last_job_id": "job", "last_job_project": "project", '
        '"last_job_location": "asia-northeast1"}'
    )
    captured: dict[str, str | None] = {}
    monkeypatch.setattr(
        "bqutil.cli.get_job",
        lambda project, job_id, location: (
            captured.update(project=project, job_id=job_id, location=location)
            or query_job()
        ),
    )

    result = CliRunner().invoke(main, ["analyze", "--last", "--format", "json"])

    assert result.exit_code == 0, result.output
    assert captured["location"] == "asia-northeast1"


def test_compare_json_is_one_parseable_document_and_uses_project_location_precedence(
    monkeypatch,
) -> None:
    baseline = query_job()
    baseline.job_id = "before"
    candidate = query_job()
    candidate.job_id = "after"
    candidate.total_bytes_processed = 2048
    captured: list[tuple[str, str, str | None]] = []

    def fetch(project: str, job_id: str, location: str | None) -> SimpleNamespace:
        captured.append((project, job_id, location))
        return baseline if job_id == "before" else candidate

    monkeypatch.setattr("bqutil.cli.get_job", fetch)
    result = CliRunner().invoke(
        main,
        [
            "compare",
            "qualified-project:before",
            "after",
            "--project",
            "shared-project",
            "--candidate-project",
            "candidate-project",
            "--location",
            "US",
            "--candidate-location",
            "asia-northeast1",
        ],
    )

    assert result.exit_code == 0, result.output
    assert result.stderr == ""
    assert captured == [
        ("qualified-project", "before", "US"),
        ("candidate-project", "after", "asia-northeast1"),
    ]
    payload = json.loads(result.stdout)
    assert payload["semantics"] == "candidate_minus_baseline"
    assert payload["baseline"]["cache_hit"] is False
    assert payload["candidate"]["cache_hit"] is False
    assert payload["baseline"]["query_plan"][0]["entry_id"] == "1"
    assert payload["candidate"]["query_plan"][0]["entry_id"] == "1"
    assert payload["metrics"]["bytes_processed"]["absolute_delta"] == 1024


def test_compare_baseline_fetch_failure_is_actionable_without_traceback(
    monkeypatch,
) -> None:
    def fail_baseline(
        project: str, job_id: str, location: str | None
    ) -> SimpleNamespace:
        raise GoogleAPICallError("baseline denied")

    monkeypatch.setattr("bqutil.cli.get_job", fail_baseline)

    result = CliRunner().invoke(
        main, ["compare", "project:before", "project:after", "--format", "json"]
    )

    assert result.exit_code != 0
    assert "Unable to fetch baseline job 'before' in project 'project'" in result.output
    assert "Check the job ID, location, and BigQuery permissions" in result.output
    assert "Traceback" not in result.output


def test_compare_candidate_fetch_failure_is_actionable_without_traceback(
    monkeypatch,
) -> None:
    baseline = query_job()

    def fail_candidate(
        project: str, job_id: str, location: str | None
    ) -> SimpleNamespace:
        if job_id == "before":
            return baseline
        raise GoogleAPICallError("candidate denied")

    monkeypatch.setattr("bqutil.cli.get_job", fail_candidate)

    result = CliRunner().invoke(
        main,
        [
            "compare",
            "project:before",
            "project:after",
            "--location",
            "US",
            "--format",
            "json",
        ],
    )

    assert result.exit_code != 0
    assert (
        "Unable to fetch candidate job 'after' in project 'project' at location 'US'"
        in result.output
    )
    assert "Check the job ID, location, and BigQuery permissions" in result.output
    assert "Traceback" not in result.output


def test_compare_baseline_auth_failure_is_actionable_without_traceback(
    monkeypatch,
) -> None:
    def fail_baseline(
        project: str, job_id: str, location: str | None
    ) -> SimpleNamespace:
        raise GoogleAuthError("credentials need refresh")

    monkeypatch.setattr("bqutil.cli.get_job", fail_baseline)

    result = CliRunner().invoke(
        main, ["compare", "project:before", "project:after", "--format", "json"]
    )

    assert result.exit_code != 0
    assert "Unable to fetch baseline job 'before' in project 'project'" in result.output
    assert "Check the job ID, location, and BigQuery permissions" in result.output
    assert "Traceback" not in result.output


def test_compare_candidate_auth_failure_is_actionable_without_traceback(
    monkeypatch,
) -> None:
    baseline = query_job()

    def fail_candidate(
        project: str, job_id: str, location: str | None
    ) -> SimpleNamespace:
        if job_id == "before":
            return baseline
        raise GoogleAuthError("credentials need refresh")

    monkeypatch.setattr("bqutil.cli.get_job", fail_candidate)

    result = CliRunner().invoke(
        main, ["compare", "project:before", "project:after", "--format", "json"]
    )

    assert result.exit_code != 0
    assert "Unable to fetch candidate job 'after' in project 'project'" in result.output
    assert "Check the job ID, location, and BigQuery permissions" in result.output
    assert "Traceback" not in result.output


def test_compare_text_explains_candidate_minus_baseline(monkeypatch) -> None:
    baseline = query_job()
    candidate = query_job()
    candidate.total_bytes_processed = 512
    monkeypatch.setattr(
        "bqutil.cli.get_job",
        lambda project, job_id, location: baseline if job_id == "before" else candidate,
    )

    result = CliRunner().invoke(
        main, ["compare", "project:before", "project:after", "--format", "text"]
    )

    assert result.exit_code == 0, result.output
    assert "candidate minus baseline" in result.output.lower()
    assert "bytes processed" in result.output.lower()
    assert "B" in result.output


def test_compare_rejects_non_query_jobs(monkeypatch) -> None:
    job = query_job()
    job.job_type = "load"
    monkeypatch.setattr("bqutil.cli.get_job", lambda project, job_id, location: job)

    result = CliRunner().invoke(main, ["compare", "project:before", "project:after"])

    assert result.exit_code != 0
    assert "only supports query jobs" in result.output


def test_missing_gcloud_returns_actionable_usage_error(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setattr("bqutil.cli.current_project", lambda: None)
    result = CliRunner().invoke(main, ["analyze", "job"])
    assert result.exit_code != 0
    assert "Pass --project" in result.output


def test_analyze_json_and_llm_are_json_safe(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    job = query_job()
    monkeypatch.setattr("bqutil.cli.get_job", lambda project, job_id, location: job)
    runner = CliRunner()
    for args in (
        ["analyze", "project:job", "--format", "json"],
        ["analyze", "project:job", "--llm"],
    ):
        result = runner.invoke(main, args)
        assert result.exit_code == 0, result.output
        assert '"entry_id": "1"' in result.output


def test_query_analyze_writes_one_json_document_to_stdout(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    sql = tmp_path / "query.sql"
    sql.write_text("SELECT 1")
    job = query_job()
    monkeypatch.setattr("bqutil.cli.client", lambda project: object())
    monkeypatch.setattr("bqutil.cli.run_query", lambda sql, client: (job, 0.1))
    monkeypatch.setattr("bqutil.cli.preview_rows", lambda job, limit: [])

    result = CliRunner().invoke(
        main, ["query", str(sql), "--project", "project", "--analyze"]
    )

    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["job_id"] == "job"
    assert "Job ID: job" in result.stderr


def test_analyze_verbose_and_debug_render_stable_details(monkeypatch) -> None:
    job = query_job()
    monkeypatch.setattr("bqutil.cli.get_job", lambda project, job_id, location: job)
    result = CliRunner().invoke(
        main, ["analyze", "project:job", "--verbose", "--debug"]
    )
    assert result.exit_code == 0
    assert "Query-plan stages: 1; bottlenecks: 3" in result.output
    assert '"user_email": "test@example.com"' in result.output


def test_dry_run_never_persists_or_executes(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    sql = tmp_path / "query.sql"
    sql.write_text("SELECT 1")
    dry_job = SimpleNamespace(total_bytes_processed=2048)
    fake_client = object()
    monkeypatch.setattr("bqutil.cli.client", lambda project: fake_client)
    monkeypatch.setattr("bqutil.cli.dry_run_query", lambda query, client: dry_job)
    monkeypatch.setattr(
        "bqutil.cli.run_query",
        lambda *args: (_ for _ in ()).throw(AssertionError("submitted")),
    )
    result = CliRunner().invoke(
        main, ["query", str(sql), "--project", "project", "--dry-run"]
    )
    assert result.exit_code == 0, result.output
    assert '"dry_run": true' in result.output
    assert load_config()["last_job_id"] is None
    rejected = CliRunner().invoke(
        main, ["query", str(sql), "--project", "project", "--dry-run", "--analyze"]
    )
    assert rejected.exit_code != 0
    assert "cannot be combined" in rejected.output


def test_dry_run_conflicts_precede_client_creation(monkeypatch, tmp_path) -> None:
    sql = tmp_path / "query.sql"
    sql.write_text("SELECT 1")
    monkeypatch.setattr(
        "bqutil.cli.client",
        lambda project: (_ for _ in ()).throw(AssertionError("client created")),
    )

    result = CliRunner().invoke(
        main,
        [
            "query",
            str(sql),
            "--project",
            "project",
            "--dry-run",
            "--output",
            str(tmp_path / "out.csv"),
        ],
    )

    assert result.exit_code != 0
    assert "--dry-run cannot be combined with --output" in result.output
    assert "client created" not in result.output


def test_query_preprocesses_date_only_macros_before_submission(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    sql = tmp_path / "query.sql"
    sql.write_text("SELECT {{ start_date() }}")
    submitted: dict[str, str] = {}
    monkeypatch.setattr("bqutil.cli.client", lambda project: object())
    monkeypatch.setattr(
        "bqutil.cli.run_query",
        lambda query, client: submitted.update(query=query) or (query_job(), 0.1),
    )
    monkeypatch.setattr("bqutil.cli.preview_rows", lambda job, limit: [])

    result = CliRunner().invoke(main, ["query", str(sql), "--project", "project"])

    assert result.exit_code == 0, result.output
    assert "{{ start_date() }}" not in submitted["query"]


def test_query_persists_before_export_and_previews(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    sql = tmp_path / "query.sql"
    sql.write_text("SELECT 1")
    job = query_job()
    monkeypatch.setattr("bqutil.cli.client", lambda project: object())
    monkeypatch.setattr("bqutil.cli.run_query", lambda sql, client: (job, 0.1))
    monkeypatch.setattr("bqutil.cli.preview_rows", lambda job, limit: [{"value": 1}])
    result = CliRunner().invoke(
        main, ["query", str(sql), "--project", "project", "--preview-rows", "1"]
    )
    assert result.exit_code == 0, result.output
    assert load_config()["last_job_id"] == "job"
    assert load_config()["last_job_location"] == "US"
    assert "Job ID: job" in result.output


def test_query_records_job_before_export_failure(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    sql = tmp_path / "query.sql"
    sql.write_text("SELECT 1")
    job = query_job()
    job.to_dataframe = lambda: (_ for _ in ()).throw(OSError("disk full"))
    monkeypatch.setattr("bqutil.cli.client", lambda project: object())
    monkeypatch.setattr("bqutil.cli.run_query", lambda sql, client: (job, 0.1))
    result = CliRunner().invoke(
        main,
        [
            "query",
            str(sql),
            "--project",
            "project",
            "--output",
            str(tmp_path / "out.csv"),
        ],
    )
    assert result.exit_code != 0
    assert load_config()["last_job_id"] == "job"
    assert "Job ID: job" in result.output


def test_resolve_project_handles_absent_gcloud(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setattr("bqutil.cli.current_project", lambda: None)
    try:
        resolve_project(None)
    except Exception as error:
        assert "Pass --project" in str(error)
    else:
        raise AssertionError("expected usage error")
