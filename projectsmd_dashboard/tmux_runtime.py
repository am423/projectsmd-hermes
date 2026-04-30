"""Tmux runtime wrapper for orchestrator runs.

Spawns a tmux session per run, captures stdout/stderr into the run registry,
and provides a kill switch.
"""
from __future__ import annotations

import shutil
import subprocess
import threading
import time
from typing import Any

from .run_registry import RunRegistry


def _tmux_available() -> bool:
    return shutil.which("tmux") is not None


def _session_name(run_id: str) -> str:
    # tmux session names must be alphanumeric-ish; sanitize
    return f"pmd-{run_id.replace('_', '-').replace(' ', '-')[:40]}"


def spawn_run(
    run_id: str,
    project_id: str,
    prompt: str,
    command: list[str],
    registry: RunRegistry,
    cwd: str | None = None,
) -> dict[str, Any]:
    """Spawn a tmux session for the given command and start a collector thread.

    Returns {"ok": True, "session": str} on success.
    """
    if not _tmux_available():
        return {"ok": False, "error": "tmux not available"}

    session = _session_name(run_id)
    registry.create_run(run_id, project_id, prompt)

    # Build the tmux command: new-session -d -s <session> <command...>
    tmux_cmd = ["tmux", "new-session", "-d", "-s", session] + command
    try:
        subprocess.run(tmux_cmd, cwd=cwd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        registry.update_status(run_id, "failed")
        registry.append_event(run_id, "system", f"tmux spawn failed: {exc.stderr}")
        return {"ok": False, "error": exc.stderr}

    # Start a background thread to tail the tmux pane and push events
    collector = threading.Thread(target=_collect, args=(run_id, session, registry), daemon=True)
    collector.start()

    return {"ok": True, "session": session}


def _collect(run_id: str, session: str, registry: RunRegistry) -> None:
    """Tail tmux pane output and push lines into the registry until the pane exits."""
    try:
        proc = subprocess.Popen(
            ["tmux", "pipe-pane", "-o", "-t", session, "cat"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        # Fallback: if pipe-pane doesn't work, use capture-pane in a loop
        if proc.stdout is None:
            _collect_fallback(run_id, session, registry)
            return

        for line in proc.stdout:
            registry.append_event(run_id, "stdout", line.rstrip("\n"))

        proc.wait()
        # Check if session still exists
        result = subprocess.run(["tmux", "has-session", "-t", session], capture_output=True)
        if result.returncode != 0:
            registry.update_status(run_id, "completed")
        else:
            registry.update_status(run_id, "failed")
    except Exception as exc:
        registry.append_event(run_id, "system", f"collector error: {exc}")
        registry.update_status(run_id, "failed")


def _collect_fallback(run_id: str, session: str, registry: RunRegistry) -> None:
    """Fallback collector using capture-pane in a polling loop."""
    last_output = ""
    while True:
        result = subprocess.run(
            ["tmux", "capture-pane", "-p", "-t", session],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            registry.update_status(run_id, "completed")
            break
        output = result.stdout
        # Only push new lines
        new_lines = output[len(last_output):].splitlines()
        for line in new_lines:
            if line.strip():
                registry.append_event(run_id, "stdout", line)
        last_output = output
        time.sleep(1.0)
        # Check if pane is still alive
        alive = subprocess.run(["tmux", "has-session", "-t", session], capture_output=True)
        if alive.returncode != 0:
            registry.update_status(run_id, "completed")
            break


def kill_run(run_id: str) -> dict[str, Any]:
    session = _session_name(run_id)
    result = subprocess.run(["tmux", "kill-session", "-t", session], capture_output=True, text=True)
    if result.returncode == 0:
        return {"ok": True}
    return {"ok": False, "error": result.stderr}
