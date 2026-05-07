# Fully Featured ProjectsMD Dashboard Tutorial and Polish Implementation Plan

> For Hermes: Use subagent-driven-development skill to implement this plan task-by-task.

Goal: Make the ProjectsMD dashboard fully featured and self-explanatory in the main UI, remove the forced welcome dialog, replace it with an optional Tutorial button, and polish the UI until spacing, padding, visual hierarchy, and interaction states are gorgeous and consistent.

Architecture: Treat this as a product-completion pass, not a copy-trimming pass. The dashboard itself is the source of truth for product capabilities; the optional tutorial is only a user-invoked guide that explains already-visible workflows and must never be required to use the product. Keep the plugin standalone, keep all frontend changes in dashboard/src/app.js, regenerate dashboard/dist/index.js, and preserve the safety contract: no innerHTML, no alert(), no prompt(), no full-page reload UX.

Tech Stack: Python pytest, ProjectsMD CLI, FastAPI plugin API, dashboard/src/app.js IIFE frontend bundle, dashboard/scripts/build_frontend.py, Hermes dashboard SDK components.

Design Direction: Linear-quality dark dashboard: precise spacing on an 8px grid, subtle translucent panels, consistent card padding, crisp borders, restrained violet/indigo accent for primary actions, strong typography hierarchy, no fuzzy/blurred overlays, no cramped card titles, no uneven button rows.

---

## Current Findings

1. Duplicate roots are real, but they are not the cause of 0/38 tasks done.
   - Live health endpoint returns roots:
     - /home/am/projects
     - /home/am/projectsmd-hermes
     - /home/am/projectsmd-hermes
   - projectsmd_dashboard/project_scan.py deduplicates project.md files by resolved path, so the duplicated root is noisy but does not double-count this project.

2. 0/38 tasks done is coming directly from /home/am/projectsmd-hermes/project.md.
   - All 38 task checkboxes are currently unchecked.
   - projectsmd status also reports 0/38, matching the dashboard.
   - This is not a refresh bug and not caused by duplicate roots.

3. The 1 blocked task is a parser false positive.
   - /home/am/projectsmd-hermes/project.md line 129 contains:
     - [ ] Task 21: Task done/blocked use only text markers ...
   - count_tasks() treats any task body containing blocked or blocker as blocked.
   - That line describes UI copy, not an actual blocked task.

4. The current forced welcome dialog is the wrong UX.
   - It blocks the dashboard on page load.
   - It lists features that are incomplete or not obvious in the UI.
   - It should be removed from automatic render and replaced with a visible Tutorial button.

5. The dashboard still has visual polish gaps.
   - Multiple panels use inconsistent CardHeader/CardContent padding.
   - Some content sits too close to section titles or card borders.
   - Controls have uneven heights and ad hoc spacing.
   - The right rail, detail column, setup checklist, roots panel, run panels, and lifecycle cards need shared layout constants.

---

## Optional Tutorial Feature Contract

The tutorial is optional help, not a required onboarding gate. Users must be able to discover and use every major workflow from the dashboard itself without opening the tutorial. The Tutorial button may describe these workflows only after the UI implements them visibly:

1. Project discovery
   - Browse discovered project.md files.
   - Search and filter by name/path/owner/tag/phase.
   - Rescan without page reload.
   - Manage roots, with duplicate roots ignored and explained.

2. Project creation
   - Create a new project from the UI.
   - Validate required fields inline.
   - Select the new project after creation.

3. Project detail reading
   - Show current state: phase, last completed, in progress, next action, blockers, notes.
   - Show tasks, decisions, discoveries, and requirements as structured sections.
   - Show raw/diff affordances without unsafe HTML.

4. Mutations
   - Add task.
   - Mark task done.
   - Block task with an inline reason form, not prompt().
   - Unblock task.
   - Add decision with rationale/outcome fields.
   - Add discovery.
   - Add or update current-state fields if backend support exists; otherwise do not mention it in tutorial.

5. Approval queue and diff preview
   - Paste proposed project.md content.
   - Preview diff.
   - Queue for approval.
   - Show pending queue items.
   - Approve/reject with inline feedback.
   - Snapshot-before-write remains intact.

