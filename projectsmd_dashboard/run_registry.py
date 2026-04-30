"""Run registry: SQLite-backed store for orchestrator runs.

Schema:
  runs       — one row per orchestrator launch
  run_events — stdout/stderr lines emitted by a run
"""
from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class RunRecord:
    id: str
    project_id: str
    prompt: str
    status: str  # "running" | "completed" | "failed"
    created_at: str
    updated_at: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunEvent:
    id: int
    run_id: str
    stream: str  # "stdout" | "stderr" | "system"
    line: str
    ts: str


class RunRegistry:
    """Thread-safe SQLite registry for orchestrator runs."""

    def __init__(self, db_path: Path) -> None:
        self._db = db_path
        self._lock = threading.Lock()
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with self._lock, sqlite3.connect(str(self._db)) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id         TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    prompt     TEXT NOT NULL,
                    status     TEXT NOT NULL DEFAULT 'running',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    meta       TEXT
                );
                CREATE TABLE IF NOT EXISTS run_events (
                    id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id  TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                    stream  TEXT NOT NULL,
                    line    TEXT NOT NULL,
                    ts      TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_events_run ON run_events(run_id);
                """
            )

    def create_run(self, run_id: str, project_id: str, prompt: str, meta: dict[str, Any] | None = None) -> RunRecord:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, sqlite3.connect(str(self._db)) as conn:
            conn.execute(
                "INSERT INTO runs (id, project_id, prompt, status, created_at, updated_at, meta) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (run_id, project_id, prompt, "running", now, now, json.dumps(meta or {})),
            )
        return RunRecord(id=run_id, project_id=project_id, prompt=prompt, status="running", created_at=now, updated_at=now, metadata=meta or {})

    def update_status(self, run_id: str, status: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, sqlite3.connect(str(self._db)) as conn:
            conn.execute("UPDATE runs SET status = ?, updated_at = ? WHERE id = ?", (status, now, run_id))

    def append_event(self, run_id: str, stream: str, line: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, sqlite3.connect(str(self._db)) as conn:
            conn.execute("INSERT INTO run_events (run_id, stream, line, ts) VALUES (?, ?, ?, ?)", (run_id, stream, line, now))

    def get_run(self, run_id: str) -> RunRecord | None:
        with self._lock, sqlite3.connect(str(self._db)) as conn:
            row = conn.execute("SELECT id, project_id, prompt, status, created_at, updated_at, meta FROM runs WHERE id = ?", (run_id,)).fetchone()
        if not row:
            return None
        return RunRecord(id=row[0], project_id=row[1], prompt=row[2], status=row[3], created_at=row[4], updated_at=row[5], metadata=json.loads(row[6] or "{}"))

    def list_runs(self, project_id: str | None = None, limit: int = 50) -> list[RunRecord]:
        with self._lock, sqlite3.connect(str(self._db)) as conn:
            if project_id:
                rows = conn.execute(
                    "SELECT id, project_id, prompt, status, created_at, updated_at, meta FROM runs WHERE project_id = ? ORDER BY created_at DESC LIMIT ?",
                    (project_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, project_id, prompt, status, created_at, updated_at, meta FROM runs ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [RunRecord(id=r[0], project_id=r[1], prompt=r[2], status=r[3], created_at=r[4], updated_at=r[5], metadata=json.loads(r[6] or "{}")) for r in rows]

    def get_events(self, run_id: str, after_id: int = 0) -> list[RunEvent]:
        with self._lock, sqlite3.connect(str(self._db)) as conn:
            rows = conn.execute(
                "SELECT id, run_id, stream, line, ts FROM run_events WHERE run_id = ? AND id > ? ORDER BY id",
                (run_id, after_id),
            ).fetchall()
        return [RunEvent(id=r[0], run_id=r[1], stream=r[2], line=r[3], ts=r[4]) for r in rows]