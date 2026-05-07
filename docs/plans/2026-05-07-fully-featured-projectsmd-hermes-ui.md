# Fully Featured ProjectsMD Hermes Web UI Implementation Plan

> For Hermes: Use subagent-driven-development skill to implement this plan task-by-task.

Goal: Turn https://github.com/am423/projectsmd-hermes into a polished, fully featured, easy-to-use ProjectsMD interface that lives as a Hermes dashboard addon at http://127.0.0.1:9119/projects.

Architecture: Keep this as a standalone Hermes dashboard plugin installed at ~/.hermes/plugins/projectsmd, not a Hermes fork. Backend remains a thin FastAPI plugin API mounted under /api/plugins/projectsmd, with project.md as the source of truth and profile-safe runtime state under ${HERMES_HOME:-~/.hermes}/projectsmd. Frontend should move from one large handwritten dist/index.js file toward a maintainable source structure compiled to dashboard/dist/index.js while still using the Hermes plugin SDK, not bundled React.

Tech Stack: Hermes dashboard plugin manifest + plugin_api.py, FastAPI APIRouter, Python stdlib/dataclasses/sqlite/tmux wrappers, ProjectsMD CLI, Hermes dashboard SDK components/hooks/utils/fetchJSON, plain JS or lightweight Vite library build configured as an IIFE with React externalized.

