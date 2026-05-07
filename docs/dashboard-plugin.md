# ProjectsMD Hermes dashboard plugin

ProjectsMD includes a Hermes Agent dashboard plugin that adds a `Projects` tab to the Hermes web UI.

Current scope:

- registers `/projects` in the dashboard nav
- checks `projectsmd`, `tmux`, and `hermes` availability
- scans configured roots for `project.md` files
- validates roots and shows onboarding/setup status
- creates new ProjectsMD projects from the UI
- searches and filters project list by query and phase
- renders project phase, current state, structured tasks, decisions, discoveries, requirements, and raw markdown
- supports safe task/decision/discovery/session/phase/archive mutations through ProjectsMD CLI wrappers
- supports diff preview, approval queue metadata, snapshots, and restore
- launches Hermes orchestrator runs through tmux using `hermes chat -q ... -s projectsmd --pass-session-id`
- parses structured `PROJECT_*` run protocol lines
- exposes quality gates, GitHub repo status, and ship checklist panels

## Install

From this repo:

```bash
bash scripts/install-dashboard-plugin.sh
```

This creates:

```text
~/.hermes/plugins/projectsmd -> /path/to/projectsmd-hermes
```

Restart the dashboard so `plugin_api.py` is mounted:

```bash
hermes dashboard --no-open
```

Then open:

```text
http://127.0.0.1:9119/projects
```

## Configure project roots

By default the plugin scans:

- `$PROJECTSMD_ROOTS`, if set
- `~/projects`
- `~/projectsmd-hermes`
- the dashboard process current directory

Set explicit roots with colon-separated paths:

```bash
export PROJECTSMD_ROOTS="$HOME/projects:$HOME/benchmark-project"
hermes dashboard --no-open
```

## API

Hermes mounts the plugin API at:

```text
/api/plugins/projectsmd
```

Available routes include:

```text
GET /api/plugins/projectsmd/health
GET/PUT /api/plugins/projectsmd/config
GET/POST /api/plugins/projectsmd/projects
GET /api/plugins/projectsmd/projects/detail?path=/path/to/project.md
POST /api/plugins/projectsmd/projects/{id}/validate
POST /api/plugins/projectsmd/projects/{id}/tasks
POST /api/plugins/projectsmd/projects/{id}/tasks/{task_id}/done
POST /api/plugins/projectsmd/projects/{id}/tasks/{task_id}/block
POST /api/plugins/projectsmd/projects/{id}/tasks/{task_id}/unblock
POST /api/plugins/projectsmd/projects/{id}/decisions
POST /api/plugins/projectsmd/projects/{id}/discoveries
POST /api/plugins/projectsmd/projects/{id}/session
POST /api/plugins/projectsmd/projects/{id}/phase-transition
POST /api/plugins/projectsmd/projects/{id}/archive
GET/POST /api/plugins/projectsmd/projects/{id}/queue
POST /api/plugins/projectsmd/projects/{id}/queue/{update_id}/approve
POST /api/plugins/projectsmd/projects/{id}/queue/{update_id}/reject
GET/POST /api/plugins/projectsmd/projects/{id}/runs
GET /api/plugins/projectsmd/projects/{id}/runs/{run_id}
GET /api/plugins/projectsmd/projects/{id}/runs/{run_id}/poll
POST /api/plugins/projectsmd/projects/{id}/runs/{run_id}/kill
GET/PUT /api/plugins/projectsmd/roster
GET/PUT /api/plugins/projectsmd/policies
GET/PUT /api/plugins/projectsmd/gates
GET /api/plugins/projectsmd/github/repo
GET /api/plugins/projectsmd/github/issues
GET /api/plugins/projectsmd/github/prs
GET /api/plugins/projectsmd/projects/{id}/ship
```

## Development checks

```bash
bash scripts/smoke-test-dashboard-plugin.sh
```

This runs:

- Python dashboard plugin tests
- JavaScript syntax check
- manifest/import smoke checks

## Security note

Hermes dashboard plugin API routes are intended for localhost use. Keep the dashboard bound to localhost unless you explicitly accept that project scan, mutation, and tmux-control endpoints are reachable on the network. See [security.md](security.md).

## Additional docs

- [User guide](user-guide.md)
- [Operator guide](operator-guide.md)
- [Security model](security.md)
- [Production readiness](production-readiness.md)
