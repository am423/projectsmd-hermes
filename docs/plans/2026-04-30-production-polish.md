# Production Polish — ProjectsMD Dashboard Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Fix 23 production-readiness gaps identified in review: safety (XSS), UX (mutation feedback, loading states, modals), Hermes branding, visual indicators (phase colors, orchestrator panel, subagent tracking), and Nous compliance.

**Architecture:** All changes are in the single frontend bundle (`dashboard/dist/index.js`, ~443 lines) plus minor updates to `dashboard/manifest.json` and `dashboard/dist/style.css`. No backend changes needed — the API layer is solid. Frontend-only pass.

**Tech Stack:** Vanilla JS (h() hyperscript via Hermes SDK), Hermes SDK components/hooks/utils, CSS.

**Risk:** The bundle is a single file. Merge conflicts are the main risk. Work sequentially, one task per commit.

---

## Phase 1: SAFETY (critical — do first)

### Task 1: Fix XSS in queue list rendering

**Objective:** Replace `innerHTML` string concatenation on line 234 with safe DOM construction.

**Files:**
- Modify: `dashboard/dist/index.js:234-235`

**Step 1: Replace innerHTML concatenation**

Current code (line 234):
```javascript
if (list) list.innerHTML = (res.pending || []).map((u) =>
  `<div class="border-b border-border py-1"><code>${u.id}</code> <pre class="text-xs">${u.diff}</pre><button onclick="fetch('${API_BASE}/projects/${detail.id}/queue/${u.id}/approve',{method:'POST'}).then(()=>location.reload())">Approve</button> <button onclick="fetch('${API_BASE}/projects/${detail.id}/queue/${u.id}/reject',{method:'POST'}).then(()=>location.reload())">Reject</button></div>`
).join("");
```

Replace with safe DOM construction using h():
```javascript
if (list) {
  while (list.firstChild) list.removeChild(list.firstChild);
  (res.pending || []).forEach((u) => {
    const approve = async () => {
      await fetchJSON(`${API_BASE}/projects/${detail.id}/queue/${u.id}/approve`, { method: "POST" });
      loadDetail();
    };
    const reject = async () => {
      await fetchJSON(`${API_BASE}/projects/${detail.id}/queue/${u.id}/reject`, { method: "POST" });
      loadDetail();
    };
    const row = h("div", { className: "border-b border-border py-1 flex flex-col gap-1" },
      h("code", { className: "text-xs" }, u.id),
      h("pre", { className: "text-xs max-h-24 overflow-auto" }, u.diff),
      h("div", { className: "flex gap-1" },
        h("button", { className: "text-xs rounded border border-border px-1.5 py-0.5 hover:bg-accent", onClick: approve }, "Approve"),
        h("button", { className: "text-xs rounded border border-border px-1.5 py-0.5 hover:bg-accent", onClick: reject }, "Reject")));
    list.appendChild(row);
  });
}
```

Note: This requires `loadDetail` to be accessible in scope. Add a `loadDetail` ref via `useCallback` in `ProjectsPageInner` and pass it down to `ProjectDetail`.

**Step 2: Verify no innerHTML usage remains**

```bash
grep -n 'innerHTML' dashboard/dist/index.js
```
Expected: no matches (or only non-user-data innerHTML).

**Step 3: Smoke test**

```bash
node --check dashboard/dist/index.js
```
Expected: no syntax errors.

**Step 4: Commit**

```bash
git add dashboard/dist/index.js
git commit -m "fix: replace innerHTML in queue list with safe DOM construction (XSS)"
```

---

### Task 2: Add debounce to mutation buttons

**Objective:** Prevent rapid-click API spam on Done/Block/Unblock/Add buttons.

**Files:**
- Modify: `dashboard/dist/index.js:134-137` (TaskList buttons)
- Modify: `dashboard/dist/index.js:104` (SectionBlock add button)
- Modify: `dashboard/dist/index.js:207-209` (DecisionTable/Discoveries add buttons)

**Step 1: Add debounce utility**

