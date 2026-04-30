"""Tests for event protocol parser."""
from __future__ import annotations

from projectsmd_dashboard.event_protocol import parse_event_line, parse_stream


def test_parse_task_event():
    line = '{"type": "task", "id": 1, "action": "done"}'
    ev = parse_event_line(line)
    assert ev is not None
    assert ev.type == "task"
    assert ev.payload["id"] == 1


def test_parse_non_json_returns_none():
    assert parse_event_line("plain text") is None


def test_parse_invalid_json_returns_none():
    assert parse_event_line("{not json}") is None


def test_parse_stream():
    lines = [
        "{\"type\": \"task\", \"id\": 1}",
        "some log",
        "{\"type\": \"discovery\", \"text\": \"Found bug\"}",
    ]
    events = parse_stream(lines)
    assert len(events) == 2
    assert events[0].type == "task"
    assert events[1].type == "discovery"
