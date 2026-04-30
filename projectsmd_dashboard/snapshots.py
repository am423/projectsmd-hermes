"""Project snapshots: versioned backups of project.md before mutations.

Snapshots are stored as project.md.<timestamp> in the same directory.
"""
from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path


def snapshot(project_md: Path) -> Path:
    """Create a timestamped snapshot of project.md. Returns the snapshot path."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    snap = project_md.with_suffix(f".md.{ts}")
    shutil.copy2(project_md, snap)
    return snap


def list_snapshots(project_md: Path) -> list[Path]:
    """List all snapshots for a project.md, newest first."""
    pattern = f"{project_md.name}.*"
    snaps = sorted(project_md.parent.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return [s for s in snaps if s.name.startswith(project_md.name + ".") and s != project_md]


def restore_snapshot(project_md: Path, snapshot_path: Path) -> None:
    """Restore project.md from a snapshot."""
    shutil.copy2(snapshot_path, project_md)