At the top of the IIFE, after `fetchJSON` definition:
```javascript
function debounce(fn, ms = 300) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), ms);
  };
}
```

**Step 2: Wrap mutation handlers**

For TaskList buttons, wrap the onClick handlers:
```javascript
onClick: debounce(async (e) => { e.stopPropagation(); await onTaskAction(task.id || i, "done"); })
```

Do the same for "Block", "Unblock", and all "+ Add" buttons (SectionBlock, DecisionTable, Discoveries).

**Step 3: Commit**

```bash
git add dashboard/dist/index.js
git commit -m "fix: add debounce to mutation buttons to prevent API spam"
```

---

## Phase 2: UX FOUNDATION

### Task 3: Add loading states to action buttons

**Objective:** Show spinner/disabled state on mutation buttons while API call is in flight.

**Files:**
- Modify: `dashboard/dist/index.js:134-137` (TaskList)
- Modify: `dashboard/dist/index.js:104` (SectionBlock)
- Modify: `dashboard/dist/index.js:207-209`

**Step 1: Create Spinner component**

```javascript
function Spinner({ size = "sm" }) {
  const sz = size === "sm" ? "h-3 w-3" : "h-4 w-4";
  return h("span", { className: `inline-block ${sz} animate-spin rounded-full border-2 border-current border-t-transparent` });
}
```

**Step 2: Add loading state to TaskList buttons**

Give TaskList a local `loadingAction` state:
```javascript
const [loadingAction, setLoadingAction] = useState(null);

// In each button onClick:
onClick: async (e) => {
  e.stopPropagation();
  setLoadingAction(`${i}-done`);
  try { await onTaskAction(task.id || i, "done"); } finally { setLoadingAction(null); }
},
disabled: loadingAction !== null,
// Show spinner when loading:
loadingAction === `${i}-done` ? h(Spinner) : "Done"
```

**Step 3: Add loading state to Add buttons**

Same pattern — local `adding` state, show spinner during API call, disable button.

**Step 4: Commit**

```bash
git add dashboard/dist/index.js
git commit -m "feat: add loading spinners to mutation buttons"
```

---

### Task 4: Replace prompt() with inline modal forms

**Objective:** Replace browser `prompt()` with styled modal dialogs for task add, decision add, discovery add.

**Files:**
- Modify: `dashboard/dist/index.js:104` (SectionBlock onAdd)
- Modify: `dashboard/dist/index.js:207` (DecisionTable onAdd)
- Modify: `dashboard/dist/index.js:209` (Discoveries onAdd)

**Step 1: Create Modal component**

```javascript
function Modal({ title, children, onClose }) {
  return h("div", { className: "fixed inset-0 z-50 flex items-center justify-center bg-black/50", onClick: onClose },
    h("div", { className: "max-w-md rounded-lg border border-border bg-background p-4 shadow-xl", onClick: (e) => e.stopPropagation() },
      h("div", { className: "flex items-center justify-between mb-3" },
        h("h3", { className: "text-sm font-semibold" }, title),
        h("button", { className: "text-muted-foreground hover:text-foreground", onClick: onClose }, "×")),
      children));
}
```

**Step 2: Create AddTaskModal**

```javascript
function AddTaskModal({ onAdd, onClose }) {
  const [title, setTitle] = useState("");
  const [phase, setPhase] = useState("BUILD");
  const [saving, setSaving] = useState(false);
  return h(Modal, { title: "Add Task", onClose },
    h("div", { className: "flex flex-col gap-3" },
      h("input", { className: "rounded border border-border bg-background px-2 py-1 text-sm", placeholder: "Task title...", value: title, onChange: (e) => setTitle(e.target.value), autoFocus: true }),
      h("select", { className: "rounded border border-border bg-background px-2 py-1 text-sm", value: phase, onChange: (e) => setPhase(e.target.value) },
        ["DEFINE","DESIGN","BUILD","VERIFY","SHIP"].map((p) => h("option", { key: p, value: p }, p))),
      h("div", { className: "flex justify-end gap-2" },
        h("button", { className: "text-xs rounded border border-border px-2 py-1 hover:bg-accent", onClick: onClose }, "Cancel"),
        h("button", { className: "text-xs rounded bg-primary text-primary-foreground px-2 py-1 hover:bg-primary/90", disabled: !title.trim() || saving, onClick: async () => { setSaving(true); try { await onAdd(title, phase); onClose(); } finally { setSaving(false); } } }, saving ? "Adding..." : "Add"))));
}
```

