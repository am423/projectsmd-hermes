"""Tests for tmux runtime wrapper.

These tests verify the helper functions without spawning tmux (which may not
be available in all environments).
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from projectsmd_dashboard.tmux_runtime import _session_name, _tmux_available


def test_tmux_available_returns_bool():
    assert isinstance(_tmux_available(), bool)


def test_session_name_sanitizes():
    assert _session_name("run_1").startswith("pmd-")
    assert "_" not in _session_name("run_1")
    assert len(_session_name("a" * 100)) <= 45
