from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from .models import CurrentState, ProjectSummary, TaskCounts

TASK_RE = re.compile(r"^\s*- \[(?P<mark>[ xX])\]\s+(?P<body>.*)$")
SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
CURRENT_STATE_RE = re.compile(r"^\*\*(?P<key>[^*]+):\*\*\s*(?P<value>.*)$", re.MULTILINE)


def default_project_roots() -> list[Path]:
    roots: list[Path] = []
    env_roots = os.environ.get("PROJECTSMD_ROOTS", "")
    for raw in env_roots.split(os.pathsep):
        if raw.strip():
            roots.append(Path(raw).expanduser())

    home = Path.home()
    for candidate in (home / "projects", home / "projectsmd-hermes", Path.cwd()):
        if candidate not in roots:
            roots.append(candidate)
    return roots


def scan_projects(roots: list[str | Path] | None = None) -> list[dict[str, Any]]:
    selected_roots = [Path(root).expanduser() for root in (roots or default_project_roots())]
    seen: set[Path] = set()
    projects: list[dict[str, Any]] = []

    for root in selected_roots:
        if not root.exists():
            continue
        project_files = [root] if root.is_file() and root.name == "project.md" else root.rglob("project.md")
        for project_file in project_files:
            if any(part in {".git", "target", "node_modules", ".venv", "__pycache__"} for part in project_file.parts):
                continue
            resolved = project_file.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            try:
                projects.append(summarize_project(project_file))
            except OSError:
                continue

    projects.sort(key=lambda item: item.get("updated") or item.get("mtime") or "", reverse=True)
    return projects


def get_project_detail(project_md: str | Path) -> dict[str, Any]:
    path = Path(project_md).expanduser().resolve()
    text = path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(text)
    sections = parse_sections(body)
    current_state = parse_current_state(sections.get("Current State", ""))
    summary = summarize_text(path, text, frontmatter, sections, current_state)
    summary["raw"] = text
    summary["sections"] = sections
    summary["current_state"] = current_state
    return summary


def summarize_project(project_md: str | Path) -> dict[str, Any]:
    path = Path(project_md).expanduser().resolve()
    text = path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(text)
    sections = parse_sections(body)
    current_state = parse_current_state(sections.get("Current State", ""))
    return summarize_text(path, text, frontmatter, sections, current_state)


def summarize_text(
    path: Path,
    text: str,
    frontmatter: dict[str, Any],
    sections: dict[str, str],
    current_state: CurrentState,
) -> dict[str, Any]:
    stat = path.stat()
    tasks = count_tasks(sections.get("Tasks", text))
    phase = first_nonempty(current_state.phase, frontmatter.get("status"), "unknown")
    summary = ProjectSummary(
        id=project_id(path),
        name=first_nonempty(frontmatter.get("project"), path.parent.name),
        path=str(path),
        root=str(path.parent),
        status=first_nonempty(frontmatter.get("status"), phase),
        phase=phase,
        owner=frontmatter.get("owner", ""),
        agent=frontmatter.get("agent", ""),
        tags=parse_tags(frontmatter.get("tags", [])),
        created=frontmatter.get("created", ""),
        updated=frontmatter.get("updated", ""),
        mtime=stat.st_mtime,
        tasks=tasks,
        next_action=current_state.next_action,
        blockers=current_state.blockers,
    )
    return summary.to_dict()


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end].strip()
    body = text[text.find("\n", end + 4) + 1 :]
    data: dict[str, Any] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if value == "[]":
            data[key] = []
        elif value.startswith("[") and value.endswith("]"):
            data[key] = [item.strip().strip('"').strip("'") for item in value[1:-1].split(",") if item.strip()]
        else:
            data[key] = value
    return data, body


def parse_sections(body: str) -> dict[str, str]:
    matches = list(SECTION_RE.finditer(body))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[title] = body[start:end].strip()
    return sections


def parse_current_state(section: str) -> CurrentState:
    state = CurrentState()
    for match in CURRENT_STATE_RE.finditer(section):
        key = match.group("key").strip().lower()
        value = match.group("value").strip()
        if key == "phase":
            state.phase = value
        elif key == "next action":
            state.next_action = value
        elif key == "blockers":
            state.blockers = value
        elif key == "in progress":
            state.in_progress = value
        elif key == "last completed":
            state.last_completed = value
        elif key == "notes":
            state.notes = value
    return state


def count_tasks(text: str) -> TaskCounts:
    done = pending = blocked = 0
    for line in text.splitlines():
        match = TASK_RE.match(line)
        if not match:
            continue
        body = match.group("body").lower()
        if match.group("mark").lower() == "x":
            done += 1
        else:
            pending += 1
        if "blocked" in body or "blocker" in body:
            blocked += 1
    return TaskCounts(done=done, pending=pending, blocked=blocked, total=done + pending)


def project_id(path: Path) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", str(path.parent).strip("/"))
    return slug.strip("-").lower() or "root"


def parse_tags(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if not value:
        return []
    return [item.strip() for item in str(value).split(",") if item.strip()]


def first_nonempty(*values: Any) -> str:
    for value in values:
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""
