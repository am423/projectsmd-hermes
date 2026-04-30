"""Tests for CLI wrapper and locks."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path


from projectsmd_dashboard.locks import project_lock
from projectsmd_dashboard.projectsmd_cli import init, task_add, validate


class TestLocks:
    def test_lock_acquired_and_released(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test")
        try:
            with project_lock(tmp.name):
                assert True
        finally:
            os.unlink(tmp.name)

    def test_lock_blocks_concurrent(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test")
        acquired = []
        try:
            with project_lock(tmp.name, timeout=0.5):
                acquired.append("first")
                try:
                    with project_lock(tmp.name, timeout=0.1):
                        acquired.append("second")
                except TimeoutError:
                    acquired.append("timeout")
        finally:
            os.unlink(tmp.name)
        assert acquired == ["first", "timeout"]


class TestProjectsmdCLI:
    def test_init_creates_project_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = init(
                root=tmp,
                name="Test Project",
                owner="Adam",
                description="A test project.",
                core_value="Make testing easy.",
            )
            assert result["ok"] is True
            project_md = Path(tmp) / "project.md"
            assert project_md.exists()
            text = project_md.read_text()
            assert "Test Project" in text

    def test_init_refuses_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "project.md").write_text("---\nproject: Existing\n---\n")
            result = init(root=tmp, name="New", owner="Adam", description="x", core_value="y")
            assert result["ok"] is False

    def test_task_add_and_validate(self):
        with tempfile.TemporaryDirectory() as tmp:
            init(root=tmp, name="TaskTest", owner="Adam", description="x", core_value="y")
            project_md = Path(tmp) / "project.md"
            result = task_add(project_md, "Implement auth", phase="build")
            assert result["ok"] is True
            val = validate(project_md)
            assert val["ok"] is True
            assert "Implement auth" in val["stdout"] or "Implement auth" in project_md.read_text()
