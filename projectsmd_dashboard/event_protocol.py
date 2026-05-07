"""Event protocol parser for agent run output.

Parses structured events from agent stdout lines so the dashboard can
render them as cards instead of raw text.

Supported events (JSON lines with a type field):
  {"type": "task", "id": 1, "action": "done"}
  {"type": "decision", "text": "...", "rationale": "..."}
  {"type": "discovery", "text": "..."}
  {"type": "phase", "phase": "SHIP"}
  {"type": "error", "message": "..."}
  {"type": "complete"}
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class AgentEvent:
    type: str
    payload: dict[str, Any]
    raw: str


def parse_event_line(line: str) -> AgentEvent | None:
    """Parse a single stdout line into an AgentEvent if it follows a supported protocol."""
    stripped = line.strip()
    project_event = _parse_project_protocol(stripped)
    if project_event:
        return project_event
    if not stripped.startswith("{"):
        return None
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    event_type = payload.get("type")
    if not event_type or not isinstance(event_type, str):
        return None
    return AgentEvent(type=event_type, payload=payload, raw=stripped)


def _parse_project_protocol(stripped: str) -> AgentEvent | None:
    if not stripped.startswith("PROJECT_") or ":" not in stripped:
        return None
    prefix, raw_payload = stripped.split(":", 1)
    event_type = prefix.lower().replace("project_", "")
    raw_payload = raw_payload.strip()
    try:
        payload = json.loads(raw_payload) if raw_payload else {}
    except json.JSONDecodeError:
        payload = {"message": raw_payload}
    if not isinstance(payload, dict):
        payload = {"value": payload}
    return AgentEvent(type=event_type, payload=payload, raw=stripped)


def parse_stream(lines: list[str]) -> list[AgentEvent]:
    """Parse a list of stdout lines into AgentEvents."""
    events: list[AgentEvent] = []
    for line in lines:
        ev = parse_event_line(line)
        if ev:
            events.append(ev)
    return events
