# World-Class Agentic Project Management Implementation Plan

> For Hermes: Use subagent-driven-development skill to implement this plan task-by-task.

Goal: Turn ProjectsMD Hermes from a read-only project.md browser into a polished end-to-end agentic project management system for planning, launching, supervising, steering, validating, and shipping multi-agent work.

Architecture: Keep project.md as the durable source of truth, add a small local SQLite runtime for ephemeral orchestration state, and expose everything through the Hermes dashboard Projects tab. The backend owns safety, file locks, CLI mutations, tmux/Hermes process control, and event parsing; the frontend is a human command center for project state, agent runs, checkpoints, diffs, and audit history.

Tech Stack: Rust CLI projectsmd, Python FastAPI dashboard plugin backend, SQLite, tmux, Hermes Agent CLI, dashboard IIFE JS using window.__HERMES_PLUGIN_SDK__, pytest/unittest, cargo test, node --check.

Current State

Repo: /home/am/projectsmd-hermes
GitHub: https://github.com/am423/projectsmd-hermes
Latest commit at planning time: f327317
Installed dashboard plugin: ~/.hermes/plugins/projectsmd -> /home/am/projectsmd-hermes
Dashboard route: /projects
Current plugin API:
- GET /api/plugins/projectsmd/health
- GET /api/plugins/projectsmd/projects
- GET /api/plugins/projectsmd/projects/detail?path=/path/to/project.md

Current capabilities:
- Projects sidebar tab exists.
- Duplicate ProjectsMD plugin was removed.
- UI scans project.md roots and renders project cards/detail/read-only sections.
- Orchestrator launch is intentionally disabled.
- No write operations, no tmux launch, no event stream, no checkpoint workflow, no project creation wizard, no CLI JSON mode, no persisted run history.

Definition of world-class

A world-class version must do these well:

1. Project source of truth
   - project.md remains canonical and human-readable.
   - Every mutation is safe, auditable, lock-protected, and reversible.
   - UI can create, inspect, edit, validate, diff, and archive projects without corrupting project.md.

2. Agentic orchestration
   - Human can launch an orchestrator from the dashboard.
   - Orchestrator can request subagents by role.
   - Subagents work on precise assignments derived from project.md state.
   - The system tracks progress, blockers, results, and proposed updates live.

3. Human control
   - Nothing dangerous happens silently.
   - Human can approve/reject project.md changes, phase transitions, destructive commands, and risky file writes.
   - Stop, pause, steer, reassign, and resume are first-class controls.

4. Professional dashboard UX
   - Looks native to Hermes dashboard.
   - Fast and responsive with clear empty/loading/error states.
   - Makes project state obvious at a glance.
   - Shows the next action, not just raw files.

5. Trust and reliability
   - Complete audit trail.
   - Tests for parser, CLI wrapper, locks, tmux runtime, event protocol, API, and UI smoke.
   - Recoverable after dashboard restart, browser refresh, or agent crash.
   - Safe local-only security model documented and enforced.

Milestone roadmap

M0 — Stabilize foundation
M1 — Make Projects a real project workspace
M2 — Add safe project.md mutations
M3 — Add orchestration runtime and tmux-backed Hermes runs
M4 — Add subagent assignment protocol and live supervision
M5 — Add checkpoint, diff, and human approval workflow
M6 — Add quality gates, verification, and shipping workflows
M7 — Add polish, observability, packaging, and docs
M8 — Dogfood on real projects and harden

M0 — Stabilize foundation

Objective: Make the existing plugin reliable, testable, and maintainable before adding orchestration.

Task 0.1: Add plugin package metadata and test dependencies

Files:
- Create: pyproject.toml
- Modify: README.md

Steps:
1. Add minimal Python project metadata for dashboard backend tests.
2. Add optional test deps: fastapi, httpx, pytest, pytest-cov.
3. Keep Rust Cargo.toml unchanged.
4. Verify: python -m pytest tests -q, cargo test.

Acceptance:
- Python tests can run with pytest, not only unittest.
- No import path hacks required except dashboard/plugin_api.py shim.

Task 0.2: Replace ad hoc parser with typed models

Files:
- Create: projectsmd_dashboard/models.py
- Modify: projectsmd_dashboard/project_scan.py
- Test: tests/test_project_scan.py

Steps:
1. Add dataclasses or Pydantic models:
   - ProjectSummary
   - ProjectDetail
   - TaskCounts
   - CurrentState
   - ValidationResult
