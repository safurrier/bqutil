"""Persistent XDG configuration."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = {
    "default_project": None,
    "last_job_id": None,
    "last_job_project": None,
    "last_job_location": None,
}


def config_path() -> Path:
    return (
        Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        / "bqutil"
        / "config.json"
    )


def load_config() -> dict[str, Any]:
    try:
        data = json.loads(config_path().read_text())
    except (OSError, json.JSONDecodeError):
        data = {}
    return {**DEFAULT_CONFIG, **data}


def save_config(config: dict[str, Any]) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({**DEFAULT_CONFIG, **config}, indent=2) + "\n")
