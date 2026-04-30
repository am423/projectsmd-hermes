"""Safety policies: rules that constrain what agents can do.

Policies are loaded from ~/.hermes/projectsmd/policies.json.
Default policies block destructive operations unless explicitly allowed.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SafetyPolicy:
    id: str
    name: str
    description: str
    action: str  # "block" | "warn" | "allow"
    patterns: list[str] = field(default_factory=list)


def _policies_path() -> Path:
    return Path.home() / ".hermes" / "projectsmd" / "policies.json"


def load_policies() -> list[SafetyPolicy]:
    path = _policies_path()
    if not path.exists():
        return _default_policies()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [SafetyPolicy(**item) for item in data]
    except (json.JSONDecodeError, TypeError):
        return _default_policies()


def save_policies(policies: list[SafetyPolicy]) -> None:
    path = _policies_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([p.__dict__ for p in policies], indent=2),
        encoding="utf-8",
    )


def check_command(command: list[str], policies: list[SafetyPolicy] | None = None) -> dict[str, Any]:
    """Check a shell command against safety policies.

    Returns {"ok": True} if allowed, or {"ok": False, "policy": str, "reason": str} if blocked.
    """
    if policies is None:
        policies = load_policies()
    cmd_str = " ".join(command)
    for policy in policies:
        if policy.action == "allow":
            continue
        for pattern in policy.patterns:
            if pattern in cmd_str:
                return {
                    "ok": False,
                    "policy": policy.id,
                    "reason": f"Blocked by policy '{policy.name}': {policy.description}",
                }
    return {"ok": True}


def _default_policies() -> list[SafetyPolicy]:
    return [
        SafetyPolicy(
            id="no-rm-rf",
            name="No rm -rf",
            description="Prevent recursive deletion of directories.",
            action="block",
            patterns=["rm -rf", "rm -r /", "rm -rf /"],
        ),
        SafetyPolicy(
            id="no-git-force",
            name="No git force",
            description="Prevent force pushes and destructive git operations.",
            action="block",
            patterns=["git push --force", "git push -f", "git reset --hard"],
        ),
        SafetyPolicy(
            id="no-dd",
            name="No disk overwrite",
            description="Prevent direct disk writes with dd.",
            action="block",
            patterns=["dd if=", "of=/dev/"],
        ),
        SafetyPolicy(
            id="warn-sudo",
            name="Warn sudo",
            description="Flag commands that use sudo for review.",
            action="warn",
            patterns=["sudo "],
        ),
    ]