2. Make scan_projects return serializable model dicts.
3. Add tests for normal project.md, malformed frontmatter, missing sections, huge file, duplicate paths.
4. Verify: python -m pytest tests/test_project_scan.py -q.

Acceptance:
- API output shape is stable and documented.
- Bad project.md files show validation errors, not crashed scans.

Task 0.3: Add dashboard API contract tests

Files:
- Create: tests/test_plugin_api_contract.py

Steps:
1. Use FastAPI TestClient when fastapi is installed.
2. Test /health, /projects, /projects/detail.
3. Test 404 for invalid project path.
4. Test that routes do not include double /api/plugins prefix.

Acceptance:
- Backend routes are verified as Hermes will mount them.

Task 0.4: Add frontend smoke harness

Files:
- Create: tests/test_dashboard_bundle.py
- Modify: scripts/smoke-test-dashboard-plugin.sh

Steps:
1. Keep node --check.
2. Add string-level assertions for SDK.components, SDK.hooks, SDK.fetchJSON, register("projectsmd").
3. Add manifest validation.
4. Add script output that tells user to restart dashboard when backend routes change.

Acceptance:
- Prevents the SDK mistake that broke the first screen.

M1 — Make Projects a real project workspace

Objective: Turn read-only browsing into a useful daily project cockpit.

Task 1.1: Add plugin config file

Files:
- Create: projectsmd_dashboard/config.py
- Create: tests/test_config.py
- Modify: projectsmd_dashboard/api.py

Config path:
- ~/.hermes/projectsmd/config.json

Fields:
- project_roots: list[str]
- ignored_dirs: list[str]
- default_owner: string
- default_agent: string
- auto_validate: bool
- max_scan_depth: int

API:
- GET /config
- PUT /config

Acceptance:
- User can configure roots without environment variables.
- Config is profile-safe if Hermes exposes HERMES_HOME; otherwise defaults to ~/.hermes.

Task 1.2: Add root management UI

Files:
- Modify: dashboard/dist/index.js
- Test: tests/test_dashboard_bundle.py

UI:
- Roots card shows configured roots.
- Add root input.
- Remove root button.
- Rescan button.

Acceptance:
- No need to restart dashboard to change roots.

Task 1.3: Add project creation wizard

Files:
- Create: projectsmd_dashboard/projectsmd_cli.py
- Modify: projectsmd_dashboard/api.py
- Modify: dashboard/dist/index.js
- Test: tests/test_projectsmd_cli.py, tests/test_plugin_api_contract.py

API:
- POST /projects

Body:
- root
- name
- owner
- agent
- tags
- description
- core_value
- brownfield

Backend:
- Calls projectsmd init non-interactively.
- Refuses if project.md exists unless explicit overwrite flag is added later.
- Returns ProjectDetail.

Acceptance:
- User can create a new project from dashboard.
- Result validates.

Task 1.4: Add native section rendering

Files:
- Modify: dashboard/dist/index.js

UI:
- Render tasks as checkboxes/badges, not pre blocks.
- Render decisions as a table.
- Render Current State as structured fields.
- Keep raw markdown behind details.

Acceptance:
- Page is usable without reading raw markdown.

M2 — Safe project.md mutations

Objective: Let users update project.md from the dashboard through projectsmd CLI wrappers, never arbitrary shell.

Task 2.1: Add file lock and command allowlist

Files:
- Create: projectsmd_dashboard/locks.py
- Modify: projectsmd_dashboard/projectsmd_cli.py
- Test: tests/test_projectsmd_cli.py

Allowed commands:
- validate
- status
- next
- task list
- task add
- task done
- task block
- task unblock
- decide
- discover
- session --non-interactive
- phase --transition
- archive

Acceptance:
- No API accepts arbitrary command strings.
- Concurrent mutations serialize per project.md.

Task 2.2: Add mutation API endpoints

Files:
- Modify: projectsmd_dashboard/api.py
- Test: tests/test_plugin_api_contract.py

API:
- POST /projects/{project_id}/tasks
- POST /projects/{project_id}/tasks/{task_id}/done
- POST /projects/{project_id}/tasks/{task_id}/block
- POST /projects/{project_id}/tasks/{task_id}/unblock
- POST /projects/{project_id}/decisions
- POST /projects/{project_id}/discoveries
- POST /projects/{project_id}/session
- POST /projects/{project_id}/phase-transition
- POST /projects/{project_id}/archive

Acceptance:
- Every mutation returns before/after summary and refreshed detail.

Task 2.3: Add mutation UI

