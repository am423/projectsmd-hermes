from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from .config import load_config, save_config
from .diff_preview import diff_from_file
from .project_scan import get_project_detail, scan_projects
from .projectsmd_cli import (
    archive,
    decide,
    discover,
    init as projectsmd_init,
    phase_transition,
    session_summary,
    task_add,
    task_block,
    task_done,
    task_unblock,
    validate,
)
from .prompts import build_task_prompt
from .roster import AgentRole, load_roster, save_roster
from .run_registry import RunRegistry
from .safety import SafetyPolicy, check_command, load_policies, save_policies
from .snapshots import list_snapshots, restore_snapshot, snapshot
from .tmux_runtime import kill_run, spawn_run
from .update_queue import approve_update, enqueue_update, list_pending, reject_update
from .gates import QualityGate, check_gate, fail_gate, load_gates, reset_gate, run_all_gates, save_gates
from .github_integration import get_repo_info, list_issues, list_prs
from .ship_checklist import check_ship_item, ship_status, uncheck_ship_item

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
    config = load_config()
    roots = config.get("project_roots", [])
    return {
        "ok": True,
        "plugin": "projectsmd",
        "label": "Projects",
        "projectsmd": _tool_version("projectsmd"),
        "tmux": _tool_version("tmux"),
        "hermes": _tool_version("hermes"),
        "roots": roots,
    }


@router.get("/config")
def get_config() -> dict[str, Any]:
    return load_config()


@router.put("/config")
def put_config(config: dict[str, Any]) -> dict[str, Any]:
    save_config(config)
    return config


@router.get("/projects")
def projects(roots: list[str] | None = None) -> dict[str, Any]:
    config = load_config()
    selected_roots = roots or config.get("project_roots", [])
    return {"projects": scan_projects(selected_roots), "roots": selected_roots}


@router.get("/projects/detail")
def project_detail(path: str) -> dict[str, Any]:
    project_path = Path(path).expanduser()
    if project_path.is_dir():
        project_path = project_path / "project.md"
    if project_path.name != "project.md" or not project_path.exists():
        raise HTTPException(status_code=404, detail="project.md not found")
    return get_project_detail(project_path)


@router.post("/projects")
def create_project(body: dict[str, Any]) -> dict[str, Any]:
    root = body.get("root")
    if not root:
        raise HTTPException(status_code=400, detail="root is required")
    result = projectsmd_init(
        root=root,
        name=body.get("name", "Untitled"),
        owner=body.get("owner", ""),
        description=body.get("description", ""),
        core_value=body.get("core_value", ""),
        agent=body.get("agent"),
        tags=body.get("tags"),
        brownfield=body.get("brownfield", False),
    )
    if not result["ok"]:
        raise HTTPException(status_code=409, detail=result.get("stderr", "init failed"))
    project_md = Path(root).expanduser() / "project.md"
    return get_project_detail(project_md)


@router.post("/projects/{project_id}/validate")
def validate_project(project_id: str, body: dict[str, Any]) -> dict[str, Any]:
    project_md = _resolve_project_md(body)
    result = validate(project_md)
    return {"result": result, "detail": get_project_detail(project_md)}


@router.post("/projects/{project_id}/tasks")
def add_task(project_id: str, body: dict[str, Any]) -> dict[str, Any]:
    project_md = _resolve_project_md(body)
    result = task_add(project_md, body.get("title", ""), phase=body.get("phase"))
    return {"result": result, "detail": get_project_detail(project_md)}


@router.post("/projects/{project_id}/tasks/{task_id}/done")
def done_task(project_id: str, task_id: int, body: dict[str, Any]) -> dict[str, Any]:
    project_md = _resolve_project_md(body)
    result = task_done(project_md, task_id)
    return {"result": result, "detail": get_project_detail(project_md)}


@router.post("/projects/{project_id}/tasks/{task_id}/block")
def block_task(project_id: str, task_id: int, body: dict[str, Any]) -> dict[str, Any]:
    project_md = _resolve_project_md(body)
    result = task_block(project_md, task_id, body.get("reason", ""))
    return {"result": result, "detail": get_project_detail(project_md)}


@router.post("/projects/{project_id}/tasks/{task_id}/unblock")
def unblock_task(project_id: str, task_id: int, body: dict[str, Any]) -> dict[str, Any]:
    project_md = _resolve_project_md(body)
    result = task_unblock(project_md, task_id)
    return {"result": result, "detail": get_project_detail(project_md)}


