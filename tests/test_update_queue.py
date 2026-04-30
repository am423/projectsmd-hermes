"""Tests for update queue."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from projectsmd_dashboard.update_queue import (
    PendingUpdate,
    _queue_path,
    approve_update,
    enqueue_update,
    list_pending,
    reject_update,
)


def test_enqueue_and_list(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "queue.json"
        monkeypatch.setattr("projectsmd_dashboard.update_queue._queue_path", lambda: path)
        u = enqueue_update("/tmp/project.md", "new content", "+line")
        assert u.status == "pending"
        pending = list_pending()
        assert len(pending) == 1
        assert pending[0].project_path == "/tmp/project.md"


def test_approve_and_reject(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "queue.json"
        monkeypatch.setattr("projectsmd_dashboard.update_queue._queue_path", lambda: path)
        u = enqueue_update("/tmp/project.md", "x", "diff")
        approved = approve_update(u.id)
        assert approved is not None
        assert approved.status == "approved"
        assert len(list_pending()) == 0

        u2 = enqueue_update("/tmp/project.md", "y", "diff2")
        rejected = reject_update(u2.id)
        assert rejected is not None
        assert rejected.status == "rejected"


def test_list_pending_filters_by_project(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "queue.json"
        monkeypatch.setattr("projectsmd_dashboard.update_queue._queue_path", lambda: path)
        enqueue_update("/tmp/a.md", "x", "d")
        enqueue_update("/tmp/b.md", "y", "d")
        assert len(list_pending("/tmp/a.md")) == 1