6. Orchestrator and runs
   - Launch a tmux-backed Hermes run when tmux is available.
   - Pick a role.
   - See run status, recent output, and history.
   - Stop/kill an active run if backend support exists; otherwise do not mention stop/kill in tutorial.

7. Verify and ship
   - Show quality gates.
   - Show GitHub status/integration panel.
   - Show ship checklist.
   - Make stub/unavailable states explicit and useful.

8. Keyboard shortcuts
   - Ctrl+R rescans.
   - Ctrl+N opens the Roots/add-project-root affordance or a path navigation affordance. If it only shows guidance, the tutorial must say that.
   - Escape clears selection or closes tutorial/modal.

---

## Task 1: Add regression tests for duplicate root handling

Objective: Prove duplicate configured/default roots do not duplicate project rows and make the intended behavior explicit.

Files:
- Modify: tests/test_dashboard_plugin.py
- Test: tests/test_dashboard_plugin.py

Step 1: Add a test that scans the same root twice.

Add a pytest/unittest case that creates one project.md under a temp root, calls scan_projects([root, root]), and asserts exactly one project is returned.

Step 2: Run the focused test.

Run:
python -m pytest tests/test_dashboard_plugin.py -k duplicate -q

Expected: PASS.

Step 3: Commit after implementation.

git add tests/test_dashboard_plugin.py
git commit -m "test: cover duplicate project root scanning"

---

## Task 2: Deduplicate configured roots in health/config output

Objective: Remove the visible duplicate /home/am/projectsmd-hermes root from health and Roots UI.

Files:
- Modify: projectsmd_dashboard/config.py
- Modify: projectsmd_dashboard/api.py if health endpoint merges defaults directly there
- Test: tests/test_config.py or tests/test_plugin_api_contract.py

Step 1: Add a helper such as dedupe_roots(roots).

Behavior:
- expanduser
- resolve existing paths when possible
- preserve first occurrence order
- tolerate missing paths by normalizing string paths without throwing

Step 2: Use the helper in default_config(), load_config() normalization, save_config(), or the API boundary that returns roots.

Acceptance:
- health roots should list /home/am/projectsmd-hermes once.
- root_status should also contain one entry per unique root.
- Roots UI should show a single row per root.

Step 3: Add tests.

Run:
python -m pytest tests/test_config.py tests/test_plugin_api_contract.py -q

Expected: PASS.

Step 4: Commit.

git add projectsmd_dashboard/config.py projectsmd_dashboard/api.py tests/test_config.py tests/test_plugin_api_contract.py
git commit -m "fix: deduplicate dashboard project roots"

---

## Task 3: Fix blocked-task detection semantics

Objective: Stop counting task text that merely contains the word blocked as an active blocker.

Files:
- Modify: projectsmd_dashboard/project_scan.py
- Modify: tests/test_dashboard_plugin.py

Step 1: Write failing tests for these cases.

Cases:
- "- [ ] Task done/blocked use only text markers" must not count as blocked.
- "- [ ] Fix deploy <!-- blocked: waiting on token -->" must count as blocked.
- If ProjectsMD supports explicit blocked syntax "- [!] ...", add support and test it.

Step 2: Patch TASK_RE and count logic.

Recommended behavior:
- Accept marks: space, x, X, !
- done when mark is x/X
- blocked when mark is ! OR the task body contains an explicit metadata marker like <!-- blocked: ... -->
- do not classify based on plain prose containing blocked/blocker.

Step 3: Patch parse_tasks() similarly so detail task rows agree with summary counts.

Step 4: Run tests.

python -m pytest tests/test_dashboard_plugin.py -q

Expected: PASS and project summary for /home/am/projectsmd-hermes becomes blocked: 0.

Step 5: Commit.

git add projectsmd_dashboard/project_scan.py tests/test_dashboard_plugin.py
git commit -m "fix: count only explicit blocked tasks"

---

## Task 4: Create a feature coverage test for optional tutorial accuracy

Objective: Ensure the optional tutorial maps to visible, implemented UI controls or panels, while the dashboard remains fully usable without opening it.

Files:
- Create or modify: tests/test_dashboard_tutorial_contract.py
- Modify: dashboard/src/app.js only after the failing test exists

Step 1: Add a test that forbids the auto-mounted welcome dialog.