Files:
- Modify: dashboard/dist/index.js

UI:
- Add task form scoped to phase.
- Done/block/unblock buttons beside tasks.
- Add decision form with rationale.
- Add discovery form.
- Session summary form.
- Phase transition button with confirmation.

Acceptance:
- UI covers the common ProjectsMD workflow end-to-end without terminal.

Task 2.4: Add diff preview for every mutation

Files:
- Create: projectsmd_dashboard/diffing.py
- Modify: projectsmd_dashboard/api.py
- Modify: dashboard/dist/index.js
- Test: tests/test_diffing.py

API behavior:
- Mutations can run with preview=true.
- Backend copies project.md to temp dir, runs command, returns unified diff.
- Apply only after confirmation.

Acceptance:
- Destructive or major mutations require preview/confirm.

M3 — Orchestration runtime

Objective: Launch and supervise Hermes orchestrator sessions safely from Projects tab.

Task 3.1: Add run registry schema

Files:
- Create: projectsmd_dashboard/runtime_store.py
- Create: tests/test_runtime_store.py

Storage:
- ~/.hermes/projectsmd/runtime.db

Tables:
- runs
- agents
- assignments
- events
- checkpoints
- project_snapshots

Acceptance:
- Runs survive dashboard restart.
- DB migrations are idempotent.

Task 3.2: Add tmux runtime wrapper

Files:
- Create: projectsmd_dashboard/tmux_runtime.py
- Test: tests/test_tmux_runtime.py

Functions:
- session_exists(name)
- launch_session(name, command, cwd)
- send_text(name, text)
- capture_tail(name, lines)
- stop_session(name)
- list_project_sessions(run_id)

Acceptance:
- Unit tests verify generated tmux commands.
- Optional real-tmux smoke test behind PROJECTSMD_REAL_TMUX=1.

Task 3.3: Add prompt templates

Files:
- Create: projectsmd_dashboard/prompts.py
- Create: projectsmd_dashboard/templates/orchestrator.md
- Create: projectsmd_dashboard/templates/subagent.md
- Test: tests/test_prompts.py

Prompt requirements:
- Include project.md snapshot.
- Include active phase and allowed actions.
- Include single-writer rule: orchestrator owns project.md.
- Include structured protocol lines.
- Include stop/approval policy.

Acceptance:
- Prompt rendering is deterministic and covered by snapshot tests.

Task 3.4: Launch orchestrator API

Files:
- Modify: projectsmd_dashboard/api.py
- Modify: dashboard/dist/index.js
- Test: tests/test_plugin_api_contract.py

API:
- POST /projects/{project_id}/runs
- GET /runs
- GET /runs/{run_id}
- POST /runs/{run_id}/stop
- POST /runs/{run_id}/steer

Launch command:
- tmux new-session -d -s projectsmd-<project_id>-<run_id>-orchestrator -x 160 -y 48 'hermes -s projectsmd --pass-session-id'
- send initial prompt with tmux send-keys

Acceptance:
- Dashboard can launch, tail, steer, and stop orchestrator.

M4 — Subagent assignment protocol

Objective: Make multi-agent work structured, visible, and controllable.

Task 4.1: Define event protocol parser

Files:
- Create: projectsmd_dashboard/events.py
- Test: tests/test_events.py

Protocol lines:
- PROJECT_ASSIGNMENT: {json}
- PROJECT_PROGRESS: {json}
- PROJECT_BLOCKER: {json}
- PROJECT_RESULT: {json}
- PROJECT_SUBAGENT_REQUEST: {json}
- PROJECT_MD_UPDATE_PROPOSED: {json}
- PROJECT_CHECKPOINT: {json}

Acceptance:
- Invalid JSON becomes parse_error event, not crash.
- Events are persisted with raw line and parsed payload.

Task 4.2: Add roster model and editor

Files:
- Create: projectsmd_dashboard/roster.py
- Modify: dashboard/dist/index.js
- Test: tests/test_roster.py

Default roles:
- Orchestrator
- Define Agent
- Design Agent
- Build Agent
- Verify Agent
- Ship Agent
- Research Agent optional
- Review Agent optional

Fields:
- enabled
- role
- model
- provider
- toolsets
- phase_scope
- write_permissions
- max_parallel_tasks
- checkpoint_policy

Acceptance:
- User can edit and save a roster per project.

Task 4.3: Add subagent launch from orchestrator requests

Files:
- Modify: projectsmd_dashboard/api.py
- Modify: projectsmd_dashboard/tmux_runtime.py
- Modify: projectsmd_dashboard/events.py
- Test: tests/test_subagent_launch.py

