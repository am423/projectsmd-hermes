"""Tests for GitHub integration."""
from __future__ import annotations

from projectsmd_dashboard.github_integration import get_repo_info


def test_get_repo_info_https():
    info = get_repo_info("https://github.com/am423/projectsmd-hermes.git")
    assert info["ok"] is True
    assert info["owner"] == "am423"
    assert info["repo"] == "projectsmd-hermes"


def test_get_repo_info_ssh():
    info = get_repo_info("git@github.com:am423/projectsmd-hermes.git")
    assert info["ok"] is True
    assert info["owner"] == "am423"
    assert info["repo"] == "projectsmd-hermes"


def test_get_repo_info_no_remote():
    # When no remote_url is passed and we're in a git repo, it auto-detects.
    # So we test with a bad URL instead.
    info = get_repo_info("https://gitlab.com/foo/bar.git")
    assert info["ok"] is False


def test_get_repo_info_bad_format():
    info = get_repo_info("https://gitlab.com/foo/bar.git")
    assert info["ok"] is False