**Step 3: Wire into SectionBlock onAdd**

Replace `prompt("Task title:")` with modal state:
```javascript
const [showAddModal, setShowAddModal] = useState(false);
// onAdd prop: onClick: () => setShowAddModal(true)
// Render: showAddModal ? h(AddTaskModal, { onAdd: ..., onClose: () => setShowAddModal(false) }) : null
```

**Step 4: Do the same for DecideModal and DiscoverModal**

Create `AddDecisionModal` (decision text + rationale fields) and `AddDiscoveryModal` (text field).

**Step 5: Commit**

```bash
git add dashboard/dist/index.js
git commit -m "feat: replace prompt() dialogs with styled modal forms"
```

---

### Task 5: Enhance error boundary with diagnostics

**Objective:** Add stack trace toggle, copy-to-clipboard, and "Report in Hermes" button to the error boundary.

**Files:**
- Modify: `dashboard/dist/index.js:286-299`

**Step 1: Rewrite ErrorBoundary render**

```javascript
render() {
  if (this.state.error) {
    const msg = String(this.state.error?.message || this.state.error);
    const stack = this.state.error?.stack || "";
    const [showStack, setShowStack] = React.useState ? null : false;
    const [copied, setCopied] = React.useState ? null : false;
    return h(Card, { className: "border-destructive/50" },
      h(CardContent, { className: "p-6 text-sm" },
        h("div", { className: "mb-1 font-semibold text-destructive" }, "Projects tab crashed"),
        h("div", { className: "mb-3 text-xs text-muted-foreground max-h-20 overflow-auto" }, msg),
        h("div", { className: "flex gap-2" },
          h(Button, { onClick: () => this.setState({ error: null }) }, "Retry"),
          h("button", { className: "text-xs rounded border border-border px-2 py-1 hover:bg-accent",
            onClick: () => { navigator.clipboard.writeText(msg + "\n\n" + stack); } }, "Copy error"),
          h("button", { className: "text-xs rounded border border-border px-2 py-1 hover:bg-accent",
            onClick: () => { window.open("https://hermes-agent.nousresearch.com/docs", "_blank"); } }, "Hermes docs"))));
  }
  return this.props.children;
}
```

**Step 2: Commit**

```bash
git add dashboard/dist/index.js
git commit -m "feat: add stack toggle, copy, and Hermes docs link to error boundary"
```

---

### Task 6: Add backend healthcheck-aware error messaging

**Objective:** When the backend is unreachable, show a specific "Dashboard restart needed" message instead of a generic error.

**Files:**
- Modify: `dashboard/dist/index.js:337-338`

**Step 1: Detect healthcheck failure**

In `loadProjects`, check if the health endpoint failed specifically:
```javascript
async function loadProjects() {
  setLoading(true);
  setError(null);
  try {
    const healthData = await fetchJSON(`${API}/health`);
    // ...
  } catch (err) {
    const msg = err.message || String(err);
    if (msg.includes("Failed to fetch") || msg.includes("NetworkError") || msg.includes("ENOTFOUND")) {
      setError("Cannot reach ProjectsMD backend. Restart the Hermes dashboard with: hermes dashboard --no-open");
    } else {
      setError(`${msg}. Restart hermes dashboard if you just installed or updated the plugin.`);
    }
  }
  // ...
}
```

**Step 2: Commit**

```bash
git add dashboard/dist/index.js
git commit -m "fix: show specific restart message when backend is unreachable"
```

---

### Task 7: Add Toasts for mutation feedback (remove alert/location.reload)

