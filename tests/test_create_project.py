"""Tests for project creation API."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from fastapi.testclient import TestClient

from projectsmd_dashboard.api import router

from fastapi import FastAPI

app = FastAPI()
app.include_router(router, prefix="/api/plugins/projectsmd")
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
