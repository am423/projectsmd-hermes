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


def validate_roots(roots: list[str | Path]) -> list[dict[str, Any]]:
    """Return UI-friendly validation status for configured project roots."""
    statuses: list[dict[str, Any]] = []
    ignored = set(default_config()["ignored_dirs"])
    for raw in roots:
        path = Path(raw).expanduser()
        status: dict[str, Any] = {"path": str(path), "ok": False, "reason": "", "project_count": 0}
        if not path.exists():
            status["reason"] = "not_found"
        elif not path.is_dir():
            status["reason"] = "not_directory"
        elif not os.access(path, os.R_OK):
            status["reason"] = "not_readable"
        else:
            count = 0
            for project_md in path.rglob("project.md"):
                if any(part in ignored for part in project_md.parts):
                    continue
                count += 1
            status.update({"ok": True, "reason": "ok", "project_count": count})
        statuses.append(status)
    return statuses


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
        "favorites": [],
        "recent_project_paths": [],
        "sort": "updated_desc",
        "filters": {"query": "", "phase": "", "blocked": False, "owner": "", "tag": ""},
    }