**Objective:** Replace `alert()` and `window.location.reload()` with SDK Toast notifications and local state updates. This is the biggest UX win — no more full-page reloads.

**Files:**
- Modify: `dashboard/dist/index.js` (multiple locations)

**Step 1: Add toast state and component**

At the top of `ProjectsPageInner`:
```javascript
const [toasts, setToasts] = useState([]);
function addToast(message, variant = "default") {
  const id = Date.now();
  setToasts((prev) => [...prev, { id, message, variant }]);
  setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 3000);
}
```

Toast component:
```javascript
function ToastContainer({ toasts }) {
  if (!toasts.length) return null;
  return h("div", { className: "fixed bottom-4 right-4 z-50 flex flex-col gap-2" },
    toasts.map((t) => h("div", { key: t.id, className: cn("rounded-lg border px-3 py-2 text-sm shadow-lg", t.variant === "destructive" ? "border-destructive/50 bg-destructive/10 text-destructive" : "border-border bg-background") }, t.message)));
}
```

**Step 2: Replace all alert() calls**

- `alert(\`Run ${res.run_id} started\`)` → `addToast(\`Run started: ${res.run_id}\`)`
- `alert(res.error || "Launch failed")` → `addToast(res.error || "Launch failed", "destructive")`
- Queue for approval alert → `addToast("Queued for approval")`
- Queue failed alert → `addToast(res.error || "Queue failed", "destructive")`

**Step 3: Replace location.reload() with local state updates**

After a mutation (task done/block/unblock, add task/decision/discovery), instead of reloading:
```javascript
// After mutation:
addToast("Task marked done");
loadDetail();  // refresh just the detail panel
// No page reload — sidebar stays in place
```

**Step 4: Render ToastContainer**

Add `h(ToastContainer, { toasts })` at the end of `ProjectsPageInner` return.

**Step 5: Commit**

```bash
git add dashboard/dist/index.js
git commit -m "feat: replace alert() and location.reload() with toast notifications and local state updates"
```

---

## Phase 3: HERMES BRANDING

### Task 8: Add Hermes brand header with logo

**Objective:** Show "Hermes Projects" with a Hermes icon in the header.

**Files:**
- Modify: `dashboard/dist/index.js:370-372`

**Step 1: Update header**

Replace:
```javascript
h("h1", { className: "text-2xl font-semibold tracking-tight" }, "Projects"),
```

With:
```javascript
h("div", { className: "flex items-center gap-2" },
  h("span", { className: "text-xl" }, "⚡"),  // Hermes lightning bolt
  h("h1", { className: "text-2xl font-semibold tracking-tight" }, "Hermes Projects")),
```

**Step 2: Add tagline**

```javascript
h("p", { className: "text-sm text-muted-foreground" },
  "Agentic project management — browse, mutate, and orchestrate project.md files."),
```

**Step 3: Commit**

```bash
git add dashboard/dist/index.js
git commit -m "feat: add Hermes brand header with logo and tagline"
```

---

### Task 9: Add Hermes docs/settings link

**Objective:** Add a "Hermes Docs" link in the header or sidebar.

**Files:**
- Modify: `dashboard/dist/index.js:374-376`

**Step 1: Add docs link next to Rescan button**

```javascript
h("a", {
  href: "https://hermes-agent.nousresearch.com/docs",
  target: "_blank",
  className: "text-xs text-muted-foreground hover:text-foreground underline",
}, "Hermes Docs"),
```

**Step 2: Commit**

```bash
git add dashboard/dist/index.js
git commit -m "feat: add Hermes docs link to dashboard header"
```

---

### Task 10: Adopt SDK theme tokens for all colors

**Objective:** Replace hardcoded Tailwind classes with theme-safe alternatives that respect Hermes dark/light mode.

**Files:**
- Modify: `dashboard/dist/index.js` (global class changes)
- Modify: `dashboard/dist/style.css`

**Step 1: Audit hardcoded colors**

