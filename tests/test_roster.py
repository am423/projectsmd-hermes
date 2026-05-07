"""Tests for roster model."""
from __future__ import annotations

import tempfile
from pathlib import Path


from projectsmd_dashboard.roster import (
    AgentRole,
    _default_roster,
    load_roster,
    save_roster,
)


def test_default_roster_has_entries():
    roster = _default_roster()
    ids = {r.id for r in roster}
    assert {"orchestrator", "define", "design", "build", "verify", "ship", "research", "review"}.issubset(ids)
    orchestrator = next(r for r in roster if r.id == "orchestrator")
    assert orchestrator.can_write_files is True
    assert "projectsmd" in orchestrator.skills


def test_save_and_load_roster_roundtrip(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "roster.json"
        monkeypatch.setattr("projectsmd_dashboard.roster._roster_path", lambda: path)
        roster = [AgentRole(id="x", name="X", description="test")]
        save_roster(roster)
        loaded = load_roster()
        assert len(loaded) == 1
        assert loaded[0].id == "x"


def test_load_roster_missing_returns_default(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "roster.json"
        monkeypatch.setattr("projectsmd_dashboard.roster._roster_path", lambda: path)
        loaded = load_roster()
        assert any(r.id == "orchestrator" for r in loaded)