Flow:
1. Orchestrator emits PROJECT_SUBAGENT_REQUEST.
2. Backend creates assignment and subagent tmux session.
3. Subagent prompt includes assignment and project.md snapshot.
4. UI shows subagent card.

Acceptance:
- Backend, not model text alone, controls process creation.

Task 4.4: Add Agent Board UI

Files:
- Modify: dashboard/dist/index.js

UI:
- Run timeline.
- Orchestrator card.
- Subagent cards by role.
- Assignment status: queued/running/blocked/review/done/failed.
- Output tail drawer.
- Stop/reassign buttons.

Acceptance:
- Human can understand all running work in 10 seconds.

M5 — Checkpoints, diffs, and approval workflow

Objective: Make autonomous work trustworthy.

Task 5.1: Add project snapshots

Files:
- Create: projectsmd_dashboard/snapshots.py
- Test: tests/test_snapshots.py

Behavior:
- Snapshot project.md before every run, mutation, and phase transition.
- Store content hash and timestamp.
- Allow restore by snapshot id.

Acceptance:
- User can recover from bad agent updates.

Task 5.2: Add proposed update queue

Files:
- Modify: projectsmd_dashboard/runtime_store.py
- Modify: projectsmd_dashboard/events.py
- Modify: projectsmd_dashboard/api.py
- Test: tests/test_checkpoints.py

API:
- GET /runs/{run_id}/proposals
- POST /runs/{run_id}/proposals/{proposal_id}/approve
- POST /runs/{run_id}/proposals/{proposal_id}/reject
- POST /runs/{run_id}/proposals/{proposal_id}/revise

Acceptance:
- Proposed project.md changes do not apply without approval unless policy explicitly allows it.

Task 5.3: Add visual diff approval UI

Files:
- Modify: dashboard/dist/index.js

UI:
- Unified diff viewer.
- Approve/reject/revise buttons.
- Show proposer, assignment, rationale, affected sections.

Acceptance:
- Human sees exactly what will change before accepting.

Task 5.4: Add safety policies

Files:
- Create: projectsmd_dashboard/security.py
- Test: tests/test_security.py

Policies:
- Refuse network-exposed dangerous endpoints unless localhost.
- Require confirmation for archive/phase transition/stop all/restore snapshot.
- Optional allowlist of project roots.
- Refuse paths outside configured roots.

Acceptance:
- API cannot mutate arbitrary filesystem paths.

M6 — Verification and shipping workflows

Objective: Close the loop from idea to shipped, not just running agents.

Task 6.1: Add quality gates model

Files:
- Create: projectsmd_dashboard/quality_gates.py
- Test: tests/test_quality_gates.py

Gate types:
- command gate: cargo test, pytest, npm test, etc.
- file existence gate
- project.md validation gate
- git clean/diff gate
- URL health gate

Acceptance:
- Gates are configured per project and phase.

Task 6.2: Add gate runner API/UI

Files:
- Modify: projectsmd_dashboard/api.py
- Modify: dashboard/dist/index.js

API:
- GET /projects/{project_id}/quality-gates
- PUT /projects/{project_id}/quality-gates
- POST /projects/{project_id}/quality-gates/run

Acceptance:
- Verify phase has concrete pass/fail evidence.

Task 6.3: Add GitHub integration

Files:
- Create: projectsmd_dashboard/github.py
- Test: tests/test_github.py

Capabilities:
- Detect repo remote.
- Show branch/status/diff summary.
- Link commits to session log.
- Optional create GitHub issue/PR from task.

Acceptance:
- Project dashboard shows whether work is committed/pushed.

Task 6.4: Add ship checklist

Files:
- Modify: projectsmd_dashboard/api.py
- Modify: dashboard/dist/index.js

UI:
- Release readiness checklist.
- Docs updated.
- Tests passed.
- Git clean/pushed.
- Archive project button.

Acceptance:
- Ship phase can be completed from dashboard with evidence.

M7 — Polish, observability, packaging

Objective: Make it feel like a product, not an experiment.

Task 7.1: Add event streaming

Files:
- Modify: projectsmd_dashboard/api.py
- Modify: dashboard/dist/index.js

Start with polling:
- GET /runs/{run_id}/events?since=<id>

Only add WebSocket later if polling is insufficient.

Acceptance:
- UI updates within 2 seconds while agents run.

Task 7.2: Add command palette and keyboard shortcuts

