"""Roster model: agent role definitions for orchestrator runs.

Stored in ~/.hermes/projectsmd/roster.json as a JSON array of AgentRole objects.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AgentRole:
    id: str
    name: str
    description: str
    skills: list[str] = field(default_factory=list)
    model: str = "default"
    system_prompt: str = ""


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
            id="builder",
            name="Builder",
            description="Writes code, runs tests, fixes bugs.",
            skills=["python", "rust", "typescript"],
            model="default",
            system_prompt="You are a senior software engineer. Write clean, tested code.",
        ),
        AgentRole(
            id="reviewer",
            name="Reviewer",
            description="Reviews code, finds issues, suggests improvements.",
            skills=["code-review", "security", "performance"],
            model="default",
            system_prompt="You are a meticulous code reviewer. Find bugs, suggest improvements.",
        ),
        AgentRole(
            id="architect",
            name="Architect",
            description="Designs systems, makes key decisions, plans phases.",
            skills=["system-design", "api-design", "database"],
            model="default",
            system_prompt="You are a systems architect. Design scalable, maintainable systems.",
        ),
    ]
