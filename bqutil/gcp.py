"""Google Cloud adapter."""

from __future__ import annotations

import subprocess
from typing import Any

from google.cloud import bigquery


def client(project: str) -> bigquery.Client:
    """Create the one concrete BigQuery adapter used by the CLI."""
    return bigquery.Client(project=project)


def current_project() -> str | None:
    """Return gcloud's configured project, if gcloud is installed and configured."""
    try:
        result = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None


def get_job(project: str, job_id: str, location: str | None = None) -> Any:
    """Fetch a BigQuery job by ID, optionally from its execution location."""
    return client(project).get_job(job_id, project=project, location=location)