@router.post("/projects/{project_id}/decisions")
def add_decision(project_id: str, body: dict[str, Any]) -> dict[str, Any]:
    project_md = _resolve_project_md(body)
    result = decide(project_md, body.get("decision", ""), rationale=body.get("rationale"))
    return {"result": result, "detail": get_project_detail(project_md)}


@router.post("/projects/{project_id}/discoveries")
def add_discovery(project_id: str, body: dict[str, Any]) -> dict[str, Any]:
    project_md = _resolve_project_md(body)
    result = discover(project_md, body.get("text", ""))
    return {"result": result, "detail": get_project_detail(project_md)}


@router.post("/projects/{project_id}/session")
def record_session(project_id: str, body: dict[str, Any]) -> dict[str, Any]:
    project_md = _resolve_project_md(body)
    result = session_summary(project_md, body.get("summary", ""))
    return {"result": result, "detail": get_project_detail(project_md)}


@router.post("/projects/{project_id}/phase-transition")
def transition_phase(project_id: str, body: dict[str, Any]) -> dict[str, Any]:
    project_md = _resolve_project_md(body)
    result = phase_transition(project_md, body.get("phase", ""))
    return {"result": result, "detail": get_project_detail(project_md)}


@router.post("/projects/{project_id}/archive")
def archive_project(project_id: str, body: dict[str, Any]) -> dict[str, Any]:
    project_md = _resolve_project_md(body)
    result = archive(project_md, summary=body.get("summary"))
    return {"result": result, "detail": get_project_detail(project_md)}


@router.post("/projects/{project_id}/snapshot")
def create_snapshot(project_id: str, body: dict[str, Any]) -> dict[str, Any]:
    project_md = _resolve_project_md(body)
    snap = snapshot(project_md)
    return {"snapshot": str(snap), "detail": get_project_detail(project_md)}


@router.get("/projects/{project_id}/snapshots")
def get_snapshots(project_id: str, path: str) -> dict[str, Any]:
    project_md = Path(path).expanduser()
    if project_md.is_dir():
        project_md = project_md / "project.md"
    if project_md.name != "project.md" or not project_md.exists():
        raise HTTPException(status_code=404, detail="project.md not found")
    snaps = list_snapshots(project_md)
    return {"snapshots": [str(s) for s in snaps]}


@router.post("/projects/{project_id}/restore")
def restore_project(project_id: str, body: dict[str, Any]) -> dict[str, Any]:
    project_md = _resolve_project_md(body)
    snap_path = Path(body.get("snapshot", ""))
    if not snap_path.exists():
        raise HTTPException(status_code=404, detail="snapshot not found")
    restore_snapshot(project_md, snap_path)
    return {"detail": get_project_detail(project_md)}


@router.post("/projects/{project_id}/queue")
def queue_update(project_id: str, body: dict[str, Any]) -> dict[str, Any]:
    project_md = _resolve_project_md(body)
    proposed = body.get("proposed")
    if proposed is None:
        raise HTTPException(status_code=400, detail="proposed is required")
    diff = diff_from_file(project_md, proposed)
    update = enqueue_update(str(project_md), proposed, diff, meta=body.get("meta"))
    return {"update": update.__dict__}


@router.get("/projects/{project_id}/queue")
def get_queue(project_id: str, path: str) -> dict[str, Any]:
    project_md = Path(path).expanduser()
    if project_md.is_dir():
        project_md = project_md / "project.md"
    if project_md.name != "project.md" or not project_md.exists():
        raise HTTPException(status_code=404, detail="project.md not found")
    pending = list_pending(str(project_md))
    return {"pending": [u.__dict__ for u in pending]}


@router.post("/projects/{project_id}/queue/{update_id}/approve")
def approve_queue_update(project_id: str, update_id: str) -> dict[str, Any]:
    update = approve_update(update_id)
    if not update:
        raise HTTPException(status_code=404, detail="update not found")
    # Write the approved content to project.md
    project_md = Path(update.project_path)
    project_md.write_text(update.proposed, encoding="utf-8")
    return {"update": update.__dict__, "detail": get_project_detail(project_md)}