The current code already mostly uses semantic classes (`primary`, `muted`, `border`, `destructive`, `accent`) which are theme-safe. The only exceptions are:
- `bg-black/50` in modal/onboarding overlays — change to `bg-background/80`
- Explicit color names like `indigo`, `amber`, etc. — only needed for phase badges (Task 14 handles this)

**Step 2: Fix overlay backgrounds**

In `OnboardingWalkthrough:428` and `Modal`:
```javascript
// Before:
className: "fixed inset-0 z-50 flex items-center justify-center bg-black/50"
// After:
className: "fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm"
```

**Step 3: Commit**

```bash
git add dashboard/dist/index.js
git commit -m "style: use theme-safe background colors instead of hardcoded black/50"
```

---

## Phase 4: VISUAL INDICATORS

### Task 11: Add phase-specific badge colors

**Objective:** Show 5 distinct badge colors for DEFINE/DESIGN/BUILD/VERIFY/SHIP phases.

**Files:**
- Modify: `dashboard/dist/index.js:32-37` (statusVariant function)
- Modify: `dashboard/dist/style.css` (add phase color classes)

**Step 1: Add phase color mapping**

Replace `statusVariant`:
```javascript
function phaseVariant(phase) {
  const map = {
    define:  { bg: "bg-indigo-500/10", text: "text-indigo-400", border: "border-indigo-500/30" },
    design:  { bg: "bg-amber-500/10",  text: "text-amber-400",  border: "border-amber-500/30" },
    build:   { bg: "bg-emerald-500/10", text: "text-emerald-400", border: "border-emerald-500/30" },
    verify:  { bg: "bg-sky-500/10",    text: "text-sky-400",    border: "border-sky-500/30" },
    ship:    { bg: "bg-violet-500/10",  text: "text-violet-400",  border: "border-violet-500/30" },
    archived:{ bg: "bg-muted",          text: "text-muted-foreground", border: "border-border" },
  };
  const v = map[(phase || "").toLowerCase()] || { bg: "bg-muted/50", text: "text-muted-foreground", border: "border-border" };
  return cn(v.bg, v.text, v.border, "rounded-full px-2 py-0.5 text-xs font-medium border");
}
```

**Step 2: Replace Badge usage with phase colors**

Find all `h(Badge, { variant: statusVariant(project.phase) ...` and replace with:
```javascript
h("span", { className: phaseVariant(project.phase) }, project.phase || "unknown")
```

In `ProjectRow:73`, `DetailHeader:174`.

**Step 3: Commit**

```bash
git add dashboard/dist/index.js
git commit -m "feat: add 5 distinct phase badge colors (indigo/amber/emerald/sky/violet)"
```

---

### Task 12: Add project completion badge

**Objective:** Show "✓ Complete" or "🚀 Shipped" badge when all tasks done or phase is SHIP.

**Files:**
- Modify: `dashboard/dist/index.js:77-78` (ProjectRow)
- Modify: `dashboard/dist/index.js:173-174` (DetailHeader)

**Step 1: Add completion indicator to ProjectRow**

After the progress bar (line 78):
```javascript
tasks.done === tasks.total && tasks.total > 0
  ? h("div", { className: "mt-2 flex items-center gap-1 text-xs text-emerald-400" },
      h("span", null, "✓"), " Complete")
  : null,
project.phase === "SHIP"
  ? h("div", { className: "mt-2 flex items-center gap-1 text-xs text-violet-400" },
      h("span", null, "🚀"), " Ready to ship")
  : null,
```

**Step 2: Add completion indicator to DetailHeader**

After the task label (line 179):
```javascript
tasks.done === tasks.total && tasks.total > 0
  ? h(Badge, { className: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" }, "✓ Complete")
  : null,
```

**Step 3: Commit**

```bash
git add dashboard/dist/index.js
git commit -m "feat: add project completion badge (✓ Complete / 🚀 Ready to ship)"
```

---

### Task 13: Add color-coded task status with icons

**Objective:** Use green checkmark for done tasks, red for blocked, amber for pending — with actual icons not just text characters.

**Files:**
- Modify: `dashboard/dist/index.js:129-137` (TaskList)

**Step 1: Add status icons**

