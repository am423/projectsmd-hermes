"""Tests for snapshots."""
from __future__ import annotations

import tempfile
from pathlib import Path

from projectsmd_dashboard.snapshots import list_snapshots, restore_snapshot, snapshot


def test_snapshot_creates_file():
    with tempfile.TemporaryDirectory() as tmp:
        md = Path(tmp) / "project.md"
        md.write_text("hello", encoding="utf-8")
        snap = snapshot(md)
        assert snap.exists()
        assert snap.name.startswith("project.md.")


def test_list_snapshots():
    with tempfile.TemporaryDirectory() as tmp:
        md = Path(tmp) / "project.md"
        md.write_text("v1", encoding="utf-8")
        snapshot(md)
        md.write_text("v2", encoding="utf-8")
        snapshot(md)
        snaps = list_snapshots(md)
        assert len(snaps) == 2


def test_restore_snapshot():
    with tempfile.TemporaryDirectory() as tmp:
        md = Path(tmp) / "project.md"
        md.write_text("original", encoding="utf-8")
        s1 = snapshot(md)
        md.write_text("changed", encoding="utf-8")
        restore_snapshot(md, s1)
        assert md.read_text(encoding="utf-8") == "original"
