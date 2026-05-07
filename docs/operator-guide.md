# ProjectsMD Dashboard Operator Guide

## Architecture

The ProjectsMD dashboard integration is a standalone Hermes dashboard plugin.

- Plugin install path: `${HERMES_HOME:-~/.hermes}/plugins/projectsmd`
- Manifest: `dashboard/manifest.json`
- Frontend source: `dashboard/src/app.js`
- Frontend bundle loaded by Hermes: `dashboard/dist/index.js`
- Backend entrypoint: `dashboard/plugin_api.py`
- Backend implementation: `projectsmd_dashboard/*.py`
- API mount: `/api/plugins/projectsmd/*`
- Runtime state: `${HERMES_HOME:-~/.hermes}/projectsmd/`

Hermes serves static plugin assets and mounts `plugin_api.py` at dashboard startup. Backend route changes require dashboard restart.

## Development workflow

```bash
python3 dashboard/scripts/build_frontend.py
node --check dashboard/dist/index.js
python3 -m pytest -q
. "$HOME/.cargo/env" && cargo test
bash scripts/smoke-test-dashboard-plugin.sh
```

Commit both `dashboard/src/app.js` and `dashboard/dist/index.js` after frontend changes.

## Runtime files

- `config.json`: project roots, filters, favorites, recents
- `queue.json`: pending/approved/rejected project.md updates
- `runs.db`: orchestrator run registry and run events
- `roster.json`: editable agent role roster
- `policies.json`: command safety policies

## Operational notes

- Keep dashboard bound to `127.0.0.1` for mutation and tmux-control routes.
- Use the Roots panel to configure scan roots.
- Verify duplicate plugin symlinks are absent if the sidebar shows duplicate Projects tabs.
- Restart dashboard after updating plugin backend files.