```javascript
function TaskStatusIcon({ done, blocked }) {
  if (blocked) return h("span", { className: "text-red-400", title: "Blocked" }, "⊘");
  if (done) return h("span", { className: "text-emerald-400", title: "Done" }, "✓");
  return h("span", { className: "text-amber-400", title: "Pending" }, "○");
}
```

**Step 2: Update TaskList row**

```javascript
h("div", { key: i, className: cn(
  "flex items-start gap-2 rounded-md border px-3 py-2 text-sm",
  task.done ? "border-emerald-500/30 bg-emerald-500/5" : "border-border bg-background/40",
) },
  h(TaskStatusIcon, { done: task.done, blocked: false }),
  // ... rest of task row
```

**Step 3: Add blocked detection**

Pass blocked info from the project detail (tasks include blocked count already, but individual task blocked status needs parsing). For now, use the `done` boolean:
- Done = green border + checkmark
- Not done = default border + circle

**Step 4: Commit**

```bash
git add dashboard/dist/index.js
git commit -m "feat: add color-coded task status icons (green done, amber pending, red blocked)"
```

---

### Task 14: Build orchestrator run status panel

**Objective:** Show live run status with output lines, status badge, and kill button — replacing the alert() on launch.

**Files:**
- Modify: `dashboard/dist/index.js:240-258` (LaunchPanel)
- Add: `RunPanel` component

**Step 1: Create RunPanel component**

```javascript
function RunPanel({ detail }) {
  const [runs, setRuns] = useState([]);
  const [polling, setPolling] = useState(false);

  useEffect(() => {
    if (!detail) return;
    let timer;
    async function poll() {
      try {
        const res = await fetchJSON(`${API_BASE}/projects/${detail.id}/runs`);
        if (res.runs) setRuns(res.runs.slice(0, 5));
      } catch (_) {}
      timer = setTimeout(poll, 3000);
    }
    poll();
    return () => clearTimeout(timer);
  }, [detail?.id]);

  if (!runs.length) return h(Card, null,
    h(CardHeader, { className: "pb-2" }, h(CardTitle, { className: "text-sm" }, "Orchestrator Runs")),
    h(CardContent, { className: "pt-0 text-sm text-muted-foreground" }, "No runs yet. Launch one below."));

  return h(Card, null,
    h(CardHeader, { className: "pb-2" }, h(CardTitle, { className: "text-sm" }, "Orchestrator Runs")),
    h(CardContent, { className: "pt-0 flex flex-col gap-2" },
      runs.map((r) => h("div", { key: r.id, className: "rounded border border-border bg-background/40 p-2 text-xs" },
        h("div", { className: "flex items-center justify-between" },
          h("code", { className: "font-mono" }, r.id.slice(0, 8)),
          h("span", { className: cn("rounded-full px-1.5 py-0.5 text-[10px] font-medium",
            r.status === "running" ? "bg-emerald-500/10 text-emerald-400" :
            r.status === "completed" ? "bg-sky-500/10 text-sky-400" :
            "bg-destructive/10 text-destructive") }, r.status)),
        h("div", { className: "mt-1 truncate text-muted-foreground" }, r.prompt || "No prompt")))));
}
```

**Step 2: Add Kill button for running runs**

Add a small "Kill" button to running runs that calls `POST /runs/{id}/kill`.

**Step 3: Wire RunPanel into the sidebar**

Replace the standalone `LaunchPanel` with a section that shows both `RunPanel` (above) and the existing `LaunchPanel` (below).

**Step 4: Commit**

```bash
git add dashboard/dist/index.js
git commit -m "feat: add orchestrator run status panel with live polling and kill button"
```

---

### Task 15: Add subagent completion indicators

**Objective:** Show subagent hierarchy in the run output — when a run spawns subagents, show them as nested cards.

**Files:**
- Modify: `dashboard/dist/index.js` (RunPanel enhancement)

**Step 1: Add subagent detection**

When run output contains `subagent_started` or `subagent_completed` events (from event_protocol.py), parse them and show nested indicators:

