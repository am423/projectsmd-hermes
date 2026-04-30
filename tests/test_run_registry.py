"""Tests for run registry."""
from __future__ import annotations

import tempfile
from pathlib import Path


from projectsmd_dashboard.run_registry import RunRegistry


def test_create_and_get_run():
    with tempfile.TemporaryDirectory() as tmp:
        reg = RunRegistry(Path(tmp) / "runs.db")
        run = reg.create_run("r1", "p1", "Implement auth")
        assert run.status == "running"
        fetched = reg.get_run("r1")
        assert fetched is not None
        assert fetched.prompt == "Implement auth"


def test_update_status():
    with tempfile.TemporaryDirectory() as tmp:
        reg = RunRegistry(Path(tmp) / "runs.db")
        reg.create_run("r1", "p1", "x")
        reg.update_status("r1", "completed")
        run = reg.get_run("r1")
        assert run.status == "completed"


def test_events():
    with tempfile.TemporaryDirectory() as tmp:
        reg = RunRegistry(Path(tmp) / "runs.db")
        reg.create_run("r1", "p1", "x")
        reg.append_event("r1", "stdout", "line1")
        reg.append_event("r1", "stderr", "err1")
        events = reg.get_events("r1")
        assert len(events) == 2
        assert events[0].line == "line1"
        assert events[1].stream == "stderr"


def test_list_runs_by_project():
    with tempfile.TemporaryDirectory() as tmp:
        reg = RunRegistry(Path(tmp) / "runs.db")
        reg.create_run("r1", "p1", "a")
        reg.create_run("r2", "p2", "b")
        assert len(reg.list_runs(project_id="p1")) == 1
        assert len(reg.list_runs()) == 2
