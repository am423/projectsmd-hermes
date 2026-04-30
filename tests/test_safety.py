"""Tests for safety policies."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from projectsmd_dashboard.safety import (
    SafetyPolicy,
    _default_policies,
    _policies_path,
    check_command,
    load_policies,
    save_policies,
)


def test_default_policies_block_rm_rf():
    result = check_command(["rm", "-rf", "/"])
    assert result["ok"] is False
    assert "no-rm-rf" == result["policy"]


def test_default_policies_allow_safe_command():
    result = check_command(["echo", "hello"])
    assert result["ok"] is True


def test_save_and_load_policies(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "policies.json"
        monkeypatch.setattr("projectsmd_dashboard.safety._policies_path", lambda: path)
        policies = [SafetyPolicy(id="x", name="X", description="test", action="block", patterns=["bad"])]
        save_policies(policies)
        loaded = load_policies()
        assert len(loaded) == 1
        assert loaded[0].id == "x"


def test_check_command_respects_loaded_policies(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "policies.json"
        monkeypatch.setattr("projectsmd_dashboard.safety._policies_path", lambda: path)
        policies = [SafetyPolicy(id="x", name="X", description="test", action="block", patterns=["evil"])]
        save_policies(policies)
        assert check_command(["evil", "cmd"])["ok"] is False
        assert check_command(["good", "cmd"])["ok"] is True
