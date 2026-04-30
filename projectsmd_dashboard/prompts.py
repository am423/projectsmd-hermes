"""Prompt templates for orchestrator runs.

Each template is a function that takes project context and returns a prompt
string suitable for an LLM agent.
"""
from __future__ import annotations

from typing import Any


def build_task_prompt(project: dict[str, Any], task_description: str) -> str:
    """Return a prompt for an agent to work on a specific task."""
    name = project.get("name", "Untitled")
    phase = project.get("current_state", {}).get("phase", "UNKNOWN")
    tasks = project.get("sections", {}).get("Tasks", "")
    return (
        f"You are working on the project '{name}' (phase: {phase}).\n\n"
        f"Task: {task_description}\n\n"
        f"Current tasks:\n{tasks}\n\n"
        "Instructions:\n"
        "1. Read the project.md file to understand context.\n"
        "2. Implement the task.\n"
        "3. Run tests and validate.\n"
        "4. Update project.md with discoveries and mark the task done.\n"
        "5. Report completion.\n"
    )


def build_discovery_prompt(project: dict[str, Any], discovery_text: str) -> str:
    """Return a prompt for an agent to integrate a discovery."""
    name = project.get("name", "Untitled")
    return (
        f"Project: {name}\n\n"
        f"New discovery: {discovery_text}\n\n"
        "Instructions:\n"
        "1. Assess impact on current tasks and decisions.\n"
        "2. Update project.md Discoveries section.\n"
        "3. Propose any task or decision changes if needed.\n"
        "4. Report what you updated.\n"
    )


def build_phase_transition_prompt(project: dict[str, Any], next_phase: str) -> str:
    """Return a prompt for an agent to manage a phase transition."""
    name = project.get("name", "Untitled")
    current_phase = project.get("current_state", {}).get("phase", "UNKNOWN")
    return (
        f"Project: {name}\n\n"
        f"Transition from {current_phase} to {next_phase}.\n\n"
        "Instructions:\n"
        "1. Review all tasks in current phase — ensure done or blocked with reasons.\n"
        "2. Update phase in project.md.\n"
        "3. Initialize next-phase task list if empty.\n"
        "4. Report readiness.\n"
    )


def build_validate_prompt(project: dict[str, Any]) -> str:
    """Return a prompt for an agent to validate project health."""
    name = project.get("name", "Untitled")
    return (
        f"Project: {name}\n\n"
        "Run validation checks:\n"
        "1. project.md syntax and required sections.\n"
        "2. All tasks have owners or are marked done/blocked.\n"
        "3. Decisions have rationales.\n"
        "4. Discoveries are dated.\n"
        "5. Tests pass.\n"
        "Report any issues found.\n"
    )
