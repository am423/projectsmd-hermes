"""Quality gates: checklist-based validation before shipping.

Each gate is a named check with pass/fail status. Gates are stored in
~/.hermes/projectsmd/gates.json.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class QualityGate:
    id: str
    name: str
    description: str
    required: bool
    status: str = "pending"  # "pending" | "passed" | "failed"
    checked_at: str | None = None
    checked_by: str | None = None


def _gates_path() -> Path:
    return Path.home() / ".hermes" / "projectsmd" / "gates.json"


def load_gates() -> list[QualityGate]:
    path = _gates_path()
    if not path.exists():
        return _default_gates()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [QualityGate(**item) for item in data]
    except (json.JSONDecodeError, TypeError):
        return _default_gates()


def save_gates(gates: list[QualityGate]) -> None:
    path = _gates_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([g.__dict__ for g in gates], indent=2),
        encoding="utf-8",
    )


def check_gate(gate_id: str, user: str = "agent") -> QualityGate | None:
    gates = load_gates()
    for g in gates:
        if g.id == gate_id:
            g.status = "passed"
            g.checked_at = datetime.now(timezone.utc).isoformat()
            g.checked_by = user
            save_gates(gates)
            return g
    return None


def fail_gate(gate_id: str, user: str = "agent") -> QualityGate | None:
    gates = load_gates()
    for g in gates:
        if g.id == gate_id:
            g.status = "failed"
            g.checked_at = datetime.now(timezone.utc).isoformat()
            g.checked_by = user
            save_gates(gates)
            return g
    return None


def reset_gate(gate_id: str) -> QualityGate | None:
    gates = load_gates()
    for g in gates:
        if g.id == gate_id:
            g.status = "pending"
            g.checked_at = None
            g.checked_by = None
            save_gates(gates)
            return g
    return None


def run_all_gates(project_path: str | None = None) -> dict[str, Any]:
    """Run all quality gates and return a summary."""
    gates = load_gates()
    passed = sum(1 for g in gates if g.status == "passed")
    failed = sum(1 for g in gates if g.status == "failed")
    pending = sum(1 for g in gates if g.status == "pending")
    required_failed = any(g.required and g.status != "passed" for g in gates)
    return {
        "ok": not required_failed,
        "passed": passed,
        "failed": failed,
        "pending": pending,
        "gates": [g.__dict__ for g in gates],
    }


def _default_gates() -> list[QualityGate]:
    return [
        QualityGate(id="tests", name="Tests pass", description="All tests pass locally.", required=True),
        QualityGate(id="lint", name="Lint clean", description="No lint errors or warnings.", required=True),
        QualityGate(id="docs", name="Docs updated", description="README and docs reflect changes.", required=False),
        QualityGate(id="review", name="Code reviewed", description="At least one human or agent review.", required=True),
        QualityGate(id="secrets", name="No secrets", description="No hardcoded secrets or tokens.", required=True),
        QualityGate(id="compat", name="Backward compatible", description="No breaking changes without migration.", required=False),
    ]
