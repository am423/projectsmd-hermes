# ProjectsMD Dashboard Security Model

The ProjectsMD dashboard plugin is designed for localhost use inside Hermes Agent.

## Boundary

- Intended host: `127.0.0.1`
- API prefix: `/api/plugins/projectsmd`
- Do not expose Hermes dashboard with project mutation or tmux-control routes on `0.0.0.0` unless you add network authentication and understand the risk.

## Mutation safety

- `project.md` remains the source of truth.
- Common mutations go through allowlisted ProjectsMD CLI wrappers.
- Unsupported or agent-proposed full-file changes go through the approval queue.
- Queue approval creates a snapshot before writing.
- Project writes use a file lock to avoid concurrent edits.

## Agent safety

- Orchestrator is the only default writer to `project.md`.
- Subagents should emit structured `PROJECT_*` protocol lines and propose queued updates.
- Tmux runs use the real Hermes CLI command shape:

```bash
hermes chat -q '<prompt>' -s projectsmd --pass-session-id
```

## Command safety

Safety policies block destructive command patterns such as:

- `rm -rf`
- `git push --force`
- `git reset --hard`
- `dd if=` / `of=/dev/`
- `sudo` is treated as requiring review

## Frontend safety

The bundle contract forbids:

- `innerHTML`
- `dangerouslySetInnerHTML`
- `alert()`
- `prompt()`
- `location.reload`

User-controlled strings render through React text nodes.
