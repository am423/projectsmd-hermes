from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from .project_scan import default_project_roots, get_project_detail, scan_projects

try:
    from fastapi import APIRouter, HTTPException
except Exception:  # pragma: no cover - lets unit tests import without FastAPI installed
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail
            super().__init__(detail)

    class APIRouter:  # type: ignore[no-redef]
        def __init__(self):
            self.routes = []

        def get(self, path: str):
            def decorator(func):
                self.routes.append(("GET", path, func))
                return func
            return decorator


router = APIRouter()


def _tool_version(command: str) -> dict[str, Any]:
    path = shutil.which(command)
    if not path:
        return {"available": False, "path": None, "version": None}
    try:
        result = subprocess.run([path, "--version"], text=True, capture_output=True, timeout=5)
        version = (result.stdout or result.stderr).strip().splitlines()[0] if (result.stdout or result.stderr).strip() else ""
    except Exception as exc:  # pragma: no cover - defensive health detail
        version = f"error: {exc}"
    return {"available": True, "path": path, "version": version}


@router.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "plugin": "projectsmd",
        "label": "Projects",
        "projectsmd": _tool_version("projectsmd"),
        "tmux": _tool_version("tmux"),
        "hermes": _tool_version("hermes"),
        "roots": [str(root) for root in default_project_roots()],
    }


@router.get("/projects")
def projects(roots: list[str] | None = None) -> dict[str, Any]:
    selected_roots = roots or [str(root) for root in default_project_roots()]
    return {"projects": scan_projects(selected_roots), "roots": selected_roots}


@router.get("/projects/detail")
def project_detail(path: str) -> dict[str, Any]:
    project_path = Path(path).expanduser()
    if project_path.is_dir():
        project_path = project_path / "project.md"
    if project_path.name != "project.md" or not project_path.exists():
        raise HTTPException(status_code=404, detail="project.md not found")
    return get_project_detail(project_path)