@router.post("/projects/{project_id}/queue/{update_id}/reject")
def reject_queue_update(project_id: str, update_id: str) -> dict[str, Any]:
    update = reject_update(update_id)
    if not update:
        raise HTTPException(status_code=404, detail="update not found")
    return {"update": update.__dict__}


def _resolve_project_md(body: dict[str, Any]) -> Path:
    path = body.get("path")
    if not path:
        raise HTTPException(status_code=400, detail="path is required")
    project_md = Path(path).expanduser()
    if project_md.is_dir():
        project_md = project_md / "project.md"
    if project_md.name != "project.md" or not project_md.exists():
        raise HTTPException(status_code=404, detail="project.md not found")
    return project_md


@router.post("/projects/{project_id}/diff")
def diff_project(project_id: str, body: dict[str, Any]) -> dict[str, Any]:
    """Preview a diff of a proposed change to project.md."""
    project_md = _resolve_project_md(body)
    proposed = body.get("proposed")
    if proposed is None:
        raise HTTPException(status_code=400, detail="proposed is required")
    return {"diff": diff_from_file(project_md, proposed)}


@router.post("/projects/{project_id}/runs")
def launch_run(project_id: str, body: dict[str, Any]) -> dict[str, Any]:
    """Launch an orchestrator run for a project.

    Accepts an optional `role_id` to select an agent role from the roster.
    """
    import uuid

    project_md = _resolve_project_md(body)
    detail = get_project_detail(project_md)
    role_id = body.get("role_id")
    roster = load_roster()
    role = next((r for r in roster if r.id == role_id), None) if role_id else None

    prompt = body.get("prompt")
    if not prompt:
        base_prompt = build_task_prompt(detail, body.get("task", "Continue work"))
        if role and role.system_prompt:
            prompt = f"{role.system_prompt}\n\n{base_prompt}"
        else:
            prompt = base_prompt

    run_id = body.get("run_id") or str(uuid.uuid4())[:8]

    db_path = Path.home() / ".hermes" / "projectsmd" / "runs.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    registry = RunRegistry(db_path)

    # Safety check on the command
    command = ["hermes", "agent", "--prompt", prompt]
    safety = check_command(command)
    if not safety["ok"]:
        raise HTTPException(status_code=403, detail=safety["reason"])

    result = spawn_run(run_id, project_id, prompt, command, registry, cwd=str(project_md.parent))
    if not result["ok"]:
        raise HTTPException(status_code=500, detail=result.get("error", "spawn failed"))
    return {"run_id": run_id, "status": "running", "session": result.get("session"), "role": role.id if role else None}


@router.get("/policies")
def get_policies() -> dict[str, Any]:
    return {"policies": [p.__dict__ for p in load_policies()]}


@router.put("/policies")
def put_policies(body: dict[str, Any]) -> dict[str, Any]:
    policies = [SafetyPolicy(**item) for item in body.get("policies", [])]
    save_policies(policies)
    return {"policies": [p.__dict__ for p in policies]}


@router.post("/policies/check")
def check_policy(body: dict[str, Any]) -> dict[str, Any]:
    command = body.get("command", [])
    return check_command(command)


@router.get("/gates")
def get_gates() -> dict[str, Any]:
    return {"gates": [g.__dict__ for g in load_gates()]}


@router.put("/gates")
def put_gates(body: dict[str, Any]) -> dict[str, Any]:
    gates = [QualityGate(**item) for item in body.get("gates", [])]
    save_gates(gates)
    return {"gates": [g.__dict__ for g in gates]}


@router.post("/gates/{gate_id}/check")
def check_gate_endpoint(gate_id: str, body: dict[str, Any]) -> dict[str, Any]:
    user = body.get("user", "agent")
    gate = check_gate(gate_id, user=user)
    if not gate:
        raise HTTPException(status_code=404, detail="gate not found")
    return {"gate": gate.__dict__}


@router.post("/gates/{gate_id}/fail")
def fail_gate_endpoint(gate_id: str, body: dict[str, Any]) -> dict[str, Any]:
    user = body.get("user", "agent")
    gate = fail_gate(gate_id, user=user)
    if not gate:
        raise HTTPException(status_code=404, detail="gate not found")
    return {"gate": gate.__dict__}


@router.post("/gates/{gate_id}/reset")
def reset_gate_endpoint(gate_id: str) -> dict[str, Any]:
    gate = reset_gate(gate_id)
    if not gate:
        raise HTTPException(status_code=404, detail="gate not found")
    return {"gate": gate.__dict__}


