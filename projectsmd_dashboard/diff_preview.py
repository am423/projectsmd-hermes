"""Diff preview for project.md mutations.

Provides a unified diff between current and proposed content.
"""
from __future__ import annotations

import difflib
from pathlib import Path


def diff_preview(original: str, proposed: str, context: int = 3) -> str:
    """Return a unified diff of original vs proposed."""
    original_lines = original.splitlines(keepends=True) or [""]
    proposed_lines = proposed.splitlines(keepends=True) or [""]
    if not original_lines[-1].endswith("\n"):
        original_lines[-1] += "\n"
    if not proposed_lines[-1].endswith("\n"):
        proposed_lines[-1] += "\n"
    diff = difflib.unified_diff(
        original_lines,
        proposed_lines,
        fromfile="project.md",
        tofile="project.md (proposed)",
        lineterm="",
        n=context,
    )
    return "".join(diff)


def diff_from_file(path: Path, proposed: str, context: int = 3) -> str:
    """Read the file at path and diff against proposed content."""
    original = path.read_text(encoding="utf-8")
    return diff_preview(original, proposed, context=context)