Current repo baseline:
- Repo: /home/am/projectsmd-hermes
- Plugin name: projectsmd
- Route: /projects
- API prefix: /api/plugins/projectsmd
- Manifest: dashboard/manifest.json
- Backend: projectsmd_dashboard/*.py
- Frontend bundle: dashboard/dist/index.js
- Current project.md phase: build
- Current blocker: none
- Current next action from project.md: fix/highest-severity frontend production polish issues.

Non-negotiables:
- Dashboard binds to 127.0.0.1 by default. Do not design mutation/tmux endpoints for exposed 0.0.0.0 use without an explicit warning and extra auth.
- Do not prefix plugin routes with /api/plugins/projectsmd in plugin_api.py or projectsmd_dashboard/api.py; Hermes adds that mount prefix.
- Use SDK.components, SDK.hooks, SDK.utils, SDK.fetchJSON or SDK.pluginAPI. Do not bundle React.
- project.md stays the source of truth.
- Orchestrator is the only default writer to project.md; subagents propose updates through queued diffs.
- All mutations go through allowlisted ProjectsMD CLI wrappers or explicit safe file-write approval flows.
- No alert(), prompt(), location.reload(), innerHTML, or unescaped HTML. Use modal forms, inline errors, toasts, and React text nodes.
- Every feature needs tests and local verification before commit.

---

## Milestone 0: Freeze the current contract and safety baseline

Objective: Make sure the current plugin behavior is understood and protected before expanding it.

Files:
- Modify: tests/test_dashboard_bundle.py
- Modify: tests/test_plugin_api_contract.py
- Modify: tests/test_safety.py
- Modify: tests/test_projectsmd_cli.py
- Read-only reference: dashboard/dist/index.js
- Read-only reference: projectsmd_dashboard/api.py

Steps:
1. Add frontend smoke assertions that dashboard/dist/index.js does not contain innerHTML, alert(, prompt(, location.reload, or dangerouslySetInnerHTML.
2. Add smoke assertions that the bundle uses SDK.pluginAPI fallback and SDK.components/SDK.hooks.
3. Add API contract tests for every mutating endpoint to verify missing path returns 400 and missing project.md returns 404.
4. Add tests that launch_run refuses unsafe commands through projectsmd_dashboard.safety.check_command.
5. Run:
   - python3 -m pytest tests/test_dashboard_bundle.py tests/test_plugin_api_contract.py tests/test_safety.py -q
   - node --check dashboard/dist/index.js
6. Commit: test: lock dashboard safety contract

Acceptance:
- Tests fail if a future change reintroduces alert/prompt/reload/innerHTML.
- Existing routes remain mounted under /api/plugins/projectsmd/*.

---

## Milestone 1: Create a maintainable frontend source layout

Objective: Stop editing a 600+ line generated-looking bundle directly.

Files:
- Create: dashboard/src/app.js
- Create: dashboard/src/api.js
- Create: dashboard/src/components/layout.js
- Create: dashboard/src/components/project-list.js
- Create: dashboard/src/components/project-detail.js
- Create: dashboard/src/components/forms.js
- Create: dashboard/src/components/toast.js
- Create: dashboard/src/components/runs.js
- Create: dashboard/src/components/queue.js
- Create: dashboard/src/components/settings.js
- Create: dashboard/scripts/build_frontend.py or package.json + scripts/build-dashboard.js
- Modify: dashboard/dist/index.js
- Modify: tests/test_dashboard_bundle.py
- Modify: README.md

Steps:
1. Split current dashboard/dist/index.js into source modules without changing behavior.
2. Use a tiny build step that concatenates modules into one IIFE, or add Vite with React externalized to window.__HERMES_PLUGIN_SDK__.React.
3. Keep dashboard/dist/index.js committed because Hermes loads it directly.
4. Add a test that source files exist and dist bundle has the registration line.
5. Add README instructions: build frontend, run tests, install plugin, start dashboard.
6. Run:
   - python3 dashboard/scripts/build_frontend.py, or npm run build:dashboard if Vite is chosen
   - node --check dashboard/dist/index.js
   - python3 -m pytest tests/test_dashboard_bundle.py -q
7. Commit: refactor: split dashboard frontend source

Acceptance:
- No behavior change yet.
- Future UI work happens in dashboard/src, not directly in dist.

---

## Milestone 2: Make project discovery and onboarding first-class

Objective: A new user can open http://127.0.0.1:9119/projects and immediately understand what to do.

Files:
- Modify: projectsmd_dashboard/config.py
- Modify: projectsmd_dashboard/api.py
- Modify: projectsmd_dashboard/project_scan.py
- Modify: dashboard/src/components/settings.js
- Modify: dashboard/src/components/project-list.js
- Modify: dashboard/src/components/forms.js
- Modify: tests/test_config.py
- Modify: tests/test_dashboard_plugin.py
- Modify: tests/test_plugin_api_contract.py

Features:
- Setup checklist card: projectsmd available, tmux available, Hermes available, plugin installed, roots configured.
- Root manager with add/remove root, path validation, scan status, empty-state CTA.
- Create Project modal supporting normal and brownfield init.
- Search/filter/sort by name, path, phase, owner, tags, blocked status, updated time.
- Recent/favorite projects persisted in plugin config.

Steps:
1. Extend config model to include project_roots, favorites, recent_project_paths, sort, filters.
2. Add backend validation for roots: exists, directory, readable, project count.
3. Add POST /projects scan refresh endpoint only if needed; otherwise use GET /projects.
4. Add Create Project modal that calls POST /projects with name, owner, description, core_value, tags, brownfield.
5. Add optimistic UI for root changes with rollback on API failure.
6. Add empty states: no roots, no projects found, projectsmd missing.
7. Run:
   - python3 -m pytest tests/test_config.py tests/test_dashboard_plugin.py tests/test_plugin_api_contract.py -q
   - node --check dashboard/dist/index.js
8. Commit: feat: add project onboarding and root management

Acceptance:
- User can configure roots and create a new project without terminal commands.
- Missing dependencies are explained in the UI with exact fix commands.

---

## Milestone 3: Build a native project.md editor experience

Objective: Replace raw markdown dependence with structured, easy ProjectMD operations.

Files:
- Modify: projectsmd_dashboard/models.py
- Modify: projectsmd_dashboard/project_scan.py
- Modify: projectsmd_dashboard/projectsmd_cli.py
- Modify: projectsmd_dashboard/api.py
- Modify: dashboard/src/components/project-detail.js
- Modify: dashboard/src/components/forms.js
- Modify: tests/test_projectsmd_cli.py
- Modify: tests/test_dashboard_plugin.py
- Modify: tests/test_plugin_api_contract.py

Features:
- Current State editor: phase, last completed, in progress, next action, blockers, notes.
- Requirements panels: validated, active, out of scope.
- Task board grouped by phase with done/block/unblock, add, edit title, delete if supported by CLI or queue diff if not.
- Decisions table with rationale/outcome editing.
- Discoveries list with add/edit support.
- Session summary modal that uses projectsmd session --non-interactive.
- Phase transition modal with preflight validation.
- Archive modal with required final summary.

Steps:
1. Extend parsing model to return structured requirements, tasks with stable ids/numbers, decisions, discoveries, sessions.
2. Add direct API routes only for CLI-supported operations.
3. For unsupported operations, generate proposed full project.md and route through diff queue instead of writing directly.
4. Add inline forms with validation; disable submit until required fields are valid.
5. Add success/error toasts and refresh detail in-place.
6. Run:
   - python3 -m pytest tests/test_projectsmd_cli.py tests/test_dashboard_plugin.py tests/test_plugin_api_contract.py -q
   - projectsmd validate
   - node --check dashboard/dist/index.js
7. Commit: feat: add native project editing workflow

Acceptance:
- A user can manage the common ProjectsMD lifecycle from the UI without editing markdown manually.
- Every unsupported edit is reviewed through a diff before applying.

---

## Milestone 4: Add safe diff queue and snapshot workflows

Objective: Make project.md changes auditable and reversible.

Files:
- Modify: projectsmd_dashboard/update_queue.py
- Modify: projectsmd_dashboard/diff_preview.py
- Modify: projectsmd_dashboard/snapshots.py
- Modify: projectsmd_dashboard/api.py
- Modify: dashboard/src/components/queue.js
- Modify: dashboard/src/components/project-detail.js
- Modify: tests/test_update_queue.py
- Modify: tests/test_diff_preview.py
- Modify: tests/test_snapshots.py
- Modify: tests/test_plugin_api_contract.py

Features:
- Diff preview with side-by-side and unified modes.
- Pending update drawer with proposed source, creator, timestamp, reason, related run/assignment.
- Approve/reject with optional comment.
- Snapshot before every approved write.
- Snapshot history and restore flow with confirmation.
- File lock around writes.

Steps:
1. Add metadata fields to queued update records: created_by, reason, run_id, assignment_id, created_at.
2. Ensure approve_update writes through a lock and snapshots first.
3. Add API routes for snapshot list, restore, queue approve/reject with comments.
4. Render diffs using text nodes only; never innerHTML.
5. Add tests for escaping malicious diff content.
6. Run:
   - python3 -m pytest tests/test_update_queue.py tests/test_diff_preview.py tests/test_snapshots.py tests/test_plugin_api_contract.py -q
   - node --check dashboard/dist/index.js
7. Commit: feat: add approval queue and snapshots

Acceptance:
- Any risky project.md change can be inspected, approved, rejected, and reverted.

---

## Milestone 5: Make orchestrator and subagent runs usable

Objective: The Projects tab becomes an agentic project cockpit, not just a browser.

Files:
- Modify: projectsmd_dashboard/roster.py
- Modify: projectsmd_dashboard/prompts.py
- Modify: projectsmd_dashboard/tmux_runtime.py
- Modify: projectsmd_dashboard/run_registry.py
- Modify: projectsmd_dashboard/event_protocol.py
- Modify: projectsmd_dashboard/api.py
- Modify: dashboard/src/components/runs.js
- Create: dashboard/src/components/roster-editor.js
- Create: dashboard/src/components/agent-board.js
- Modify: tests/test_roster.py
- Modify: tests/test_prompts.py
- Modify: tests/test_tmux_runtime.py
- Modify: tests/test_run_registry.py
- Modify: tests/test_event_protocol.py

Features:
- Roster editor with default roles: Orchestrator, Define, Design, Build, Verify, Ship, Research, Review.
- Per-role provider, model, toolsets, phase scope, max parallel tasks, write permission, checkpoint policy.
- Launch run form with objective, target phase/task, role profile, dry-run preview.
- tmux lifecycle: launch, tail, poll, kill, mark completed/failed/killed.
- Agent board: active role, assignment, status, output tail, subagent count, blockers.
- Structured protocol parser for PROJECT_ASSIGNMENT, PROJECT_PROGRESS, PROJECT_DISCOVERY, PROJECT_BLOCKER, PROJECT_CHECKPOINT, PROJECT_RESULT, PROJECT_MD_UPDATE_PROPOSED.
- Proposed updates from agents go into the queue, not straight into project.md.

Steps:
1. Fix launch command to use the real Hermes CLI shape for this environment. Prefer: hermes chat -q <prompt> -s projectsmd --pass-session-id, unless local Hermes docs confirm another command.
2. Add command-generation tests so command shape cannot regress.
3. Store run roster snapshot in SQLite meta at launch.
4. Add event parser for PROJECT_* lines plus plain stdout events.
5. Add polling UI with run detail drawer and kill button.
6. Add safety policy UI that clearly shows what commands are allowed.
7. Run:
   - python3 -m pytest tests/test_roster.py tests/test_prompts.py tests/test_tmux_runtime.py tests/test_run_registry.py tests/test_event_protocol.py -q
   - node --check dashboard/dist/index.js
   - manual smoke: launch a harmless run against a temp project and kill it
8. Commit: feat: add orchestrator run cockpit

Acceptance:
- User can launch, monitor, stop, and inspect Hermes project runs from /projects.
- Agent proposals are visible and reviewable.

---

## Milestone 6: Add quality gates, GitHub, and shipping views

Objective: Support the whole project lifecycle through verify and ship.

Files:
- Modify: projectsmd_dashboard/gates.py
- Modify: projectsmd_dashboard/github_integration.py
- Modify: projectsmd_dashboard/ship_checklist.py
- Modify: projectsmd_dashboard/api.py
- Create: dashboard/src/components/quality-gates.js
- Create: dashboard/src/components/github-panel.js
- Create: dashboard/src/components/ship-checklist.js
- Modify: tests/test_gates.py
- Modify: tests/test_github_integration.py
- Modify: tests/test_ship_checklist.py

Features:
- Quality gates panel: tests, lint, build, validate project.md, manual review, docs complete.
- One-click run gates with output and status history.
- GitHub repo info, open issues, PRs, CI status if gh/auth is available.
- Ship checklist: docs, release notes, tag, GitHub pushed, dashboard plugin installed, smoke tested.
- Phase transition guard: warn if verify/ship gates are failing.

Steps:
1. Ensure gate commands are allowlisted and project-local.
2. Add API response models for gate status, GitHub status, ship checklist.
3. Add UI panels to project detail, collapsed by default below core workflow.
4. Add clear fallback states when gh or tokens are unavailable.
5. Run:
   - python3 -m pytest tests/test_gates.py tests/test_github_integration.py tests/test_ship_checklist.py -q
   - node --check dashboard/dist/index.js
6. Commit: feat: add quality gates and ship workflow

Acceptance:
- User can see whether a project is ready to transition/ship from the dashboard.

---

## Milestone 7: Production polish and accessibility pass

Objective: Make it feel YC-quality and native to Hermes.

Files:
- Modify: dashboard/src/**/*.js
- Modify: dashboard/dist/style.css
- Modify: dashboard/manifest.json
- Modify: tests/test_dashboard_bundle.py
- Create: docs/production-readiness.md

