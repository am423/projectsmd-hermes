"""Typed models for ProjectsMD dashboard plugin.

All API output shapes should be derived from these models so the frontend
has a stable contract.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TaskCounts:
    done: int = 0
    pending: int = 0
    blocked: int = 0
    total: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {"done": self.done, "pending": self.pending, "blocked": self.blocked, "total": self.total}


@dataclass
class CurrentState:
    phase: str = ""
    next_action: str = ""
    blockers: str = ""
    in_progress: str = ""
    last_completed: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "next_action": self.next_action,
            "blockers": self.blockers,
            "in_progress": self.in_progress,
            "last_completed": self.last_completed,
            "notes": self.notes,
        }


@dataclass
class ValidationResult:
    valid: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "errors": self.errors, "warnings": self.warnings}


@dataclass
class ProjectSummary:
    id: str = ""
    name: str = ""
    path: str = ""
    root: str = ""
    status: str = ""
    phase: str = ""
    owner: str = ""
    agent: str = ""
    tags: list[str] = field(default_factory=list)
    created: str = ""
    updated: str = ""
    mtime: float = 0.0
    tasks: TaskCounts = field(default_factory=TaskCounts)
    next_action: str = ""
    blockers: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "root": self.root,
            "status": self.status,
            "phase": self.phase,
            "owner": self.owner,
            "agent": self.agent,
            "tags": self.tags,
            "created": self.created,
            "updated": self.updated,
            "mtime": self.mtime,
            "tasks": self.tasks.to_dict(),
            "next_action": self.next_action,
            "blockers": self.blockers,
        }


@dataclass
class ProjectDetail:
    id: str = ""
    name: str = ""
    path: str = ""
    root: str = ""
    status: str = ""
    phase: str = ""
    owner: str = ""
    agent: str = ""
    tags: list[str] = field(default_factory=list)
    created: str = ""
    updated: str = ""
    mtime: float = 0.0
    tasks: TaskCounts = field(default_factory=TaskCounts)
    next_action: str = ""
    blockers: str = ""
    raw: str = ""
    sections: dict[str, str] = field(default_factory=dict)
    current_state: CurrentState = field(default_factory=CurrentState)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "root": self.root,
            "status": self.status,
            "phase": self.phase,
            "owner": self.owner,
            "agent": self.agent,
            "tags": self.tags,
            "created": self.created,
            "updated": self.updated,
            "mtime": self.mtime,
            "tasks": self.tasks.to_dict(),
            "next_action": self.next_action,
            "blockers": self.blockers,
            "raw": self.raw,
            "sections": self.sections,
            "current_state": self.current_state.to_dict(),
        }
