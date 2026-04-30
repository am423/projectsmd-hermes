# ProjectsMD Hermes dashboard plugin

ProjectsMD includes a Hermes Agent dashboard plugin that adds a `Projects` tab to the Hermes web UI.

Current scope:

- registers `/projects` in the dashboard nav
- checks `projectsmd`, `tmux`, and `hermes` availability
- scans configured roots for `project.md` files
- renders project phase, current state, task counts, decisions, discoveries, and raw markdown
- leaves orchestrator launch disabled until the next implementation slice

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

Available routes:

```text
GET /api/plugins/projectsmd/health
GET /api/plugins/projectsmd/projects
GET /api/plugins/projectsmd/projects/detail?path=/path/to/project.md
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

Hermes dashboard plugin API routes are intended for localhost use. Keep the dashboard bound to localhost unless you explicitly accept that project scan and future tmux control endpoints are reachable on the network.

## Next slice

The planned next slice adds tmux-backed orchestrator/subagent launch:

- editable roster per ProjectsMD phase
- tmux run registry
- output tails
- structured `PROJECT_*` protocol parsing
- human checkpoint controls for approve/revise/reassign/stop
