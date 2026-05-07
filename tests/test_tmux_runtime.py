"""Tests for tmux runtime wrapper.

These tests verify the helper functions without spawning tmux (which may not
be available in all environments).
"""
from __future__ import annotations



from projectsmd_dashboard.tmux_runtime import _session_name, _tmux_available, build_hermes_command
from projectsmd_dashboard.roster import AgentRole


def test_tmux_available_returns_bool():
    assert isinstance(_tmux_available(), bool)


def test_session_name_sanitizes():
    assert _session_name("run_1").startswith("pmd-")
    assert "_" not in _session_name("run_1")
    assert len(_session_name("a" * 100)) <= 45


def test_build_hermes_command_uses_real_cli_shape():
    command = build_hermes_command("do work")
    assert command[:4] == ["hermes", "chat", "-q", "do work"]
    assert command[-2:] == ["projectsmd", "--pass-session-id"]
    assert "agent" not in command
    assert "--prompt" not in command


def test_build_hermes_command_includes_role_overrides():
    role = AgentRole(id="build", name="Build", description="", model="openai/gpt-5", provider="openrouter", toolsets=["terminal", "file"])
    command = build_hermes_command("do work", role)
    assert "--model" in command
    assert "openai/gpt-5" in command
    assert "--provider" in command
    assert "openrouter" in command
    assert "--toolsets" in command
    assert "terminal,file" in command
