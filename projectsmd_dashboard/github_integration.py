"""GitHub integration: link projects to repos, track issues/PRs.

Reads from ~/.git-credentials for PAT if available.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class GitHubRepo:
    owner: str
    repo: str
    url: str


def _read_git_credentials() -> str | None:
    creds = Path.home() / ".git-credentials"
    if not creds.exists():
        return None
    try:
        text = creds.read_text(encoding="utf-8")
        # Look for https://<token>@github.com/ line
        match = re.search(r"https://([^@]+)@github\.com", text)
        if match:
            return match.group(1)
    except Exception:
        pass
    return None


def _gh_cli_available() -> bool:
    return subprocess.run(["gh", "--version"], capture_output=True).returncode == 0


def get_repo_info(remote_url: str | None = None) -> dict[str, Any]:
    """Extract owner/repo from git remote or current directory."""
    if not remote_url:
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                remote_url = result.stdout.strip()
        except Exception:
            pass
    if not remote_url:
        return {"ok": False, "error": "No git remote found"}
    remote_url = remote_url.strip()
    if not remote_url or remote_url == "":
        return {"ok": False, "error": "No git remote found"}
    # Parse https://github.com/owner/repo.git or git@github.com:owner/repo.git
    https_match = re.match(r"https://github\.com/([^/]+)/([^/]+?)(?:\.git)?$", remote_url)
    ssh_match = re.match(r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$", remote_url)
    m = https_match or ssh_match
    if not m:
        return {"ok": False, "error": f"Unsupported remote format: {remote_url}"}
    owner, repo = m.group(1), m.group(2)
    return {"ok": True, "owner": owner, "repo": repo, "url": f"https://github.com/{owner}/{repo}"}


def list_issues(owner: str, repo: str, state: str = "open") -> dict[str, Any]:
    """List issues via gh CLI."""
    if not _gh_cli_available():
        return {"ok": False, "error": "gh CLI not available"}
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--repo", f"{owner}/{repo}", "--state", state, "--json", "number,title,state,url"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return {"ok": False, "error": result.stderr}
        issues = json.loads(result.stdout)
        return {"ok": True, "issues": issues}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def list_prs(owner: str, repo: str, state: str = "open") -> dict[str, Any]:
    """List PRs via gh CLI."""
    if not _gh_cli_available():
        return {"ok": False, "error": "gh CLI not available"}
    try:
        result = subprocess.run(
            ["gh", "pr", "list", "--repo", f"{owner}/{repo}", "--state", state, "--json", "number,title,state,url"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return {"ok": False, "error": result.stderr}
        prs = json.loads(result.stdout)
        return {"ok": True, "prs": prs}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