Features:
- Hermes Projects branded header with docs/settings links.
- Responsive layout for laptop/tablet/mobile widths.
- Keyboard navigation for list, modals, command actions, queue drawer.
- aria-labels on all icon/action buttons.
- Focus trap and escape-to-close for modals.
- Loading states on every action button.
- Empty/error/success states for every panel.
- Copy-to-clipboard for errors, commands, run ids, project paths.
- Theme-safe colors using Hermes/shadcn tokens; minimize custom CSS.
- Motion only where helpful, respect reduced motion if available.

Steps:
1. Create a production readiness checklist doc and check off each gap.
2. Add bundle smoke tests for no hardcoded dangerous UX patterns.
3. Add test strings for aria-label, role="dialog", Escape handling, and loading state helpers.
4. Manually test in the dashboard at http://127.0.0.1:9119/projects.
5. Run:
   - python3 -m pytest tests/test_dashboard_bundle.py -q
   - node --check dashboard/dist/index.js
6. Commit: polish: production-ready Projects dashboard UX

Acceptance:
- No alert/prompt/reload.
- Usable by keyboard.
- Looks native in Hermes dashboard.
- Works at narrow and wide widths.

---

## Milestone 8: Docs, install, and local deployment verification

Objective: Make install/use obvious and prove it works at 127.0.0.1.

