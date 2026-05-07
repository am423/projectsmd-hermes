"""Proposed update queue: staged mutations awaiting approval.

Stored in ~/.hermes/projectsmd/queue.json as a list of pending updates.
Each update has an id, project path, proposed content, diff, and status.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class PendingUpdate:
    id: str
    project_path: str
    proposed: str
    diff: str
    status: str  # "pending" | "approved" | "rejected"
    created_at: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_by: str = "user"
    reason: str = ""
    run_id: str = ""
    assignment_id: str = ""
    reviewed_at: str = ""
    review_comment: str = ""


def _queue_path() -> Path:
    return Path.home() / ".hermes" / "projectsmd" / "queue.json"


def _load_queue() -> list[PendingUpdate]:
    path = _queue_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [PendingUpdate(**item) for item in data]
    except (json.JSONDecodeError, TypeError):
        return []


def _save_queue(queue: list[PendingUpdate]) -> None:
    path = _queue_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([q.__dict__ for q in queue], indent=2),
        encoding="utf-8",
    )


def enqueue_update(project_path: str, proposed: str, diff: str, meta: dict[str, Any] | None = None) -> PendingUpdate:
    meta = meta or {}
    update = PendingUpdate(
        id=str(uuid.uuid4())[:8],
        project_path=project_path,
        proposed=proposed,
        diff=diff,
        status="pending",
        created_at=datetime.now(timezone.utc).isoformat(),
        metadata=meta,
        created_by=str(meta.get("created_by", "user")),
        reason=str(meta.get("reason", "")),
        run_id=str(meta.get("run_id", "")),
        assignment_id=str(meta.get("assignment_id", "")),
    )
    queue = _load_queue()
    queue.append(update)
    _save_queue(queue)
    return update


def list_pending(project_path: str | None = None) -> list[PendingUpdate]:
    queue = _load_queue()
    if project_path:
        return [q for q in queue if q.project_path == project_path and q.status == "pending"]
    return [q for q in queue if q.status == "pending"]


def approve_update(update_id: str, comment: str = "") -> PendingUpdate | None:
    queue = _load_queue()
    for q in queue:
        if q.id == update_id:
            q.status = "approved"
            q.reviewed_at = datetime.now(timezone.utc).isoformat()
            q.review_comment = comment
            _save_queue(queue)
            return q
    return None


def reject_update(update_id: str, comment: str = "") -> PendingUpdate | None:
    queue = _load_queue()
    for q in queue:
        if q.id == update_id:
            q.status = "rejected"
            q.reviewed_at = datetime.now(timezone.utc).isoformat()
            q.review_comment = comment
            _save_queue(queue)
            return q
