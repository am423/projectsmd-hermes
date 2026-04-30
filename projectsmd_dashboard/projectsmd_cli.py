"""Safe wrapper around the projectsmd CLI for dashboard use.

Only allowlisted commands are permitted. No arbitrary shell.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from .locks import project_lock

ALLOWED_COMMANDS = {
    "validate",
    "status",
    "next",
    "task",
    "decide",
    "discover",
    "session",
    "phase",
    "archive",
}


def _projectsmd_path() -> str:
    path = shutil.which("projectsmd")
    if not path:
        raise RuntimeError("projectsmd binary not found in PATH")
    return path


def _run(cmd: list[str], cwd: str | None = None) -> dict[str, Any]:
    try:
        result = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            timeout=30,
            cwd=cwd,
        )
        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "returncode": -1, "stdout": "", "stderr": "Command timed out"}
    except Exception as exc:
        return {"ok": False, "returncode": -1, "stdout": "", "stderr": str(exc)}


def _with_file(cmd: list[str], project_md: str | Path) -> list[str]:
    # projectsmd global flag: -f/--file must come BEFORE the subcommand
    return [cmd[0], "-f", str(project_md)] + cmd[1:]


def validate(project_md: str | Path) -> dict[str, Any]:
    with project_lock(project_md):
        return _run(_with_file([_projectsmd_path(), "validate"], project_md))


def status(project_md: str | Path) -> dict[str, Any]:
    with project_lock(project_md):
        return _run(_with_file([_projectsmd_path(), "status"], project_md))


def next_action(project_md: str | Path) -> dict[str, Any]:
    with project_lock(project_md):
        return _run(_with_file([_projectsmd_path(), "next"], project_md))


def task_add(project_md: str | Path, title: str, phase: str | None = None) -> dict[str, Any]:
    cmd = [_projectsmd_path(), "task", "add", title]
    if phase:
        cmd += ["--phase", phase]
    with project_lock(project_md):
        return _run(_with_file(cmd, project_md))


def task_done(project_md: str | Path, task_id: int) -> dict[str, Any]:
    with project_lock(project_md):
        return _run(_with_file([_projectsmd_path(), "task", "done", str(task_id)], project_md))


def task_block(project_md: str | Path, task_id: int, reason: str) -> dict[str, Any]:
    with project_lock(project_md):
        return _run(_with_file([_projectsmd_path(), "task", "block", str(task_id), "--reason", reason], project_md))


def task_unblock(project_md: str | Path, task_id: int) -> dict[str, Any]:
    with project_lock(project_md):
        return _run(_with_file([_projectsmd_path(), "task", "unblock", str(task_id)], project_md))


def decide(project_md: str | Path, decision: str, rationale: str | None = None) -> dict[str, Any]:
    cmd = [_projectsmd_path(), "decide", decision]
    if rationale:
        cmd += ["--rationale", rationale]
    with project_lock(project_md):
        return _run(_with_file(cmd, project_md))


def discover(project_md: str | Path, text: str) -> dict[str, Any]:
    with project_lock(project_md):
        return _run(_with_file([_projectsmd_path(), "discover", text], project_md))


def session_summary(project_md: str | Path, summary: str) -> dict[str, Any]:
    with project_lock(project_md):
        return _run(_with_file([_projectsmd_path(), "session", "--non-interactive", "--summary", summary], project_md))


def phase_transition(project_md: str | Path, phase: str) -> dict[str, Any]:
    with project_lock(project_md):
        return _run(_with_file([_projectsmd_path(), "phase", "--transition", phase], project_md))


def archive(project_md: str | Path, summary: str | None = None) -> dict[str, Any]:
    cmd = [_projectsmd_path(), "archive"]
    if summary:
        cmd += ["--summary", summary]
    with project_lock(project_md):
        return _run(_with_file(cmd, project_md))


def init(root: str | Path, **kwargs) -> dict[str, Any]:
    root_path = Path(root).expanduser().resolve()
    project_md = root_path / "project.md"
    if project_md.exists():
        return {"ok": False, "returncode": -1, "stdout": "", "stderr": "project.md already exists"}

    cmd = [
        _projectsmd_path(),
        "init",
        "--name", kwargs.get("name", "Untitled"),
        "--owner", kwargs.get("owner", ""),
        "--description", kwargs.get("description", ""),
        "--core-value", kwargs.get("core_value", ""),
    ]
    if kwargs.get("agent"):
        cmd += ["--agent", kwargs["agent"]]
    if kwargs.get("tags"):
        cmd += ["--tags", kwargs["tags"]]
    if kwargs.get("brownfield"):
        cmd += ["--brownfield"]

    return _run(cmd, cwd=str(root_path))