Files:
- Modify: dashboard/dist/index.js

Shortcuts:
- r rescan
- n new task
- d decision
- g run gates
- o launch orchestrator
- s stop selected run

Acceptance:
- Power user can drive the app quickly.

Task 7.3: Add onboarding walkthrough

Files:
- Modify: dashboard/dist/index.js
- Modify: docs/dashboard-plugin.md

Flow:
- No roots configured -> add root.
- No project.md -> create project.
- Project exists -> show next action.
- Orchestration disabled/missing tmux/hermes -> show exact fix.

Acceptance:
- First run is self-explanatory.

Task 7.4: Add release packaging

Files:
- Modify: scripts/install-dashboard-plugin.sh
- Create: scripts/uninstall-dashboard-plugin.sh
- Create: .github/workflows/ci.yml
- Modify: README.md

CI:
- cargo fmt --check
- cargo test
- python -m pytest tests -q
- node --check dashboard/dist/index.js
- bash scripts/smoke-test-dashboard-plugin.sh

Acceptance:
- GitHub shows green CI for every push.

M8 — Dogfood and hardening

Objective: Use it on real projects until it earns trust.

Task 8.1: Dogfood on projectsmd-hermes itself

Steps:
1. Create project.md in /home/am/projectsmd-hermes.
2. Use dashboard to manage remaining implementation tasks.
3. Launch orchestrator only after M3 is complete.
4. Record discoveries and UX pain immediately.

Acceptance:
- Tool manages its own development without terminal-only fallbacks.

Task 8.2: Dogfood on one larger existing project

Candidate:
- /home/am/projects/datasets
- /home/am/benchmark-project
- another active repo Adam chooses

Acceptance:
- Handles large project.md, many tasks, and multi-session work.

Task 8.3: Add recovery drills

Scenarios:
- Dashboard restart during run.
- Browser refresh during run.
- tmux session killed.
- agent emits invalid protocol JSON.
- malformed project.md.
- phase transition rejected.

Acceptance:
- Recovery documented and tested.

Task 8.4: Tighten docs into product docs

Files:
- README.md
- HERMES.md
- docs/dashboard-plugin.md
- docs/orchestration.md
- docs/security.md
- docs/protocol.md

Acceptance:
- A new user can install, create a project, launch an orchestrator, approve a change, run gates, and ship.

Suggested execution order

Sprint 1: Foundation and workspace
- M0 all tasks
- M1 all tasks
- M2.1, M2.2

Sprint 2: Mutation and UX
- M2.3, M2.4
- M7.2, M7.3
- Start dogfooding read/write workflow

Sprint 3: Orchestrator MVP
- M3 all tasks
- M4.1
- Minimal run page with orchestrator only

Sprint 4: Subagents and supervision
- M4.2, M4.3, M4.4
- M7.1 polling events

Sprint 5: Trust layer
- M5 all tasks
- M6.1, M6.2

Sprint 6: Ship-grade product
- M6.3, M6.4
- M7.4
- M8 hardening

Non-negotiable engineering rules

- TDD for backend logic: parser, CLI wrappers, locks, runtime store, tmux wrapper, event parser, security checks.
- No arbitrary shell endpoint.
- No direct project.md writes from subagents.
- Every project.md mutation is lock-protected.
- Every destructive operation has preview or confirmation.
- Every run has an audit trail.
- Dashboard JS uses SDK.components and SDK.hooks only.
- Backend route changes require dashboard restart; frontend-only changes can use plugin rescan/reload.
- Keep localhost-only assumption explicit; block risky endpoints if dashboard is publicly bound.

First implementation slice to start with

Do not jump straight to orchestration. Build trust first.

Next slice should be:
1. Add config file and editable project roots.
2. Add typed ProjectSummary/ProjectDetail models.
3. Add pytest API contract tests.
4. Add project creation wizard.
5. Add safe validate/status/next endpoints.
6. Polish section rendering for tasks/decisions.

Why: If basic project CRUD and rendering are not solid, autonomous orchestration will amplify bad state and user distrust.

Success metrics

- 0 duplicate sidebar entries.
- Projects tab loads in under 500ms for normal roots after initial scan cache.
- A user can create a project, add tasks, log a decision, validate, and record a session entirely in UI.
- A user can launch an orchestrator, see live progress, steer it, stop it, and approve/reject proposed project.md updates.
- System recovers cleanly after dashboard restart.
- All project.md changes are explainable by event log and diff.
- CI passes on every push.
- Dogfooding produces fewer terminal fallbacks over time.
