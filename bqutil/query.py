"""Query preprocessing and execution."""

from __future__ import annotations

import re
import time
from datetime import datetime, timedelta
from typing import Any

from google.cloud import bigquery


def replace_dbt_refs(query: str, project: str) -> str:
    """Apply the legacy, opinionated dbt macro replacements."""
    pattern = r"{{[\s]*ref\(['\"](\w+)['\"](?:,[\s]*['\"](\w+)['\"])?\)[\s]*}}"
    result = re.sub(
        pattern,
        lambda match: f"`{project}.dbt_testing.{match.group(2) or match.group(1)}`",
        query,
    )
    return result.replace(
        "{{ start_date() }}",
        f"'{(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')} 00:00:00'",
    ).replace("{{ end_date() }}", f"'{datetime.now().strftime('%Y-%m-%d')} 00:00:00'")


def run_query(query: str, client: Any) -> tuple[Any, float]:
    """Submit a query and wait for completion."""
    start = time.monotonic()
    job = client.query(query)
    job.result()
    return job, time.monotonic() - start


def dry_run_query(query: str, client: Any) -> Any:
    """Validate and estimate a query without executing it or creating result rows."""
    config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    return client.query(query, job_config=config)


def preview_rows(job: Any, limit: int) -> list[dict[str, Any]]:
    """Return no more than LIMIT result rows as JSON-compatible mappings."""
    return [dict(row.items()) for row in job.result(max_results=limit)]
