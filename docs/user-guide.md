# ProjectsMD Dashboard User Guide

Open the Hermes dashboard Projects tab at:

```text
http://127.0.0.1:9119/projects
```

## Install

```bash
git clone https://github.com/am423/projectsmd-hermes.git
cd projectsmd-hermes
cargo install --path .
bash scripts/install-dashboard-plugin.sh
hermes dashboard --no-open
```

## What you can do

- Scan configured roots for `project.md` files.
- Create a new ProjectsMD project from the UI.
- Search and filter projects by name, path, owner, tag, and phase.
- View current state, tasks, decisions, discoveries, raw markdown, and structured project detail.
- Add tasks, decisions, and discoveries through safe ProjectsMD CLI-backed API routes.
- Preview diffs and queue proposed `project.md` changes for approval.
- Approve queued updates with automatic snapshots before writing.
- Launch and monitor Hermes orchestrator runs through tmux.
- Inspect quality gates, GitHub repo status, and ship checklist status.

## Keyboard shortcuts

- `Ctrl+R`: rescan projects
- `Ctrl+N`: shows guidance for adding a root through the Roots panel
- `Escape`: clear selected project / close context

## Troubleshooting

- If API routes 404 after an update, restart `hermes dashboard --no-open`.
- If `projectsmd` is missing, run `cargo install --path .` from this repo.
- If orchestrator runs cannot start, install `tmux` and verify `hermes` is on PATH.
- If no projects appear, add a readable root in the Roots panel.
