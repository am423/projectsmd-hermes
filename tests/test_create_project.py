"""Tests for project creation API."""
from __future__ import annotations

import pytest
import tempfile
from pathlib import Path


from fastapi.testclient import TestClient

from projectsmd_dashboard.api import router
from projectsmd_dashboard.projectsmd_cli import PROJECTSMD_AVAILABLE

from fastapi import FastAPI

app = FastAPI()
app.include_router(router, prefix="/api/plugins/projectsmd")

pytestmark = pytest.mark.skipif(
    not PROJECTSMD_AVAILABLE,
    reason="projectsmd binary not available",
)
client = TestClient(app)


class TestCreateProject:
    def test_create_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            response = client.post("/api/plugins/projectsmd/projects", json={
                "root": tmp,
                "name": "API Test",
                "owner": "Adam",
                "description": "Created from API.",
                "core_value": "Make it work.",
            })
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "API Test"
            assert (Path(tmp) / "project.md").exists()

    def test_create_project_refuses_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "project.md").write_text("---\nproject: Existing\n---\n")
            response = client.post("/api/plugins/projectsmd/projects", json={
                "root": tmp,
                "name": "New",
                "owner": "Adam",
                "description": "x",
                "core_value": "y",
            })
            assert response.status_code == 409

    def test_create_project_requires_root(self):
        response = client.post("/api/plugins/projectsmd/projects", json={
            "name": "NoRoot",
        })
        assert response.status_code == 400