Files:
- Modify: README.md
- Modify: docs/dashboard-plugin.md
- Modify: scripts/install-dashboard-plugin.sh
- Modify: scripts/smoke-test-dashboard-plugin.sh
- Create: docs/user-guide.md
- Create: docs/operator-guide.md
- Create: docs/security.md

Steps:
1. Document install:
   - git clone https://github.com/am423/projectsmd-hermes.git
   - cd projectsmd-hermes
   - cargo install --path .
   - bash scripts/install-dashboard-plugin.sh
   - hermes dashboard --no-open
   - open http://127.0.0.1:9119/projects
2. Document plugin architecture and API routes.
3. Document security model: localhost only, no arbitrary shell, project.md single-writer policy, snapshots.
4. Extend smoke-test script to check health, config, projects list, manifest, and frontend bundle syntax.
5. Run:
   - bash scripts/install-dashboard-plugin.sh
   - bash scripts/smoke-test-dashboard-plugin.sh
   - python3 -m pytest -q
   - . "$HOME/.cargo/env" && cargo test
6. Commit: docs: document Projects dashboard plugin

Acceptance:
- A new user can install and open /projects without reverse-engineering the repo.
- Smoke test proves the addon is visible and API is reachable.

---

## Milestone 9: Final verification, project.md wrap-up, and push

