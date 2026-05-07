"""Tests for update queue."""
from __future__ import annotations

import tempfile
from pathlib import Path


from projectsmd_dashboard.update_queue import (
    approve_update,
    enqueue_update,
    list_pending,
    reject_update,
)


def test_enqueue_and_list(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "queue.json"
        monkeypatch.setattr("projectsmd_dashboard.update_queue._queue_path", lambda: path)
        u = enqueue_update("/tmp/project.md", "new content", "+line", meta={"created_by": "agent", "reason": "test", "run_id": "r1", "assignment_id": "a1"})
        assert u.status == "pending"
        assert u.created_by == "agent"
        assert u.reason == "test"
        assert u.run_id == "r1"
        assert u.assignment_id == "a1"
        pending = list_pending()
        assert len(pending) == 1
        assert pending[0].project_path == "/tmp/project.md"


def test_approve_and_reject(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "queue.json"
        monkeypatch.setattr("projectsmd_dashboard.update_queue._queue_path", lambda: path)
        u = enqueue_update("/tmp/project.md", "x", "diff")
        approved = approve_update(u.id, comment="looks good")
        assert approved is not None
        assert approved.status == "approved"
        assert approved.reviewed_at
        assert approved.review_comment == "looks good"
        assert len(list_pending()) == 0

        u2 = enqueue_update("/tmp/project.md", "y", "diff2")
        rejected = reject_update(u2.id, comment="nope")
        assert rejected is not None
        assert rejected.status == "rejected"
        assert rejected.review_comment == "nope"


def test_list_pending_filters_by_project(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "queue.json"
        monkeypatch.setattr("projectsmd_dashboard.update_queue._queue_path", lambda: path)
        enqueue_update("/tmp/a.md", "x", "d")
        enqueue_update("/tmp/b.md", "y", "d")
        assert len(list_pending("/tmp/a.md")) == 1


def test_approve_endpoint_snapshots_before_write(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from projectsmd_dashboard.api import router

    with tempfile.TemporaryDirectory() as tmp:
        queue_path = Path(tmp) / "queue.json"
        monkeypatch.setattr("projectsmd_dashboard.update_queue._queue_path", lambda: queue_path)
        monkeypatch.setattr("projectsmd_dashboard.api.approve_update", approve_update)
        project_md = Path(tmp) / "project.md"
        project_md.write_text("---\nproject: Demo\n---\n\n## Current State\n\n**Phase:** build\n", encoding="utf-8")
        update = enqueue_update(str(project_md), "---\nproject: Demo\n---\n\n## Current State\n\n**Phase:** verify\n", "diff")
        app = FastAPI()
        app.include_router(router, prefix="/api/plugins/projectsmd")
        response = TestClient(app).post(f"/api/plugins/projectsmd/projects/demo/queue/{update.id}/approve", json={"comment": "ok"})
        assert response.status_code == 200
        data = response.json()
        assert Path(data["snapshot"]).exists()
        assert "verify" in project_md.read_text(encoding="utf-8")
        assert data["update"]["review_comment"] == "ok"