@router.post("/gates/run")
def run_gates() -> dict[str, Any]:
    return run_all_gates()


@router.get("/github/repo")
def github_repo(path: str) -> dict[str, Any]:
    project_md = Path(path).expanduser()
    if project_md.is_dir():
        project_md = project_md / "project.md"
    if project_md.name != "project.md" or not project_md.exists():
        raise HTTPException(status_code=404, detail="project.md not found")
    result = get_repo_info()
    if not result["ok"]:
        raise HTTPException(status_code=404, detail=result.get("error", "repo not found"))
    return result


@router.get("/github/issues")
def github_issues(owner: str, repo: str, state: str = "open") -> dict[str, Any]:
    return list_issues(owner, repo, state=state)


@router.get("/github/prs")
def github_prs(owner: str, repo: str, state: str = "open") -> dict[str, Any]:
    return list_prs(owner, repo, state=state)


@router.get("/projects/{project_id}/ship")
def get_ship_checklist(project_id: str, path: str) -> dict[str, Any]:
    project_md = Path(path).expanduser()
    if project_md.is_dir():
        project_md = project_md / "project.md"
    if project_md.name != "project.md" or not project_md.exists():
        raise HTTPException(status_code=404, detail="project.md not found")
    return ship_status(project_md)


@router.post("/projects/{project_id}/ship/{item_id}/check")
def check_ship_item_endpoint(project_id: str, item_id: str, body: dict[str, Any]) -> dict[str, Any]:
    project_md = _resolve_project_md(body)
    item = check_ship_item(project_md, item_id, user=body.get("user", "agent"))
    if not item:
        raise HTTPException(status_code=404, detail="item not found")
    return {"item": item.__dict__, "status": ship_status(project_md)}


@router.post("/projects/{project_id}/ship/{item_id}/uncheck")
def uncheck_ship_item_endpoint(project_id: str, item_id: str, body: dict[str, Any]) -> dict[str, Any]:
    project_md = _resolve_project_md(body)
    item = uncheck_ship_item(project_md, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="item not found")
    return {"item": item.__dict__, "status": ship_status(project_md)}


@router.get("/projects/{project_id}/runs")
def list_runs(project_id: str) -> dict[str, Any]:
    db_path = Path.home() / ".hermes" / "projectsmd" / "runs.db"
    registry = RunRegistry(db_path)
    runs = registry.list_runs(project_id=project_id)
    return {"runs": [r.__dict__ for r in runs]}


@router.get("/projects/{project_id}/runs/{run_id}")
def get_run(project_id: str, run_id: str) -> dict[str, Any]:
    db_path = Path.home() / ".hermes" / "projectsmd" / "runs.db"
    registry = RunRegistry(db_path)
    run = registry.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    events = registry.get_events(run_id)
    return {"run": run.__dict__, "events": [e.__dict__ for e in events]}


@router.get("/projects/{project_id}/runs/{run_id}/poll")
def poll_run_events(project_id: str, run_id: str, after: int = 0) -> dict[str, Any]:
    """Poll for new events since after_id."""
    db_path = Path.home() / ".hermes" / "projectsmd" / "runs.db"
    registry = RunRegistry(db_path)
    run = registry.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    events = registry.get_events(run_id, after_id=after)
    return {"run": run.__dict__, "events": [e.__dict__ for e in events]}


@router.post("/projects/{project_id}/runs/{run_id}/kill")
def kill_run_endpoint(project_id: str, run_id: str) -> dict[str, Any]:
    result = kill_run(run_id)
    if not result["ok"]:
        raise HTTPException(status_code=500, detail=result.get("error", "kill failed"))
    db_path = Path.home() / ".hermes" / "projectsmd" / "runs.db"
    registry = RunRegistry(db_path)
    registry.update_status(run_id, "killed")
    return {"run_id": run_id, "status": "killed"}


@router.get("/roster")
def get_roster() -> dict[str, Any]:
    return {"roster": [r.__dict__ for r in load_roster()]}


@router.put("/roster")
def put_roster(body: dict[str, Any]) -> dict[str, Any]:
    roster = [AgentRole(**item) for item in body.get("roster", [])]
    save_roster(roster)
    return {"roster": [r.__dict__ for r in roster]}