Assertions:
- dashboard/src/app.js does not render h(OnboardingWalkthrough) automatically inside ProjectsPage.
- bundle does not include a forced full-screen tutorial overlay on initial render.

Step 2: Add a test that verifies the optional Tutorial button.

Assertions against dashboard/src/app.js or dashboard/dist/index.js:
- Contains visible label "Tutorial".
- Contains state such as showTutorial or equivalent.
- Tutorial opens on button click, not page load.
- Tutorial can close via button and Escape.
- No workflow is hidden behind the tutorial; core controls are visible in the dashboard itself.

Step 3: Add a test for tutorial-feature strings.

The tutorial may include only features that have matching visible controls/panels. Core controls that must be usable without opening the tutorial:
- Search projects
- Filter by phase
- Rescan
- New Project
- Roots
- Add task
- Add decision
- Add discovery
- Diff preview / Queue
- Queue for approval
- Launch run
- Orchestrator Runs or Runs
- Verify & Ship or Quality gates

Step 4: Run the test and confirm it fails before implementation.

python -m pytest tests/test_dashboard_tutorial_contract.py -q

Expected: FAIL until Tasks 5-8 are implemented.

Step 5: Commit the failing/then-passing test with its implementation task, not separately if CI would fail.

---

## Task 5: Replace forced welcome dialog with optional Tutorial button

Objective: Remove the automatic welcome interruption and expose tutorial as optional, user-clicked help. The dashboard must be understandable and usable without it.

Files:
- Modify: dashboard/src/app.js
- Modify: dashboard/dist/index.js via rebuild
- Test: tests/test_dashboard_tutorial_contract.py

Step 1: Remove automatic tutorial mounting.

Change ProjectsPage from rendering both ProjectsPageInner and OnboardingWalkthrough automatically to rendering only ProjectsPageInner. The tutorial should be controlled by state inside ProjectsPageInner or a small top-level wrapper.

Step 2: Add a Tutorial button in the header action row.

Header actions should become:
- Tutorial
- New Project
- Rescan
- Docs

The Tutorial button should be a secondary/ghost button with the same height and padding as New Project and Rescan.

Step 3: Implement TutorialModal.

Requirements:
- Opens only when Tutorial is clicked.
- Uses no backdrop blur.
- Has a crisp dim overlay: bg-background/80.
- Uses consistent modal padding: p-5, header gap-2, body gap-4, footer gap-2.
- Has close button and Escape support.
- Has Back/Next/Done navigation.
- Does not use alert(), prompt(), innerHTML, or location.reload.

Step 4: Rebuild and test.

python3 dashboard/scripts/build_frontend.py
node --check dashboard/dist/index.js
python -m pytest tests/test_dashboard_tutorial_contract.py tests/test_dashboard_bundle.py -q

Step 5: Commit.

git add dashboard/src/app.js dashboard/dist/index.js tests/test_dashboard_tutorial_contract.py
git commit -m "feat: replace welcome dialog with tutorial button"

---

## Task 6: Implement missing mutation UI promised by tutorial

Objective: Make the UI fully featured for task, decision, and discovery workflows.

Files:
- Modify: dashboard/src/app.js
- Modify: projectsmd_dashboard/api.py only if missing endpoints are absent
- Modify: tests/test_plugin_api_contract.py if endpoints are added/changed
- Modify: dashboard/dist/index.js via rebuild

Step 1: Inventory existing backend endpoints.

Use search_files/read_file on projectsmd_dashboard/api.py and tests/test_plugin_api_contract.py. Confirm endpoints exist for:
- POST /projects/{id}/tasks
- POST /projects/{id}/tasks/{task_id}/done
- POST /projects/{id}/tasks/{task_id}/block
- POST /projects/{id}/tasks/{task_id}/unblock
- POST /projects/{id}/decisions
- POST /projects/{id}/discoveries

Step 2: Add missing UI forms.

In ProjectDetail, add compact action buttons and inline modal/forms for:
- Add task: title, phase.
- Add decision: decision, rationale, outcome.
- Add discovery: text.
- Block task: reason field.

Step 3: Use one reusable modal/form component.

