"""Tests for diff preview."""
from __future__ import annotations

from projectsmd_dashboard.diff_preview import diff_preview


def test_diff_preview_shows_changes():
    original = "line1\nline2\nline3\n"
    proposed = "line1\nline2-modified\nline3\n"
    diff = diff_preview(original, proposed)
    assert "-line2\n" in diff
    assert "+line2-modified\n" in diff


def test_diff_preview_empty_files():
    diff = diff_preview("", "new line\n")
    assert "+new line" in diff


def test_diff_preview_no_changes():
    diff = diff_preview("same\n", "same\n")
    assert diff == ""
