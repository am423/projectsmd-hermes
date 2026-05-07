# Production Readiness Review

Status: implementation pass complete

Checklist:

- No `alert()`, `prompt()`, `location.reload`, `innerHTML`, or `dangerouslySetInnerHTML` in the dashboard bundle.
- Uses Hermes dashboard SDK components/hooks/fetchJSON/pluginAPI; React is not bundled.
- Hermes Projects branded header with docs link.
- Responsive grid layout for narrow and wide screens.
- Keyboard shortcuts: Ctrl+R rescan, Ctrl+N guidance toast, Escape clear selection/modal context.
- Modal dialogs use `role="dialog"` and `aria-label`.
- Search and phase filter controls have aria labels.
- Action feedback uses inline status/toasts, not blocking browser dialogs.
- Setup checklist explains missing projectsmd/tmux/hermes/root prerequisites with fix guidance.
- Project mutations go through safe API routes and ProjectsMD CLI wrappers.
- Queue approvals snapshot project.md before writing.
- Orchestrator runs use the real Hermes CLI shape: `hermes chat -q ... -s projectsmd --pass-session-id`.
- GitHub, quality gates, and ship checklist are exposed from the dashboard.

Verification commands:

```bash
python3 dashboard/scripts/build_frontend.py
node --check dashboard/dist/index.js
python3 -m pytest tests/test_dashboard_bundle.py -q
```