Avoid duplicate one-off padding. Create constants:
- MODAL_PANEL = "w-full max-w-lg rounded-xl border border-border bg-background p-5 shadow-xl"
- FORM_STACK = "flex flex-col gap-3"
- FIELD_LABEL = "text-xs font-medium text-muted-foreground"
- FIELD_INPUT = COMPACT_FIELD or shared full-width variant
- ACTION_ROW = "flex items-center justify-end gap-2 pt-2"

Step 4: Add loading/disabled states per action.

Each mutation button should disable only the active action, show a small spinner or loading text, and update detail + project list silently when complete.

Step 5: Inline validation.

No alert/prompt. Required fields show toast or inline text.

Step 6: Tests.

Run:
python -m pytest tests/test_plugin_api_contract.py tests/test_dashboard_bundle.py tests/test_safety.py -q

Step 7: Commit.

git add dashboard/src/app.js dashboard/dist/index.js projectsmd_dashboard/api.py tests/test_plugin_api_contract.py
git commit -m "feat: add full project mutation forms"

---

## Task 7: Make Diff / Queue a first-class workflow

Objective: Ensure tutorial claims about diff/approval are backed by an obvious, polished UI.

Files:
- Modify: dashboard/src/app.js
- Modify: dashboard/dist/index.js via rebuild
- Test: tests/test_dashboard_bundle.py or tests/test_dashboard_tutorial_contract.py

Step 1: Promote Diff preview / Queue within ProjectDetail.

Keep it collapsible if needed, but style it as a clear section with:
- title row
- short description
- textarea
- Preview diff button if backend supports preview endpoint
- Queue for approval button
- Show pending button
- pending queue list with Approve/Reject

Step 2: Add empty/loading/error states.

Examples:
- "No pending updates"
- "Queued updates are written only after approval; a snapshot is created first."

Step 3: Keep list rendering safe.

No innerHTML. Diff text must render as text inside pre/code or mapped lines.

Step 4: Rebuild/test.

python3 dashboard/scripts/build_frontend.py
node --check dashboard/dist/index.js
python -m pytest tests/test_dashboard_tutorial_contract.py tests/test_safety.py -q

Step 5: Commit.

git add dashboard/src/app.js dashboard/dist/index.js tests/test_dashboard_tutorial_contract.py
git commit -m "feat: polish approval queue workflow"

---

## Task 8: Complete orchestrator/run-management UI promised by tutorial

Objective: Make Launch run and Runs panels feel production-ready, not stubby.

Files:
- Modify: dashboard/src/app.js
- Modify: projectsmd_dashboard/api.py / tmux_runtime.py only if current endpoints lack status/history/stop support
- Modify: dashboard/dist/index.js via rebuild
- Test: tests/test_plugin_api_contract.py tests/test_dashboard_tutorial_contract.py

Step 1: Inventory existing run endpoints.

Confirm backend supports:
- create run
- list runs for project
- read run status/output
- stop/kill run if available

Step 2: Polish LaunchPanel.

Requirements:
- task textarea has a clear label and helper text.
- role selector has readable options.
- launch button disabled until project + task exist.
- tmux unavailable state is visible from health check.
- success toast includes run id.

Step 3: Polish RunPanel.

Requirements:
- status badges with distinct visual states.
- latest output in a readable monospace block.
- refresh/reload action.
- stop/kill button only if backend supports it.
- empty state: "No runs yet. Launch one from this panel."

Step 4: Ensure live polling refreshes run status without flicker.

Use existing silent 2s polling; avoid loading spinners on every tick.

Step 5: Rebuild/test/commit.

python3 dashboard/scripts/build_frontend.py
node --check dashboard/dist/index.js
python -m pytest tests/test_plugin_api_contract.py tests/test_dashboard_tutorial_contract.py -q

git add dashboard/src/app.js dashboard/dist/index.js projectsmd_dashboard/api.py projectsmd_dashboard/tmux_runtime.py tests/
git commit -m "feat: complete run management dashboard"

---

## Task 9: Redesign dashboard spacing and visual system

Objective: Fix all padding/layout issues and make the UI gorgeous, crisp, and consistent.

Files:
- Modify: dashboard/src/app.js
- Modify: dashboard/dist/index.js via rebuild
- Test: tests/test_dashboard_bundle.py

Step 1: Define shared layout constants at the top of app.js.

