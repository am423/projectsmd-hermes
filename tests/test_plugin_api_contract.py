"""FastAPI contract tests for the ProjectsMD dashboard plugin API.

These tests mount the router under a real FastAPI app so we can use
TestClient and verify routes, status codes, and response shapes.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from projectsmd_dashboard.api import router

app = FastAPI()
app.include_router(router, prefix="/api/plugins/projectsmd")
client = TestClient(app)


class TestHealth:
    def test_health_ok(self):
        response = client.get("/api/plugins/projectsmd/health")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["plugin"] == "projectsmd"
        assert data["label"] == "Projects"
        assert "projectsmd" in data
        assert "tmux" in data
        assert "hermes" in data
        assert "roots" in data

    def test_health_no_double_prefix(self):
        response = client.get("/api/plugins/projectsmd/health")
        assert response.status_code == 200


class TestProjects:
    def test_projects_returns_list(self):
        response = client.get("/api/plugins/projectsmd/projects")
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        assert "roots" in data
        assert isinstance(data["projects"], list)


class TestProjectDetail:
    def test_detail_404_for_missing(self):
        response = client.get("/api/plugins/projectsmd/projects/detail", params={"path": "/nonexistent/project.md"})
        assert response.status_code == 404

    def test_detail_reads_valid_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp) / "demo"
            project_dir.mkdir()
            path = project_dir / "project.md"
            path.write_text(
                """---
project: Demo
status: build
created: 2026-04-30
updated: 2026-04-30
owner: Adam
---

## Current State

**Phase:** build
**Next action:** Ship the dashboard tab
**Blockers:** None

## Tasks

### Phase: BUILD

- [x] Scaffold plugin
- [ ] Render project list
""",
                encoding="utf-8",
            )
            response = client.get("/api/plugins/projectsmd/projects/detail", params={"path": str(path)})
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Demo"
            assert data["phase"] == "build"
            assert data["next_action"] == "Ship the dashboard tab"
            assert data["tasks"]["done"] == 1
            assert data["tasks"]["pending"] == 1

    def test_detail_resolves_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp) / "demo"
            project_dir.mkdir()
            (project_dir / "project.md").write_text(
                "---\nproject: DirDemo\n---\n\n## Current State\n\n**Phase:** define\n",
                encoding="utf-8",
            )
            response = client.get("/api/plugins/projectsmd/projects/detail", params={"path": str(project_dir)})
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "DirDemo"