Objective: Finish cleanly and leave the repo ready for Adam to dogfood.

Files:
- Modify: project.md via projectsmd CLI only
- Check: all changed files

Steps:
1. Run full verification:
   - python3 -m pytest -q
   - . "$HOME/.cargo/env" && cargo test
   - node --check dashboard/dist/index.js
   - bash scripts/smoke-test-dashboard-plugin.sh
   - projectsmd validate
2. Start/restart Hermes dashboard locally and manually verify:
   - http://127.0.0.1:9119/projects loads
   - health panel is green
   - project list scans roots
   - create temp project works
   - add task/decision/discovery works
   - queue diff approve/reject works
   - orchestrator launch dry run works
   - kill run works
   - no duplicate Projects/ProjectsMD sidebar tabs
3. Update project.md with completed tasks and discoveries using projectsmd commands.
4. Commit final changes in logical commits if not already committed.
5. Push to GitHub: git push origin main
6. Verify GitHub remote and latest commit:
   - gh repo view am423/projectsmd-hermes
   - git status --short
   - git log --oneline -3
7. Commit/session wrap-up if needed: projectsmd session --non-interactive --summary "Implemented fully featured Hermes Projects dashboard UI."

Acceptance:
- Git working tree is clean except intentional local artifacts like coverage files removed or gitignored.
- GitHub has the latest commits.
- Dashboard works locally at 127.0.0.1.

---

## Recommended execution order

1. Milestone 0 first. It prevents regressions and catches current production issues.
2. Milestone 1 second. It makes the rest faster and safer.
3. Milestones 2-4 create the easy project management UI.
4. Milestone 5 adds the agentic differentiator.
5. Milestone 6 closes verify/ship lifecycle support.
6. Milestones 7-9 make it production quality, documented, verified, and pushed.

## Definition of done

The feature is done when:
- /projects appears as a Hermes dashboard addon at 127.0.0.1.
- A user can discover/create projects, edit lifecycle state, manage tasks, record decisions/discoveries/sessions, review diffs, restore snapshots, configure roots, launch/monitor/stop orchestrator runs, inspect subagent progress, run quality gates, and ship from the UI.
- project.md remains the source of truth.
- Mutations are safe, auditable, and reversible.
- UI has no alert/prompt/reload/XSS shortcuts.
- Tests, cargo test, node syntax check, smoke test, and projectsmd validate pass.
- Repo is pushed to am423/projectsmd-hermes.
