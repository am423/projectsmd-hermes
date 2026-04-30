"""Tests for roster model."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from projectsmd_dashboard.roster import (
    AgentRole,
    _default_roster,
    _roster_path,
    load_roster,
    save_roster,
)


def test_default_roster_has_entries():
    roster = _default_roster()
    assert len(roster) >= 3
    assert any(r.id == "builder" for r in roster)


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
        assert any(r.id == "builder" for r in loaded)
