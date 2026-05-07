"""Roster model: agent role definitions for orchestrator runs.

Stored in ~/.hermes/projectsmd/roster.json as a JSON array of AgentRole objects.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AgentRole:
    id: str
    name: str
    description: str
    skills: list[str] = field(default_factory=list)
    model: str = "default"
    system_prompt: str = ""
    provider: str = ""
    toolsets: list[str] = field(default_factory=list)
    phase_scope: list[str] = field(default_factory=list)
    max_parallel_tasks: int = 1
    can_write_files: bool = False
    requires_checkpoint_before_actions: bool = True


def _roster_path() -> Path:
    home = Path.home()
    return home / ".hermes" / "projectsmd" / "roster.json"


def load_roster() -> list[AgentRole]:
    path = _roster_path()
    if not path.exists():
        return _default_roster()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [AgentRole(**item) for item in data]
    except (json.JSONDecodeError, TypeError):
        return _default_roster()


def save_roster(roster: list[AgentRole]) -> None:
    path = _roster_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([r.__dict__ for r in roster], indent=2),
        encoding="utf-8",
    )


def _default_roster() -> list[AgentRole]:
    return [
        AgentRole(
            id="orchestrator",
            name="Orchestrator",
            description="Owns project.md, phase transitions, assignment, checkpointing, and synthesis.",
            skills=["projectsmd"],
            system_prompt="You are the ProjectsMD orchestrator. You are the only default writer to project.md; subagents propose updates.",
            toolsets=["terminal", "file", "delegation"],
            phase_scope=["define", "design", "build", "verify", "ship"],
            can_write_files=True,
        ),
        AgentRole(id="define", name="Define Agent", description="Clarifies requirements, users, constraints, and out-of-scope boundaries.", skills=["research"], phase_scope=["define"]),
        AgentRole(id="design", name="Design Agent", description="Designs architecture, interfaces, constraints, and data flow.", skills=["architecture"], phase_scope=["design"]),
        AgentRole(id="build", name="Build Agent", description="Implements build-phase tasks with tests.", skills=["code", "tests"], toolsets=["terminal", "file"], phase_scope=["build"], can_write_files=True),
        AgentRole(id="verify", name="Verify Agent", description="Runs tests and validates acceptance criteria.", skills=["testing", "qa"], toolsets=["terminal", "file"], phase_scope=["verify"]),
        AgentRole(id="ship", name="Ship Agent", description="Handles docs, release, deploy, and ship checklist.", skills=["release", "docs"], phase_scope=["ship"]),
        AgentRole(id="research", name="Research Agent", description="Researches external docs and prior art.", skills=["research"], toolsets=["web"]),
        AgentRole(id="review", name="Review Agent", description="Reviews implementation for spec compliance, security, and quality.", skills=["code-review", "security"], toolsets=["terminal", "file"]),
    ]
