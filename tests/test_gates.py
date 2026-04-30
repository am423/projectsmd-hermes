"""Tests for quality gates."""
from __future__ import annotations

import tempfile
from pathlib import Path


from projectsmd_dashboard.gates import (
    QualityGate,
    _default_gates,
    check_gate,
    fail_gate,
    load_gates,
    run_all_gates,
    save_gates,
)


def test_default_gates():
    gates = _default_gates()
    assert len(gates) >= 4
    assert any(g.id == "tests" for g in gates)


def test_save_and_load_gates(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "gates.json"
        monkeypatch.setattr("projectsmd_dashboard.gates._gates_path", lambda: path)
        gates = [QualityGate(id="x", name="X", description="test", required=True)]
        save_gates(gates)
        loaded = load_gates()
        assert len(loaded) == 1
        assert loaded[0].id == "x"


def test_check_and_fail_gate(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "gates.json"
        monkeypatch.setattr("projectsmd_dashboard.gates._gates_path", lambda: path)
        gates = _default_gates()
        save_gates(gates)
        g = check_gate("tests", user="agent")
        assert g is not None
        assert g.status == "passed"
        assert g.checked_by == "agent"
        g2 = fail_gate("lint", user="agent")
        assert g2 is not None
        assert g2.status == "failed"


def test_run_all_gates(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "gates.json"
        monkeypatch.setattr("projectsmd_dashboard.gates._gates_path", lambda: path)
        gates = _default_gates()
        save_gates(gates)
        check_gate("tests")
        check_gate("lint")
        result = run_all_gates()
        assert result["passed"] >= 2
        assert result["ok"] is False  # review and secrets still pending
