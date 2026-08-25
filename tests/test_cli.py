"""Command-level compatibility and output-contract tests."""

from types import SimpleNamespace

from click.testing import CliRunner

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
    assert (
        "analyze --last --format json"
        in runner.invoke(main, ["analyze", "--help"]).output
    )
    assert "config --set-project" in runner.invoke(main, ["config", "--help"]).output


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


def test_missing_gcloud_returns_actionable_usage_error(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setattr("bqutil.cli.current_project", lambda: None)
    result = CliRunner().invoke(main, ["analyze", "job"])
    assert result.exit_code != 0
    assert "Pass --project" in result.output


def test_analyze_json_llm_and_query_analyze_are_json_safe(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    job = query_job()
    monkeypatch.setattr("bqutil.cli.get_job", lambda project, job_id: job)
    runner = CliRunner()
    for args in (
        ["analyze", "project:job", "--format", "json"],
        ["analyze", "project:job", "--llm"],
    ):
        result = runner.invoke(main, args)
        assert result.exit_code == 0, result.output
        assert '"entry_id": "1"' in result.output
    sql = tmp_path / "query.sql"
    sql.write_text("SELECT 1")
    monkeypatch.setattr("bqutil.cli.client", lambda project: object())
    monkeypatch.setattr("bqutil.cli.run_query", lambda sql, client: (job, 0.1))
    monkeypatch.setattr("bqutil.cli.preview_rows", lambda job, limit: [])
    result = runner.invoke(
        main, ["query", str(sql), "--project", "project", "--analyze"]
    )
    assert result.exit_code == 0, result.output
    assert '"entry_id": "1"' in result.output


def test_analyze_verbose_and_debug_render_stable_details(monkeypatch) -> None:
    job = query_job()
    monkeypatch.setattr("bqutil.cli.get_job", lambda project, job_id: job)
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