Add/standardize:
- PAGE = "mx-auto flex w-full max-w-[1600px] flex-col gap-5 p-4 sm:p-5 lg:p-6"
- SECTION_GRID = "grid gap-4 lg:grid-cols-1 xl:grid-cols-[23rem_minmax(0,1fr)_19rem]"
- CARD_BASE = "rounded-xl border border-border/80 bg-card/60 shadow-sm"
- CARD_HEADER = "px-4 pb-2 pt-4"
- CARD_CONTENT = "px-4 pb-4 pt-2"
- CARD_CONTENT_STACK = CARD_CONTENT + " flex flex-col gap-3"
- PANEL_HEADER = "px-4 pb-2 pt-4"
- PANEL_CONTENT = "px-4 pb-4 pt-2"
- CONTROL_ROW = "flex flex-wrap items-center gap-2"
- BUTTON_SM = "h-8 px-3 py-1.5 text-xs"
- INPUT_BASE = "h-9 rounded-md border border-border bg-background px-3 text-sm"
- TEXTAREA_BASE = "min-h-28 rounded-md border border-border bg-background px-3 py-2 text-sm"

Step 2: Apply constants across the whole dashboard.

Targets:
- Header action row.
- Stat cards.
- Setup checklist.
- Search/filter bar.
- Project list card.
- Detail header.
- Task/decision/discovery sections.
- Diff / Queue.
- Launch panel.
- Run panel.
- Verify & Ship / lifecycle panels.
- Roots panel.
- Create project modal.
- Tutorial modal.
- Toasts.

Step 3: Fix known padding failures.

Rules:
- No CardContent with pt-0 directly below a visible CardHeader unless the component has its own top spacing.
- No title text touching a border or adjacent control.
- Every card header gets top padding and bottom breathing room.
- Every right-rail card has identical horizontal padding.
- Compact buttons in side panels share exact height.
- Textareas and inputs align to the same left/right edge as buttons.

Step 4: Upgrade visual hierarchy.

Use restrained Linear-like polish inside existing Hermes theme:
- Stronger hero/header: eyebrow + title + compact subtitle.
- Cards: rounded-xl, subtle border, consistent shadow.
- Primary actions: clear accent, not too bright.
- Secondary actions: ghost/outline.
- Status: phase badges with distinct but muted colors.
- Empty states: centered, concise, useful next action.

Step 5: Add bundle tests for style regressions.

Tests should forbid:
- "pt-0" on CardContent near key cards unless allowlisted.
- "backdrop-blur" in tutorial/onboarding modal.
- duplicate one-off button class strings if shared constants exist.
- stale forced welcome copy.

Step 6: Rebuild/test/commit.

python3 dashboard/scripts/build_frontend.py
node --check dashboard/dist/index.js
python -m pytest tests/test_dashboard_bundle.py tests/test_safety.py -q

git add dashboard/src/app.js dashboard/dist/index.js tests/test_dashboard_bundle.py
git commit -m "style: unify projects dashboard spacing"

---

## Task 10: Add compact UI explanations for task counters

Objective: Prevent future confusion about 0/38 and blocked counts without making the UI noisy.

Files:
- Modify: dashboard/src/app.js
- Modify: dashboard/dist/index.js via rebuild

Step 1: Add helper text near Tasks stat or DetailHeader progress.

Suggested copy:
"Counts come from project.md checkboxes. Mark tasks done to move progress."

Step 2: Add blocker helper text.

Suggested copy:
"Blocked means explicit [!] or blocked metadata, not plain text mentioning blocked."

Step 3: Keep it compact.

Use a tooltip, muted caption, or info row. Do not add another modal.

Step 4: Rebuild/syntax-check/commit.

python3 dashboard/scripts/build_frontend.py
node --check dashboard/dist/index.js

git add dashboard/src/app.js dashboard/dist/index.js
git commit -m "docs: clarify dashboard task counters"

---

## Task 11: Update optional tutorial copy after UI completion

Objective: Ensure the optional Tutorial button accurately explains major workflows for users who ask for help, while the main dashboard remains self-explanatory.

Files:
- Modify: dashboard/src/app.js
- Modify: dashboard/dist/index.js via rebuild
- Test: tests/test_dashboard_tutorial_contract.py

Step 1: Write final tutorial steps.

