(function () {
  "use strict";

  const SDK = window.__HERMES_PLUGIN_SDK__;
  if (!SDK) return;

  const { React } = SDK;
  const h = React.createElement;
  const {
    Card, CardHeader, CardTitle, CardContent,
    Badge, Button,
  } = SDK.components;
  const { useEffect, useMemo, useState } = SDK.hooks;
  const { cn } = SDK.utils;
  const fetchJSON = SDK.fetchJSON || ((url, opts) => fetch(url, opts).then((r) => {
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
    return r.json();
  }));

  function debounce(fn, ms) {
    if (ms === void 0) ms = 300;
    var timer;
    return function () {
      var self = this, args = arguments;
      clearTimeout(timer);
      timer = setTimeout(function () { fn.apply(self, args); }, ms);
    };
  }

  const API = "/api/plugins/projectsmd";

  function pct(done, total) {
    if (!total) return 0;
    return Math.round((done / total) * 100);
  }

  function taskLabel(project) {
    const tasks = project.tasks || {};
    return `${tasks.done || 0}/${tasks.total || 0} done`;
  }

  function statusVariant(value) {
    const normalized = String(value || "").toLowerCase();
    if (normalized === "blocked" || normalized === "paused") return "destructive";
    if (normalized === "ship" || normalized === "archived") return "secondary";
    return "outline";
  }

  function shortPath(path) {
    return String(path || "").replace(/^\/home\/[^/]+/, "~");
  }

  function EmptyState(props) {
    return h("div", { className: "rounded-lg border border-dashed border-border p-6 text-sm text-muted-foreground" },
      h("div", { className: "mb-2 font-medium text-foreground" }, props.title),
      h("div", null, props.children));
  }

  function StatCard({ label, value, detail }) {
    return h(Card, null,
      h(CardContent, { className: "p-4" },
        h("div", { className: "text-xs uppercase tracking-wide text-muted-foreground" }, label),
        h("div", { className: "mt-1 text-2xl font-semibold" }, value),
        detail ? h("div", { className: "mt-1 text-xs text-muted-foreground" }, detail) : null));
  }

  function ProjectRow({ project, selected, onSelect }) {
    const tasks = project.tasks || {};
    const percent = pct(tasks.done || 0, tasks.total || 0);
    return h("button", {
      type: "button",
      onClick: () => onSelect(project.path),
      className: cn(
        "w-full rounded-lg border p-3 text-left transition-colors",
        "hover:border-primary/60 hover:bg-muted/50 cursor-pointer",
        selected ? "border-primary bg-primary/10" : "border-border bg-background/40",
      ),
    },
      h("div", { className: "flex items-start justify-between gap-3" },
        h("div", { className: "min-w-0" },
          h("div", { className: "truncate font-medium" }, project.name || project.root),
          h("div", { className: "mt-1 truncate text-xs text-muted-foreground" }, shortPath(project.root))),
        h(Badge, { variant: statusVariant(project.phase), className: "shrink-0" }, project.phase || "unknown")),
      h("div", { className: "mt-3 flex items-center justify-between text-xs text-muted-foreground" },
        h("span", null, taskLabel(project)),
        h("span", null, `${percent}%`)),
      h("div", { className: "mt-2 h-1.5 overflow-hidden rounded-full bg-muted" },
        h("div", { className: "h-full rounded-full bg-primary", style: { width: `${percent}%` } })),
      project.next_action ? h("div", { className: "mt-3 line-clamp-2 text-xs text-muted-foreground" }, project.next_action) : null);
  }

  function ProjectList({ projects, selectedPath, onSelect, loading }) {
    if (loading) {
      return h(EmptyState, { title: "Scanning for project.md files" }, "Checking configured roots...");
    }
    if (!projects.length) {
      return h(EmptyState, { title: "No projects found" },
        "Create one with `projectsmd init`, or set PROJECTSMD_ROOTS before starting the dashboard.");
    }
    return h("div", { className: "flex flex-col gap-2" },
      projects.map((project) => h(ProjectRow, {
        key: project.path,
        project,
        selected: selectedPath === project.path,
        onSelect,
      })));
  }

  function SectionBlock({ title, body, children, onAdd }) {
    if (!String(body || "").trim() && !children) return null;
    return h(Card, null,
      h(CardHeader, { className: "pb-2 flex items-center justify-between" },
        h(CardTitle, { className: "text-sm" }, title),
        onAdd ? h("button", { className: "text-xs rounded border border-border px-1.5 py-0.5 hover:bg-accent", onClick: onAdd }, "+ Add") : null),
      h(CardContent, { className: "pt-0" },
        children || h("pre", { className: "max-h-96 overflow-auto whitespace-pre-wrap rounded-md bg-muted/40 p-3 font-mono text-xs leading-relaxed text-foreground" }, body)));
  }

  function TaskList({ body, onTaskAction }) {
    if (!body) return null;
    const lines = body.split("\n");
    const tasks = [];
    let currentPhase = "";
    for (const line of lines) {
      const phaseMatch = line.match(/^### Phase:\s*(.+)$/i);
      if (phaseMatch) {
        currentPhase = phaseMatch[1].trim();
        continue;
      }
      const taskMatch = line.match(/^\s*- \[([ xX])\]\s+(.*)$/);
      if (taskMatch) {
        tasks.push({ done: taskMatch[1].toLowerCase() === "x", body: taskMatch[2], phase: currentPhase });
      }
    }
    if (!tasks.length) {
      return h("pre", { className: "max-h-96 overflow-auto whitespace-pre-wrap rounded-md bg-muted/40 p-3 font-mono text-xs leading-relaxed text-foreground" }, body);
    }
    return h("div", { className: "flex flex-col gap-1" },
      tasks.map((task, i) =>
        h("div", { key: i, className: "flex items-start gap-2 rounded-md border border-border bg-background/40 px-3 py-2 text-sm" },
          h("span", { className: task.done ? "text-primary" : "text-muted-foreground" }, task.done ? "✓" : "○"),
          h("span", { className: task.done ? "line-through text-muted-foreground" : "text-foreground" }, task.body),
          task.phase ? h("span", { className: "ml-auto text-xs text-muted-foreground" }, task.phase) : null,
          h("div", { className: "ml-auto flex gap-1" },
            h("button", { className: "text-xs rounded border border-border px-1.5 py-0.5 hover:bg-accent", onClick: async (e) => { e.stopPropagation(); await onTaskAction(task.id || i, "done"); } }, "Done"),
            h("button", { className: "text-xs rounded border border-border px-1.5 py-0.5 hover:bg-accent", onClick: async (e) => { e.stopPropagation(); await onTaskAction(task.id || i, "block"); } }, "Block"),
            h("button", { className: "text-xs rounded border border-border px-1.5 py-0.5 hover:bg-accent", onClick: async (e) => { e.stopPropagation(); await onTaskAction(task.id || i, "unblock"); } }, "Unblock")))));
  }

  function DecisionTable({ body }) {
    if (!body) return null;
    const lines = body.split("\n");
    const rows = [];
    let inTable = false;
    for (const line of lines) {
      if (line.trim().startsWith("| Decision ")) { inTable = true; continue; }
      if (line.trim().startsWith("|")) {
        const cells = line.split("|").slice(1, -1).map((c) => c.trim());
        if (cells.length >= 3 && cells[0] !== "Decision") {
          rows.push({ decision: cells[0], rationale: cells[1], outcome: cells[2] });
        }
      }
    }
    if (!rows.length) {
      return h("pre", { className: "max-h-96 overflow-auto whitespace-pre-wrap rounded-md bg-muted/40 p-3 font-mono text-xs leading-relaxed text-foreground" }, body);
    }
    return h("div", { className: "flex flex-col gap-2" },
      rows.map((row, i) =>
        h("div", { key: i, className: "rounded-md border border-border bg-background/40 p-3 text-sm" },
          h("div", { className: "font-medium" }, row.decision || "Untitled"),
          h("div", { className: "mt-1 text-xs text-muted-foreground" }, "Rationale: ", row.rationale || "—"),
          h("div", { className: "mt-1 text-xs text-muted-foreground" }, "Outcome: ", row.outcome || "—"))));
  }

  function DetailHeader({ detail }) {
    const tasks = detail.tasks || {};
    const percent = pct(tasks.done || 0, tasks.total || 0);
    return h(Card, null,
      h(CardContent, { className: "p-5" },
        h("div", { className: "flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between" },
          h("div", { className: "min-w-0" },
            h("div", { className: "flex flex-wrap items-center gap-2" },
              h("h2", { className: "truncate text-xl font-semibold" }, detail.name || "Untitled project"),
              h(Badge, { variant: statusVariant(detail.phase) }, detail.phase || "unknown"),
              detail.owner ? h(Badge, { variant: "outline" }, detail.owner) : null),
            h("div", { className: "mt-2 truncate font-mono text-xs text-muted-foreground" }, shortPath(detail.path))),
          h("div", { className: "w-full lg:w-48" },
            h("div", { className: "flex justify-between text-xs text-muted-foreground" },
              h("span", null, taskLabel(detail)),
              h("span", null, `${percent}%`)),
            h("div", { className: "mt-2 h-2 overflow-hidden rounded-full bg-muted" },
              h("div", { className: "h-full rounded-full bg-primary", style: { width: `${percent}%` } }))))));
  }

  function CurrentState({ detail }) {
    return h(Card, null,
      h(CardHeader, { className: "pb-2" }, h(CardTitle, { className: "text-sm" }, "Current State")),
      h(CardContent, { className: "grid gap-3 pt-0 text-sm" },
        h("div", null,
          h("div", { className: "text-xs uppercase tracking-wide text-muted-foreground" }, "Next action"),
          h("div", { className: "mt-1" }, detail.next_action || "Not set")),
        h("div", null,
          h("div", { className: "text-xs uppercase tracking-wide text-muted-foreground" }, "Blockers"),
          h("div", { className: "mt-1" }, detail.blockers || "None"))));
  }

  function ProjectDetail({ detail, loading }) {
    if (loading) return h(EmptyState, { title: "Loading project" }, "Reading project.md...");
    if (!detail) return h(EmptyState, { title: "Pick a project" }, "Select a project from the list to inspect its project.md state.");

    const [queueItems, setQueueItems] = useState([]);
    const [queueLoading, setQueueLoading] = useState(false);

    async function loadQueue() {
      setQueueLoading(true);
      try {
        const res = await fetchJSON(`${API}/projects/detail?path=${encodeURIComponent(detail.path)}`);
        // fetch queue for this project
        const qRes = await fetchJSON(`${API}/projects/${res.id}/queue?path=${encodeURIComponent(detail.path)}`);
        setQueueItems(qRes.pending || []);
      } catch (_) {} finally { setQueueLoading(false); }
    }

    const sections = detail.sections || {};
    return h("div", { className: "flex flex-col gap-4" },
      h(DetailHeader, { detail }),
      h(CurrentState, { detail }),
      h("div", { className: "grid gap-4 xl:grid-cols-2" },
        h(SectionBlock, { title: "What This Is", body: sections["What This Is"] }),
        h(SectionBlock, { title: "Key Decisions", body: sections["Key Decisions"], children: h(DecisionTable, { body: sections["Key Decisions"] }), onAdd: async () => { const text = prompt("Decision:"); if (!text) return; const res = await fetchJSON(`${API_BASE}/projects/${detail.id}/decisions`, { method: "POST", body: { path: detail.path, decision: text } }); if (res.ok) window.location.reload(); } })),
      h(SectionBlock, { title: "Tasks", body: sections.Tasks, children: h(TaskList, { body: sections.Tasks, onTaskAction: async (taskId, action) => { const res = await fetchJSON(`${API_BASE}/projects/${detail.id}/tasks/${taskId}/${action}`, { method: "POST", body: { path: detail.path } }); if (res.ok) window.location.reload(); } }), onAdd: async () => { const text = prompt("Task title:"); if (!text) return; const res = await fetchJSON(`${API_BASE}/projects/${detail.id}/tasks`, { method: "POST", body: { path: detail.path, title: text } }); if (res.ok) window.location.reload(); } }),
      h(SectionBlock, { title: "Discoveries", body: sections.Discoveries, onAdd: async () => { const text = prompt("Discovery:"); if (!text) return; const res = await fetchJSON(`${API_BASE}/projects/${detail.id}/discoveries`, { method: "POST", body: { path: detail.path, text } }); if (res.ok) window.location.reload(); } }),
      h("details", { className: "rounded-lg border border-border bg-background/40" },
        h("summary", { className: "cursor-pointer p-3 text-sm font-medium" }, "Raw project.md"),
        h("pre", { className: "max-h-[32rem] overflow-auto border-t border-border p-3 font-mono text-xs leading-relaxed" }, detail.raw || "")),
      h("details", { className: "rounded-lg border border-border bg-background/40" },
        h("summary", { className: "cursor-pointer p-3 text-sm font-medium" }, "Diff preview / Queue"),
        h("div", { className: "border-t border-border p-3 flex flex-col gap-3" },
          h("textarea", { className: "w-full rounded border border-border bg-muted/40 p-2 font-mono text-xs", rows: 6, placeholder: "Paste proposed project.md content...", onChange: async (e) => {
            const proposed = e.target.value;
            if (!proposed) return;
            const res = await fetchJSON(`${API_BASE}/projects/${detail.id}/diff`, { method: "POST", body: { path: detail.path, proposed } });
            const el = document.getElementById("diff-output");
            if (el) el.textContent = res.ok ? res.diff : res.error || "Error";
          } }),
          h("pre", { id: "diff-output", className: "max-h-64 overflow-auto rounded bg-muted/40 p-2 font-mono text-xs" }, "Diff will appear here..."),
          h("div", { className: "flex gap-2" },
            h("button", { className: "text-xs rounded border border-border px-2 py-1 hover:bg-accent", onClick: async () => {
              const proposed = document.querySelector("textarea")?.value;
              if (!proposed) return;
              const res = await fetchJSON(`${API}/projects/${detail.id}/queue`, { method: "POST", body: { path: detail.path, proposed } });
              alert(res.ok ? "Queued for approval" : (res.error || "Queue failed"));
              loadQueue();
            } }, "Queue for approval"),
            h("button", { className: "text-xs rounded border border-border px-2 py-1 hover:bg-accent", onClick: loadQueue }, queueLoading ? "Loading..." : "Show pending"),
          ),
          h("div", { id: "queue-list", className: "text-xs" },
            queueItems.map(function (u) {
              return h("div", { key: u.id, className: "border-b border-border py-1 flex flex-col gap-1" },
                h("code", { className: "text-xs" }, u.id),
                h("pre", { className: "text-xs max-h-24 overflow-auto" }, u.diff),
                h("div", { className: "flex gap-1" },
                  h("button", { className: "text-xs rounded border border-border px-1.5 py-0.5 hover:bg-accent", onClick: async function () {
                    await fetchJSON(`${API}/projects/${detail.id}/queue/${u.id}/approve`, { method: "POST" });
                    loadQueue();
                  } }, "Approve"),
                  h("button", { className: "text-xs rounded border border-border px-1.5 py-0.5 hover:bg-accent", onClick: async function () {
                    await fetchJSON(`${API}/projects/${detail.id}/queue/${u.id}/reject`, { method: "POST" });
                    loadQueue();
                  } }, "Reject")))
            })))));
  }

  function LaunchPanel({ detail, onLaunch }) {
    const [task, setTask] = useState("");
    const [role, setRole] = useState("");
    const [roles, setRoles] = useState([]);
    useEffect(() => {
      fetchJSON(`${API_BASE}/roster`).then((res) => { if (res.ok && res.roster) setRoles(res.roster); });
    }, []);
    if (!detail) return h(Card, null,
      h(CardHeader, { className: "pb-2" }, h(CardTitle, { className: "text-sm" }, "Orchestrator")),
      h(CardContent, { className: "pt-0 text-sm" }, h("p", { className: "text-muted-foreground" }, "Select a project to launch an agent run.")));
    return h(Card, null,
      h(CardHeader, { className: "pb-2" }, h(CardTitle, { className: "text-sm" }, "Orchestrator")),
      h(CardContent, { className: "pt-0 text-sm flex flex-col gap-2" },
        h("input", { className: "rounded border border-border bg-background px-2 py-1 text-xs", placeholder: "Task description...", value: task, onChange: (e) => setTask(e.target.value) }),
        h("select", { className: "rounded border border-border bg-background px-2 py-1 text-xs", value: role, onChange: (e) => setRole(e.target.value) },
          h("option", { value: "" }, "Default role"),
          roles.map((r) => h("option", { key: r.id, value: r.id }, r.name))),
        h(Button, { className: "w-full", onClick: () => onLaunch(task, role) }, "Launch run")));
  }

  function RootManager({ roots, onChange }) {
    const [input, setInput] = useState("");
    return h("div", { className: "flex flex-col gap-2" },
      h("div", { className: "flex flex-col gap-2" },
        roots.map((root) =>
          h("div", { key: root, className: "flex items-center justify-between gap-2" },
            h("code", { className: "rounded bg-muted/50 px-2 py-1 font-mono text-xs text-muted-foreground" }, shortPath(root)),
            h(Button, {
              variant: "ghost",
              className: "h-6 px-2 text-xs",
              onClick: () => onChange(roots.filter((r) => r !== root)),
            }, "Remove")))),
      h("div", { className: "flex gap-2" },
        h("input", {
          value: input,
          onChange: (e) => setInput(e.target.value),
          placeholder: "Add root path",
          className: "flex-1 rounded border border-border bg-background px-2 py-1 text-xs",
          onKeyDown: (e) => { if (e.key === "Enter") { e.preventDefault(); onChange([...roots, input]); setInput(""); } },
        }),
        h(Button, {
          className: "h-7 px-2 text-xs",
          onClick: () => { onChange([...roots, input]); setInput(""); },
        }, "Add")));
  }

  class ErrorBoundary extends React.Component {
    constructor(props) { super(props); this.state = { error: null }; }
    static getDerivedStateFromError(error) { return { error }; }
    componentDidCatch(error, info) { console.error("Projects plugin crashed:", error, info); }
    render() {
      if (this.state.error) {
        return h(Card, null,
          h(CardContent, { className: "p-6 text-sm" },
            h("div", { className: "mb-1 font-semibold text-destructive" }, "Projects tab crashed"),
            h("div", { className: "mb-3 text-xs text-muted-foreground" }, String(this.state.error && this.state.error.message || this.state.error)),
            h(Button, { onClick: () => this.setState({ error: null }) }, "Retry")));
      }
      return this.props.children;
    }
  }

  function ProjectsPageInner() {
    const [health, setHealth] = useState(null);
    const [projects, setProjects] = useState([]);
    const [selectedPath, setSelectedPath] = useState(null);
    const [detail, setDetail] = useState(null);
    const [loading, setLoading] = useState(true);
    const [detailLoading, setDetailLoading] = useState(false);
    const [error, setError] = useState(null);

    const selectedProject = useMemo(
      () => projects.find((project) => project.path === selectedPath),
      [projects, selectedPath],
    );
    const totals = useMemo(() => projects.reduce((acc, project) => {
      const tasks = project.tasks || {};
      acc.done += tasks.done || 0;
      acc.pending += tasks.pending || 0;
      acc.blocked += tasks.blocked || 0;
      acc.total += tasks.total || 0;
      return acc;
    }, { done: 0, pending: 0, blocked: 0, total: 0 }), [projects]);

    async function loadProjects() {
      setLoading(true);
      setError(null);
      try {
        const healthData = await fetchJSON(`${API}/health`);
        const projectData = await fetchJSON(`${API}/projects`);
        const nextProjects = projectData.projects || [];
        setHealth(healthData);
        setProjects(nextProjects);
        setSelectedPath((current) => {
          if (current && nextProjects.some((project) => project.path === current)) return current;
          return nextProjects.length ? nextProjects[0].path : null;
        });
      } catch (err) {
        setError(`${err.message || err}. Restart hermes dashboard if you just installed or updated the plugin.`);
      } finally {
        setLoading(false);
      }
    }

    useEffect(() => { loadProjects(); }, []);

    useEffect(() => {
      if (!selectedPath) { setDetail(null); return; }
      setDetailLoading(true);
      setError(null);
      fetchJSON(`${API}/projects/detail?path=${encodeURIComponent(selectedPath)}`)
        .then(setDetail)
        .catch((err) => setError(err.message || String(err)))
        .finally(() => setDetailLoading(false));
    }, [selectedPath]);

    // Keyboard shortcuts
    useEffect(() => {
      function onKey(e) {
        if (e.key === "r" && e.ctrlKey) { e.preventDefault(); loadProjects(); }
        if (e.key === "n" && e.ctrlKey) { e.preventDefault(); const root = prompt("Project root path:"); if (root) { setSelectedPath(root); } }
        if (e.key === "Escape") { setSelectedPath(null); }
      }
      document.addEventListener("keydown", onKey);
      return () => document.removeEventListener("keydown", onKey);
    }, []);

    return h("div", { className: "flex flex-col gap-4 p-4" },
      h("div", { className: "flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between" },
        h("div", null,
          h("h1", { className: "text-2xl font-semibold tracking-tight" }, "Projects"),
          h("p", { className: "text-sm text-muted-foreground" },
            "Browse ProjectsMD project.md files and see the current resume point.")),
        h("div", { className: "flex items-center gap-2" },
          health && health.projectsmd ? h(Badge, { variant: health.projectsmd.available ? "outline" : "destructive" },
            health.projectsmd.available ? "projectsmd available" : "projectsmd missing") : null,
          h(Button, { onClick: loadProjects, disabled: loading }, loading ? "Scanning..." : "Rescan"))),

      error ? h("div", { className: "rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive" }, error) : null,

      h("div", { className: "grid gap-3 sm:grid-cols-2 xl:grid-cols-4" },
        h(StatCard, { label: "Projects", value: projects.length, detail: health && health.roots ? `${health.roots.length} roots scanned` : "" }),
        h(StatCard, { label: "Tasks", value: totals.total, detail: `${totals.done} done, ${totals.pending} pending` }),
        h(StatCard, { label: "Blocked", value: totals.blocked, detail: totals.blocked ? "Needs attention" : "No blockers found" }),
        h(StatCard, { label: "Selected", value: selectedProject ? selectedProject.phase || "unknown" : "—", detail: selectedProject ? shortPath(selectedProject.root) : "No project selected" })),

      h("div", { className: "grid gap-4 xl:grid-cols-[22rem_minmax(0,1fr)_18rem]" },
        h(Card, { className: "xl:sticky xl:top-4 xl:max-h-[calc(100vh-8rem)] xl:overflow-auto" },
          h(CardHeader, { className: "pb-2" }, h(CardTitle, { className: "text-base" }, "Project files")),
          h(CardContent, { className: "pt-0" }, h(ProjectList, { projects, selectedPath, onSelect: setSelectedPath, loading }))),
        h("div", { className: "min-w-0" }, h(ProjectDetail, { detail, loading: detailLoading })),
        h("div", { className: "flex flex-col gap-4" },
          h(LaunchPanel, { detail, onLaunch: async (task, role) => {
            if (!detail) return;
            const res = await fetchJSON(`${API_BASE}/projects/${detail.id}/runs`, { method: "POST", body: { path: detail.path, task, role_id: role } });
            if (res.ok) { alert(`Run ${res.run_id} started`); } else { alert(res.error || "Launch failed"); }
          } }),
          h(Card, null,
            h(CardHeader, { className: "pb-2" }, h(CardTitle, { className: "text-sm" }, "Roots")),
            h(CardContent, { className: "pt-0" },
              h(RootManager, {
                roots: (health && health.roots) || [],
                onChange: async (nextRoots) => {
                  try {
                    await fetchJSON(`${API}/config`, {
                      method: "PUT",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ project_roots: nextRoots }),
                    });
                    loadProjects();
                  } catch (err) {
                    setError(err.message || String(err));
                  }
                },
              }))))));
  }

  function OnboardingWalkthrough() {
    const [step, setStep] = useState(0);
    const steps = [
      { title: "Welcome", body: "This is the ProjectsMD dashboard. Browse your project.md files and manage projects." },
      { title: "Projects", body: "Select a project from the left sidebar to see its details." },
      { title: "Mutations", body: "Use the + Add buttons to add tasks, decisions, and discoveries. Click task buttons to mark done, block, or unblock." },
      { title: "Orchestrator", body: "Enter a task and pick a role, then click Launch run to start an agent." },
      { title: "Diff / Queue", body: "Paste proposed project.md content in the Diff preview area to see changes. Queue for approval to stage mutations." },
      { title: "Keyboard shortcuts", body: "Ctrl+R = rescan, Ctrl+N = select project by path, Escape = clear selection." },
    ];
    if (step >= steps.length) return null;
    return h("div", { className: "fixed inset-0 z-50 flex items-center justify-center bg-black/50" },
      h("div", { className: "max-w-sm rounded-lg border border-border bg-background p-4 shadow-lg" },
        h("h3", { className: "text-sm font-semibold" }, steps[step].title),
        h("p", { className: "mt-1 text-xs text-muted-foreground" }, steps[step].body),
        h("div", { className: "mt-3 flex justify-end gap-2" },
          h("button", { className: "text-xs rounded border border-border px-2 py-1 hover:bg-accent", onClick: () => setStep(step + 1) }, step < steps.length - 1 ? "Next" : "Done"),
          step > 0 ? h("button", { className: "text-xs rounded border border-border px-2 py-1 hover:bg-accent", onClick: () => setStep(step - 1) }, "Back") : null,
          h("button", { className: "text-xs rounded border border-border px-2 py-1 hover:bg-accent", onClick: () => setStep(steps.length) }, "Skip"))));
  }

  function ProjectsPage() {
    return h(ErrorBoundary, null, h(ProjectsPageInner), h(OnboardingWalkthrough));
  }

  window.__HERMES_PLUGINS__.register("projectsmd", ProjectsPage);
})();
