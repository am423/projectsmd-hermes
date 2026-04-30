"""Ship checklist: pre-release verification for projects.

A ship checklist is a set of items that must be verified before a project
is considered ready for release. Stored in project frontmatter or a separate
ship.json file.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class ShipItem:
    id: str
    label: str
    done: bool = False
    checked_at: str | None = None


def _ship_path(project_md: Path) -> Path:
    return project_md.parent / ".projectsmd" / "ship.json"


def load_ship_checklist(project_md: Path) -> list[ShipItem]:
    path = _ship_path(project_md)
    if not path.exists():
        return _default_ship_checklist()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [ShipItem(**item) for item in data]
    except (json.JSONDecodeError, TypeError):
        return _default_ship_checklist()


def save_ship_checklist(project_md: Path, items: list[ShipItem]) -> None:
    path = _ship_path(project_md)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([i.__dict__ for i in items], indent=2),
        encoding="utf-8",
    )


def check_ship_item(project_md: Path, item_id: str, user: str = "agent") -> ShipItem | None:
    items = load_ship_checklist(project_md)
    for item in items:
        if item.id == item_id:
            item.done = True
            item.checked_at = datetime.now(timezone.utc).isoformat()
            save_ship_checklist(project_md, items)
            return item
    return None


def uncheck_ship_item(project_md: Path, item_id: str) -> ShipItem | None:
    items = load_ship_checklist(project_md)
    for item in items:
        if item.id == item_id:
            item.done = False
            item.checked_at = None
            save_ship_checklist(project_md, items)
            return item
    return None


def ship_status(project_md: Path) -> dict[str, Any]:
    items = load_ship_checklist(project_md)
    done = sum(1 for i in items if i.done)
    total = len(items)
    return {
        "ready": done == total,
        "done": done,
        "total": total,
        "items": [i.__dict__ for i in items],
    }


def _default_ship_checklist() -> list[ShipItem]:
    return [
        ShipItem(id="tests", label="All tests pass"),
        ShipItem(id="docs", label="Documentation updated"),
        ShipItem(id="review", label="Code reviewed"),
        ShipItem(id="changelog", label="Changelog updated"),
        ShipItem(id="version", label="Version bumped"),
        ShipItem(id="secrets", label="No secrets committed"),
    ]