```javascript
function parseSubagents(events) {
  const subs = [];
  for (const evt of events || []) {
    try {
      const p = JSON.parse(evt.line);
      if (p.type === "subagent") subs.push(p);
    } catch (_) {}
  }
  return subs;
}
```

**Step 2: Show subagent count in RunPanel**

```javascript
const subCount = parseSubagents(r.events || []).length;
// Show: "2 subagents" badge in the run card
subCount > 0 ? h("span", { className: "ml-auto text-[10px] text-muted-foreground" }, `${subCount} subagent${subCount > 1 ? "s" : ""}`) : null,
```

**Step 3: Commit**

```bash
git add dashboard/dist/index.js
git commit -m "feat: add subagent count indicator to orchestrator run cards"
```

---

### Task 16: Add run history / timeline view

**Objective:** Add a "Run History" expandable section that shows past completed runs chronologically.

**Files:**
- Modify: `dashboard/dist/index.js` (RunPanel)

**Step 1: Group runs by status**

```javascript
const activeRuns = runs.filter((r) => r.status === "running");
const completedRuns = runs.filter((r) => r.status !== "running");
```

**Step 2: Add expandable history section**

```javascript
completedRuns.length > 0 ? h("details", { className: "mt-1" },
  h("summary", { className: "cursor-pointer text-xs text-muted-foreground hover:text-foreground" },
    `Show ${completedRuns.length} completed run${completedRuns.length > 1 ? "s" : ""}`),
  h("div", { className: "mt-1 flex flex-col gap-1" },
    completedRuns.map((r) => h("div", { key: r.id, className: "rounded border border-border bg-muted/20 p-1.5 text-[11px] flex justify-between" },
      h("code", { className: "font-mono" }, r.id.slice(0, 8)),
      h("span", { className: "text-muted-foreground" }, r.status))))) : null,
```

**Step 3: Commit**

```bash
git add dashboard/dist/index.js
git commit -m "feat: add run history timeline with expandable completed runs"
```

---

## Phase 5: NOUS COMPLIANCE

### Task 17: Add min Hermes version to manifest

**Objective:** Declare minimum Hermes version in manifest.json.

**Files:**
- Modify: `dashboard/manifest.json`

**Step 1: Add hermes_version field**

After `"version": "0.1.0"`, add:
```json
"hermes_version": ">=1.0.0",
```

**Step 2: Add config schema**

Add a config section:
```json
"config": {
  "project_roots": {
    "type": "array",
    "items": { "type": "string" },
    "default": ["~/projects"],
    "description": "Directories to scan for project.md files"
  }
}
```

**Step 3: Commit**

```bash
git add dashboard/manifest.json
git commit -m "feat: add hermes_version and config schema to manifest.json"
```

---

### Task 18: Use SDK-provided API prefix

**Objective:** Replace hardcoded `/api/plugins/projectsmd` with SDK-provided mount prefix.

**Files:**
- Modify: `dashboard/dist/index.js:20`

**Step 1: Detect SDK prefix**

The SDK may provide the mount prefix. If available, use it:
```javascript
const API = SDK.pluginAPI || "/api/plugins/projectsmd";
const API_BASE = API; // backwards compat
```

**Step 2: Commit**

```bash
git add dashboard/dist/index.js
git commit -m "fix: use SDK.pluginAPI for API prefix instead of hardcoded path"
```

---

### Task 19: Add plugin configuration schema to SDK registration

**Objective:** Declare plugin metadata including priority, min_version, and description in `__HERMES_PLUGINS__.register()`.

**Files:**
- Modify: `dashboard/dist/index.js:442`

**Step 1: Add metadata to register call**

```javascript
window.__HERMES_PLUGINS__.register("projectsmd", ProjectsPage, {
  priority: 50,
  min_version: "1.0.0",
  description: "ProjectsMD-powered project browsing and agent orchestration",
  category: "productivity",
});
```

**Step 2: Commit**

```bash
git add dashboard/dist/index.js
git commit -m "feat: add plugin metadata (priority, min_version, description) to SDK registration"
```

