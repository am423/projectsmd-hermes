"""Per-project file locks to serialize project.md mutations.

Uses a simple directory-based lock under the Hermes home so it survives
process restarts and works without extra dependencies.
"""
from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path


def _lock_dir() -> Path:
    home = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
    return home / "projectsmd" / "locks"


def _lock_path(project_md: str | Path) -> Path:
    resolved = Path(project_md).resolve()
    slug = str(resolved).replace("/", "_").replace("\\", "_")
    return _lock_dir() / f"{slug}.lock"


@contextmanager
def project_lock(project_md: str | Path, timeout: float = 10.0):
    lock_file = _lock_path(project_md)
    lock_dir = lock_file.parent
    lock_dir.mkdir(parents=True, exist_ok=True)

    start = time.time()
    while True:
        try:
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            try:
                os.write(fd, str(os.getpid()).encode())
                yield
            finally:
                os.close(fd)
                lock_file.unlink(missing_ok=True)
            break
        except FileExistsError:
            if time.time() - start > timeout:
                # Stale lock recovery: if owner pid is dead, steal it
                try:
                    owner = int(lock_file.read_text())
                    if not _pid_alive(owner):
                        lock_file.unlink(missing_ok=True)
                        continue
                except Exception:
                    pass
                raise TimeoutError(f"Could not acquire lock for {project_md}")
            time.sleep(0.1)


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False