Suggested sequence:
- Overview: "Hermes Projects turns project.md into a live dashboard for planning, updates, and agent runs."
- Discover: "Use Roots, Search, filters, and Rescan to control which project.md files appear."
- Create: "Use New Project to initialize a tracked project with required fields validated inline."
- Read: "Select a project to inspect current state, tasks, requirements, decisions, discoveries, and session context."
- Update: "Use Add task, Add decision, Add discovery, and task action buttons to safely update project.md."
- Queue: "Use Diff preview / Queue to stage full-file proposals, review pending updates, and approve with snapshot protection."
- Run: "Use Launch run and Runs to start and monitor tmux-backed Hermes orchestrator work."
- Verify: "Use Verify & Ship for quality gates, GitHub status, and release readiness."
- Shortcuts: "Ctrl+R rescans, Ctrl+N opens root guidance, Escape closes dialogs or clears selection."

Step 2: Add tests that stale copy is gone.

Forbidden phrases:
- "welcome dialog"
- "+ Add buttons to add tasks, decisions, and discoveries"
- "Ctrl+N = select project by path"
- Any tutorial mention of a feature that lacks a visible control.

Step 3: Rebuild/test/commit.

python3 dashboard/scripts/build_frontend.py
node --check dashboard/dist/index.js
python -m pytest tests/test_dashboard_tutorial_contract.py -q

git add dashboard/src/app.js dashboard/dist/index.js tests/test_dashboard_tutorial_contract.py
git commit -m "docs: align tutorial with full dashboard workflow"

---

## Task 12: Decide whether to mark implemented project.md tasks done

Objective: Resolve the actual 0/38 project state separately from UI bug fixes.

Files:
- Modify through ProjectsMD CLI: project.md

Step 1: Review the 38 tasks against current implementation.

Do not bulk-check everything blindly. Some tasks are stale production-readiness findings, and some may have been fixed after the review.

Step 2: For each completed item, use the CLI or dashboard mutation flow.

Examples:
projectsmd task done <id>
projectsmd task unblock <id>
projectsmd session --non-interactive --summary "Completed dashboard tutorial, full mutation workflows, run management polish, and spacing cleanup."

Step 3: Re-run status.

projectsmd status

Expected: progress reflects the checked tasks. If no tasks are intentionally marked done, 0/38 remains correct.

Step 4: Commit project.md if changed.

git add project.md
git commit -m "chore: update ProjectsMD dashboard project status"

---

## Task 13: Full verification and local dashboard check

Objective: Prove the implementation is safe, complete, gorgeous, and visible at 127.0.0.1.

Files:
- No new files unless fixes are needed.

Step 1: Run backend/frontend tests.

python -m pytest -q
cargo test
node --check dashboard/dist/index.js
bash scripts/smoke-test-dashboard-plugin.sh

Expected: all pass.

Step 2: Restart dashboard if needed.

hermes dashboard --stop
hermes dashboard --no-open

Step 3: Verify live endpoints.

curl -s http://127.0.0.1:9119/api/plugins/projectsmd/health
curl -s http://127.0.0.1:9119/api/plugins/projectsmd/projects

Expected:
- roots are unique
- blocked count is 0 unless an explicit blocked task exists
- task progress matches project.md checkboxes

Step 4: Manual UI check at 127.0.0.1.

Open:
http://127.0.0.1:9119/projects

Verify:
- No welcome dialog appears on page load.
- Tutorial button is visible in the header as optional help.
- Clicking Tutorial opens a polished modal.
- Tutorial content matches visible UI features.
- Add task, Add decision, Add discovery are all visible and functional.
- Block task asks for a reason inline.
- Diff / Queue workflow is visible and understandable.
- Launch run and Runs panels are polished and have empty/loading/error states.
- Verify & Ship panels are useful, not dead stubs.
- Roots panel shows no duplicate /home/am/projectsmd-hermes.
- Blocked stat is not a false positive.
- Tasks stat matches projectsmd status.
- Padding is consistent across all cards and modals.
- No panel title is cramped against content or borders.
- No fuzzy/blurred overlay appears.
- Layout works at desktop, tablet, and narrow widths.

Step 5: Push and confirm CI.

git status --short
git push
gh run list --repo am423/projectsmd-hermes --branch main --limit 3

Expected: CI passes.
