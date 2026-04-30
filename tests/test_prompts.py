"""Tests for prompt templates."""
from __future__ import annotations

from projectsmd_dashboard.prompts import (
    build_discovery_prompt,
    build_phase_transition_prompt,
    build_task_prompt,
    build_validate_prompt,
)


def test_build_task_prompt():
    project = {"name": "Test", "current_state": {"phase": "BUILD"}, "sections": {"Tasks": "- [ ] Do thing"}}
    prompt = build_task_prompt(project, "Implement auth")
    assert "Test" in prompt
    assert "BUILD" in prompt
    assert "Implement auth" in prompt


def test_build_discovery_prompt():
    project = {"name": "Test"}
    prompt = build_discovery_prompt(project, "Found bug")
    assert "Found bug" in prompt


def test_build_phase_transition_prompt():
    project = {"name": "Test", "current_state": {"phase": "BUILD"}}
    prompt = build_phase_transition_prompt(project, "SHIP")
    assert "BUILD" in prompt
    assert "SHIP" in prompt


def test_build_validate_prompt():
    project = {"name": "Test"}
    prompt = build_validate_prompt(project)
    assert "validation" in prompt.lower()
