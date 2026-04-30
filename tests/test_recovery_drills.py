"""Recovery drills: automated tests for disaster recovery paths.

These are integration-style tests that exercise snapshot restore,
queue reject, gate reset, and other recovery paths end-to-end.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from projectsmd_dashboard.gates import _default_gates, check_gate, load_gates, reset_gate, save_gates
from projectsmd_dashboard.snapshots import list_snapshots, restore_snapshot, snapshot
from projectsmd_dashboard.update_queue import _load_queue, _save_queue, enqueue_update, reject_update


def test_snapshot_and_restore():
    with tempfile.TemporaryDirectory() as tmp:
        md = Path(tmp) / "project.md"
        md.write_text("original", encoding="utf-8")
        snap = snapshot(md)
        md.write_text("changed", encoding="utf-8")
        restore_snapshot(md, snap)
        assert md.read_text(encoding="utf-8") == "original"


def test_reject_update_cleans_queue():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "queue.json"
        # Monkeypatch queue path
        import projectsmd_dashboard.update_queue as uq
        orig_path = uq._queue_path
        uq._queue_path = lambda: path
        try:
            u = enqueue_update("/tmp/project.md", "proposed", "diff")
            assert u.status == "pending"
            rejected = reject_update(u.id)
            assert rejected is not None
            assert rejected.status == "rejected"
            # Queue should still contain it but not as pending
            pending = [q for q in _load_queue() if q.status == "pending"]
            assert len(pending) == 0
        finally:
            uq._queue_path = orig_path


def test_gate_reset():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "gates.json"
        import projectsmd_dashboard.gates as g
        orig_path = g._gates_path
        g._gates_path = lambda: path
        try:
            gates = _default_gates()
            save_gates(gates)
            check_gate("tests", user="agent")
            g2 = load_gates()
            assert next(x for x in g2 if x.id == "tests").status == "passed"
            reset_gate("tests")
            g3 = load_gates()
            assert next(x for x in g3 if x.id == "tests").status == "pending"
        finally:
            g._gates_path = orig_path


def test_multiple_snapshots_newest_first():
    with tempfile.TemporaryDirectory() as tmp:
        md = Path(tmp) / "project.md"
        md.write_text("v1", encoding="utf-8")
        s1 = snapshot(md)
        md.write_text("v2", encoding="utf-8")
        s2 = snapshot(md)
        snaps = list_snapshots(md)
        assert len(snaps) == 2
        assert snaps[0] == s2
        assert snaps[1] == s1