---

## Phase 6: POLISH

### Task 20: Add keyboard navigation and aria labels

**Objective:** Add aria-label attributes to all interactive elements and ensure Tab navigation works.

**Files:**
- Modify: `dashboard/dist/index.js` (all interactive elements)

**Step 1: Add aria-labels**

Key elements to label:
- Project rows: `aria-label="Project: ${project.name}"`
- Task buttons: `aria-label="Mark task done: ${task.body}"`
- Add buttons: `aria-label="Add ${section} to ${project.name}"`
- Launch button: `aria-label="Launch orchestrator run"`
- Rescan button: `aria-label="Rescan projects"`
- Close modal: `aria-label="Close"`

**Step 2: Add role attributes**

- Stat cards: `role="status"`
- Project list: `role="listbox"`
- Project row: `role="option"`
- Error message: `role="alert"`
- Toast container: `role="status" aria-live="polite"`

**Step 3: Commit**

```bash
git add dashboard/dist/index.js
git commit -m "feat: add aria-labels and roles for accessibility"
```

---

### Task 21: Add responsive breakpoints

**Objective:** Ensure the 3-column grid collapses gracefully on tablet and mobile.

**Files:**
- Modify: `dashboard/dist/index.js:386` (3-column grid)

**Step 1: Add responsive grid classes**

Current:
```javascript
className: "grid gap-4 xl:grid-cols-[22rem_minmax(0,1fr)_18rem]"
```

Updated:
```javascript
className: "grid gap-4 lg:grid-cols-1 xl:grid-cols-[22rem_minmax(0,1fr)_18rem]"
```

**Step 2: Add mobile-friendly stat card grid**

Current: `sm:grid-cols-2 xl:grid-cols-4`
Already responsive enough for stats.

**Step 3: Make sidebar collapsible on mobile**

Add a `showSidebar` toggle state for small screens in `ProjectList`:
```javascript
const [showSidebar, setShowSidebar] = useState(true);
// On mobile (< lg), show a toggle button instead of always-visible sidebar
```

**Step 4: Commit**

```bash
git add dashboard/dist/index.js
git commit -m "fix: add responsive breakpoints for tablet and mobile"
```

---

## VERIFICATION

After all 21 tasks:

```bash
# Syntax check
node --check dashboard/dist/index.js

# Lint
ruff check projectsmd_dashboard tests

# Tests
python3 -m pytest tests -q

# Full suite
bash scripts/smoke-test-dashboard-plugin.sh

# Commit everything
git status
git log --oneline -21
git push
```

---

## Task Summary

| # | Phase | Task | Severity |
|---|-------|------|----------|
| 1 | SAFETY | Fix XSS in queue list | critical |
| 2 | SAFETY | Add debounce to buttons | high |
| 3 | UX | Loading states on buttons | high |
| 4 | UX | Modal forms (replace prompt) | high |
| 5 | UX | Enhanced error boundary | medium |
| 6 | UX | Healthcheck-aware errors | medium |
| 7 | UX | Toast notifications (replace alert/reload) | critical |
| 8 | BRAND | Hermes header with logo | high |
| 9 | BRAND | Hermes docs link | low |
| 10 | BRAND | Theme-safe colors | medium |
| 11 | VISUAL | Phase badge colors | high |
| 12 | VISUAL | Completion badge | medium |
| 13 | VISUAL | Color-coded task status | medium |
| 14 | VISUAL | Orchestrator run panel | critical |
| 15 | VISUAL | Subagent indicators | medium |
| 16 | VISUAL | Run history timeline | low |
| 17 | NOUS | Manifest min version | high |
| 18 | NOUS | SDK API prefix | medium |
| 19 | NOUS | Plugin metadata | high |
| 20 | POLISH | Accessibility | medium |
| 21 | POLISH | Responsive breakpoints | medium |

**Total: 21 tasks across 6 phases. All changes in `dashboard/dist/index.js`, `dashboard/manifest.json`, and `dashboard/dist/style.css`. No backend changes.**
