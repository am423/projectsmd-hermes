"""Plugin configuration for ProjectsMD dashboard.

Config lives at ~/.hermes/projectsmd/config.json.
Profile-safe: respects HERMES_HOME if set.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def _config_dir() -> Path:
    home = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
    return home / "projectsmd"


def _config_path() -> Path:
    return _config_dir() / "config.json"


def load_config() -> dict[str, Any]:
    path = _config_path()
    if not path.exists():
        return default_config()
    return json.loads(path.read_text(encoding="utf-8"))


def save_config(config: dict[str, Any]) -> None:
    _config_dir().mkdir(parents=True, exist_ok=True)
    _config_path().write_text(json.dumps(config, indent=2), encoding="utf-8")


def default_config() -> dict[str, Any]:
    return {
        "project_roots": [
            str(Path.home() / "projects"),
            str(Path.home() / "projectsmd-hermes"),
            str(Path.cwd()),
        ],
        "ignored_dirs": [".git", "target", "node_modules", ".venv", "__pycache__"],
        "default_owner": "",
        "default_agent": "Hermes",
        "auto_validate": True,
        "max_scan_depth": 6,
    }
