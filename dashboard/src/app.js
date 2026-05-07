(function () {
  "use strict";

  const SDK = window.__HERMES_PLUGIN_SDK__;
  if (!SDK) return;

  const { React } = SDK;
  const h = React.createElement;
  const { Card, CardHeader, CardTitle, CardContent, Badge, Button } = SDK.components;
  const { useEffect, useMemo, useState } = SDK.hooks;
  const { cn } = SDK.utils;
  const fetchJSON = SDK.fetchJSON || ((url, opts) => fetch(url, opts).then((r) => {
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
    return r.json();
  }));

  const API = SDK.pluginAPI || "/api/plugins/projectsmd";
  const PAGE = "mx-auto flex w-full max-w-[1600px] flex-col gap-5 p-4 sm:p-5 lg:p-6";
  const SECTION_GRID = "grid gap-4 lg:grid-cols-1 xl:grid-cols-[23rem_minmax(0,1fr)_19rem]";
  const CARD_HEADER = "px-4 pb-2 pt-4";
  const CARD_CONTENT = "px-4 pb-4 pt-2";
  const CARD_CONTENT_STACK = CARD_CONTENT + " flex flex-col gap-3";
  const CONTROL_ROW = "flex flex-wrap items-center gap-2";
  const BUTTON_SM = "h-8 px-3 py-1.5 text-xs";
  const INPUT_BASE = "h-9 rounded-md border border-border bg-background px-3 text-sm outline-none transition focus:border-primary/60";
  const INPUT_SM = "h-8 rounded-md border border-border bg-background px-3 text-xs outline-none transition focus:border-primary/60";
  const TEXTAREA_BASE = "min-h-28 rounded-md border border-border bg-background px-3 py-2 text-sm outline-none transition focus:border-primary/60";
  const MONO_BLOCK = "max-h-72 overflow-auto rounded-lg border border-border bg-muted/30 p-3 font-mono text-xs leading-relaxed text-foreground";
  const MODAL_OVERLAY = "fixed inset-0 z-50 flex items-center justify-center bg-background/80 p-4";
  const MODAL_PANEL = "w-full max-w-lg rounded-xl border border-border bg-background p-5 shadow-xl";

  function pct(done, total) { return total ? Math.round((done / total) * 100) : 0; }
  function shortPath(path) { return String(path || "").replace(/^\/home\/[^/]+/, "~"); }
  function taskLabel(project) { const t = project.tasks || {}; return `${t.done || 0}/${t.total || 0} done`; }
  function phaseClass(phase) {
    const map = {
      define: "border-indigo-500/30 bg-indigo-500/10 text-indigo-400",
      design: "border-amber-500/30 bg-amber-500/10 text-amber-400",
      build: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
      verify: "border-sky-500/30 bg-sky-500/10 text-sky-400",
      ship: "border-violet-500/30 bg-violet-500/10 text-violet-400",
      paused: "border-muted bg-muted/40 text-muted-foreground",
    };
    return cn("rounded-full border px-2 py-0.5 text-xs font-medium", map[String(phase || "").toLowerCase()] || "border-border bg-muted/40 text-muted-foreground");
  }
  function statusClass(status) {
    const s = String(status || "").toLowerCase();
    if (s === "running") return "border-emerald-500/30 bg-emerald-500/10 text-emerald-400";
    if (s === "failed" || s === "killed") return "border-destructive/40 bg-destructive/10 text-destructive";
    return "border-border bg-muted/40 text-muted-foreground";
  }

  function EmptyState({ title, children }) {
    return h("div", { className: "rounded-xl border border-dashed border-border bg-muted/10 p-6 text-sm text-muted-foreground" },
      h("div", { className: "mb-1 font-medium text-foreground" }, title),
      h("div", null, children));
  }

  function StatCard({ label, value, detail, help }) {
    return h(Card, { className: "rounded-xl" },
      h(CardContent, { className: "p-4" },
        h("div", { className: "text-[11px] uppercase tracking-[0.18em] text-muted-foreground" }, label),
        h("div", { className: "mt-1 text-2xl font-semibold tracking-tight" }, value),
        detail ? h("div", { className: "mt-1 text-xs text-muted-foreground" }, detail) : null,
        help ? h("div", { className: "mt-2 border-t border-border/60 pt-2 text-[11px] leading-relaxed text-muted-foreground" }, help) : null));
  }

  function ToastContainer({ toasts }) {
    if (!toasts.length) return null;
    return h("div", { className: "fixed bottom-4 right-4 z-50 flex max-w-sm flex-col gap-2" },
      toasts.map((t) => h("div", { key: t.id, role: "status", className: cn("rounded-lg border px-3 py-2 text-sm shadow-lg", t.variant === "destructive" ? "border-destructive/50 bg-destructive/10 text-destructive" : "border-border bg-background") }, t.message)));
  }

  function FormModal({ title, description, fields, initial, onCancel, onSubmit, submitLabel }) {
    const [data, setData] = useState(initial || {});
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    useEffect(() => {
      function onKey(e) { if (e.key === "Escape") onCancel(); }
      document.addEventListener("keydown", onKey);
      return () => document.removeEventListener("keydown", onKey);
    }, []);
    async function save() {
      const missing = fields.filter((f) => f.required && !String(data[f.key] || "").trim()).map((f) => f.label);
      if (missing.length) { setError("Missing required fields: " + missing.join(", ")); return; }
      setSaving(true); setError("");
      try { await onSubmit(data); } finally { setSaving(false); }
    }
    return h("div", { className: MODAL_OVERLAY, role: "dialog", "aria-label": title, onClick: onCancel },
      h("div", { className: MODAL_PANEL, onClick: (e) => e.stopPropagation() },
        h("div", { className: "mb-4 flex items-start justify-between gap-4" },
          h("div", null,
            h("h3", { className: "text-base font-semibold tracking-tight" }, title),
            description ? h("p", { className: "mt-1 text-sm text-muted-foreground" }, description) : null),
          h("button", { className: "rounded-md border border-border px-2 py-1 text-xs hover:bg-accent", onClick: onCancel, "aria-label": "Close" }, "Close")),
        h("div", { className: "flex flex-col gap-3" },
          fields.map((f) => h("label", { key: f.key, className: "flex flex-col gap-1.5" },
            h("span", { className: "text-xs font-medium text-muted-foreground" }, f.label, f.required ? " *" : ""),
            f.type === "textarea"
              ? h("textarea", { className: TEXTAREA_BASE, value: data[f.key] || "", placeholder: f.placeholder || "", onChange: (e) => setData({ ...data, [f.key]: e.target.value }) })
              : f.type === "select"
                ? h("select", { className: INPUT_BASE, value: data[f.key] || "", onChange: (e) => setData({ ...data, [f.key]: e.target.value }) }, (f.options || []).map((o) => h("option", { key: o.value || o, value: o.value || o }, o.label || o)))
                : h("input", { className: INPUT_BASE, value: data[f.key] || "", placeholder: f.placeholder || "", onChange: (e) => setData({ ...data, [f.key]: e.target.value }), autoFocus: f.autoFocus })))),
        error ? h("div", { className: "mt-3 rounded-md border border-destructive/40 bg-destructive/10 p-2 text-xs text-destructive" }, error) : null,
        h("div", { className: "mt-4 flex justify-end gap-2" },
          h(Button, { variant: "ghost", className: BUTTON_SM, onClick: onCancel }, "Cancel"),
          h(Button, { className: BUTTON_SM, disabled: saving, onClick: save }, saving ? "Saving..." : (submitLabel || "Save")))));
  }

  function ProjectRow({ project, selected, onSelect }) {
    const tasks = project.tasks || {};
    const percent = pct(tasks.done || 0, tasks.total || 0);
    return h("button", { type: "button", onClick: () => onSelect(project.path), "aria-label": "Project: " + (project.name || project.root), className: cn("w-full rounded-xl border p-3 text-left transition", selected ? "border-primary bg-primary/10 shadow-sm" : "border-border bg-background/40 hover:border-primary/50 hover:bg-muted/40") },
      h("div", { className: "flex items-start justify-between gap-3" },
        h("div", { className: "min-w-0" },
          h("div", { className: "truncate text-sm font-medium" }, project.name || project.root),
          h("div", { className: "mt-1 truncate text-xs text-muted-foreground" }, shortPath(project.root))),
        h("span", { className: phaseClass(project.phase) }, project.phase || "unknown")),
      h("div", { className: "mt-3 flex items-center justify-between text-xs text-muted-foreground" }, h("span", null, taskLabel(project)), h("span", null, `${percent}%`)),
      h("div", { className: "mt-2 h-1.5 overflow-hidden rounded-full bg-muted" }, h("div", { className: "h-full rounded-full bg-primary transition-all", style: { width: `${percent}%` } })),
      project.next_action ? h("div", { className: "mt-3 line-clamp-2 text-xs text-muted-foreground" }, project.next_action) : null,
      tasks.done === tasks.total && tasks.total > 0 ? h("div", { className: "mt-2 text-xs text-emerald-400" }, "✓ Complete") : null);
  }

  function ProjectList({ projects, selectedPath, onSelect, loading }) {
    if (loading) return h(EmptyState, { title: "Scanning for project.md files" }, "Checking configured roots...");
    if (!projects.length) return h(EmptyState, { title: "No projects found" }, "Add a readable root or create a new project.");
    return h("div", { className: "flex flex-col gap-2" }, projects.map((project) => h(ProjectRow, { key: project.path, project, selected: selectedPath === project.path, onSelect })));
  }

  function DetailHeader({ detail }) {
    const tasks = detail.tasks || {};
    const percent = pct(tasks.done || 0, tasks.total || 0);
    return h(Card, { className: "rounded-xl" },
      h(CardContent, { className: "p-5" },
        h("div", { className: "flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between" },
          h("div", { className: "min-w-0" },
            h("div", { className: "flex flex-wrap items-center gap-2" },
              h("h2", { className: "truncate text-xl font-semibold tracking-tight" }, detail.name || "Untitled project"),
              h("span", { className: phaseClass(detail.phase) }, detail.phase || "unknown"),
              detail.owner ? h(Badge, { variant: "outline" }, detail.owner) : null),
            h("div", { className: "mt-2 truncate font-mono text-xs text-muted-foreground" }, shortPath(detail.path)),
            detail.next_action ? h("div", { className: "mt-3 rounded-lg border border-border bg-muted/20 p-3 text-sm" }, h("span", { className: "text-muted-foreground" }, "Next: "), detail.next_action) : null),
          h("div", { className: "w-full lg:w-56" },
            h("div", { className: "flex justify-between text-xs text-muted-foreground" }, h("span", null, taskLabel(detail)), h("span", null, `${percent}%`)),
            h("div", { className: "mt-2 h-2 overflow-hidden rounded-full bg-muted" }, h("div", { className: "h-full rounded-full bg-primary transition-all", style: { width: `${percent}%` } })),
            h("div", { className: "mt-2 text-[11px] leading-relaxed text-muted-foreground" }, "Counts come from project.md checkboxes. Mark tasks done to move progress.")))));
  }

  function CurrentState({ detail }) {
    const state = detail.current_state || {};
    const rows = [
      ["Phase", state.phase || detail.phase || "unknown"], ["Last completed", state.last_completed || "Not set"], ["In progress", state.in_progress || "Not set"],
      ["Next action", state.next_action || detail.next_action || "Not set"], ["Blockers", state.blockers || detail.blockers || "None"], ["Notes", state.notes || "None"],
    ];
    return h(Card, { className: "rounded-xl" },
      h(CardHeader, { className: CARD_HEADER }, h(CardTitle, { className: "text-sm" }, "Current State")),
      h(CardContent, { className: CARD_CONTENT }, h("div", { className: "grid gap-2 sm:grid-cols-2" }, rows.map((r) => h("div", { key: r[0], className: "rounded-lg border border-border bg-muted/20 p-3" }, h("div", { className: "text-[11px] uppercase tracking-wide text-muted-foreground" }, r[0]), h("div", { className: "mt-1 text-sm" }, r[1]))))));
  }

  function SectionCard({ title, action, children, empty }) {
    return h(Card, { className: "rounded-xl" },
      h(CardHeader, { className: cn(CARD_HEADER, "flex flex-row items-center justify-between gap-3") }, h(CardTitle, { className: "text-sm" }, title), action || null),
      h(CardContent, { className: CARD_CONTENT_STACK }, children || h(EmptyState, { title: "Nothing recorded" }, empty || "Add the first item when you have one.")));
  }

  function TaskList({ tasks, onTaskAction }) {
    if (!tasks || !tasks.length) return null;
    return h("div", { className: "flex flex-col gap-2" }, tasks.map((task) => h("div", { key: task.id, className: cn("flex flex-col gap-2 rounded-lg border p-3 text-sm sm:flex-row sm:items-start", task.done ? "border-emerald-500/30 bg-emerald-500/5" : task.blocked ? "border-amber-500/30 bg-amber-500/5" : "border-border bg-background/40") },
      h("span", { className: task.done ? "text-emerald-400" : task.blocked ? "text-amber-400" : "text-muted-foreground" }, task.done ? "✓" : task.blocked ? "!" : "○"),
      h("div", { className: "min-w-0 flex-1" }, h("div", { className: task.done ? "line-through text-muted-foreground" : "text-foreground" }, task.title), task.phase ? h("div", { className: "mt-1 text-xs text-muted-foreground" }, task.phase) : null),
      h("div", { className: "flex flex-wrap gap-1 sm:justify-end" },
        task.mutable ? h("button", { className: "rounded-md border border-border px-2 py-1 text-xs hover:bg-accent disabled:opacity-50", disabled: task.done, onClick: () => onTaskAction(task, "done") }, "Done") : h("span", { className: "rounded-md border border-border px-2 py-1 text-xs text-muted-foreground" }, "read-only"),
        task.mutable ? h("button", { className: "rounded-md border border-border px-2 py-1 text-xs hover:bg-accent", onClick: () => onTaskAction(task, "block") }, "Block") : null,
        task.mutable ? h("button", { className: "rounded-md border border-border px-2 py-1 text-xs hover:bg-accent", onClick: () => onTaskAction(task, "unblock") }, "Unblock") : null))));
  }

  function DecisionList({ decisions }) {
    if (!decisions || !decisions.length) return null;
    return h("div", { className: "flex flex-col gap-2" }, decisions.map((row, i) => h("div", { key: i, className: "rounded-lg border border-border bg-background/40 p-3 text-sm" }, h("div", { className: "font-medium" }, row.decision || "Untitled decision"), h("div", { className: "mt-1 text-xs text-muted-foreground" }, "Rationale: ", row.rationale || "—"), h("div", { className: "mt-1 text-xs text-muted-foreground" }, "Outcome: ", row.outcome || "—"))));
  }

  function DiscoveryList({ discoveries }) {
    if (!discoveries || !discoveries.length) return null;
    return h("div", { className: "flex flex-col gap-2" }, discoveries.map((d, i) => h("div", { key: i, className: "rounded-lg border border-border bg-background/40 p-3 text-sm" }, d.text || d)));
  }

  function Requirements({ req }) {
    if (!req) return null;
    const groups = [["Validated", req.validated], ["Active", req.active], ["Out of Scope", req.out_of_scope]];
    return h("div", { className: "grid gap-2 sm:grid-cols-3" }, groups.map(([name, items]) => h("div", { key: name, className: "rounded-lg border border-border bg-muted/20 p-3" }, h("div", { className: "text-xs font-medium text-muted-foreground" }, name), (items || []).length ? h("ul", { className: "mt-2 list-disc space-y-1 pl-4 text-xs" }, items.map((item, i) => h("li", { key: i }, item))) : h("div", { className: "mt-2 text-xs text-muted-foreground" }, "None"))));
  }

  function QueuePanel({ detail, addToast, onRefresh }) {
    const [proposed, setProposed] = useState("");
    const [diff, setDiff] = useState("Diff will appear here...");
    const [pending, setPending] = useState([]);
    const [loading, setLoading] = useState(false);
    async function preview() {
      if (!proposed.trim()) { setDiff("Paste proposed project.md content first."); return; }
      const res = await fetchJSON(`${API}/projects/${detail.id}/diff`, { method: "POST", body: { path: detail.path, proposed } });
      setDiff(res.diff || "No diff returned.");
    }
    async function loadQueue() {
      setLoading(true);
      try { const res = await fetchJSON(`${API}/projects/${detail.id}/queue?path=${encodeURIComponent(detail.path)}`); setPending(res.pending || []); } finally { setLoading(false); }
    }
    async function queue() {
      if (!proposed.trim()) { addToast("Paste proposed project.md content first", "destructive"); return; }
      await fetchJSON(`${API}/projects/${detail.id}/queue`, { method: "POST", body: { path: detail.path, proposed, meta: { reason: "dashboard" } } });
      addToast("Queued for approval"); setProposed(""); await loadQueue();
    }
    async function decide(id, action) {
      const res = await fetchJSON(`${API}/projects/${detail.id}/queue/${id}/${action}`, { method: "POST", body: {} });
      addToast(action === "approve" ? "Approved update" : "Rejected update");
      await loadQueue(); if (res.detail && onRefresh) onRefresh();
    }
    return h(SectionCard, { title: "Diff preview / Queue" },
      h("p", { className: "text-xs leading-relaxed text-muted-foreground" }, "Stage full-file project.md proposals, review the diff, then approve with snapshot protection."),
      h("textarea", { className: TEXTAREA_BASE + " font-mono text-xs", value: proposed, placeholder: "Paste proposed project.md content...", onChange: (e) => setProposed(e.target.value) }),
      h("div", { className: CONTROL_ROW },
        h(Button, { className: BUTTON_SM, onClick: preview }, "Preview diff"),
        h(Button, { className: BUTTON_SM, onClick: queue }, "Queue for approval"),
        h(Button, { variant: "ghost", className: BUTTON_SM, onClick: loadQueue }, loading ? "Loading..." : "Show pending")),
      h("pre", { className: MONO_BLOCK }, diff),
      pending.length ? h("div", { className: "flex flex-col gap-2" }, pending.map((u) => h("div", { key: u.id, className: "rounded-lg border border-border bg-background/40 p-3" }, h("div", { className: "flex items-center justify-between gap-2" }, h("code", { className: "text-xs" }, u.id), h("div", { className: "flex gap-1" }, h("button", { className: "rounded-md border border-border px-2 py-1 text-xs hover:bg-accent", onClick: () => decide(u.id, "approve") }, "Approve"), h("button", { className: "rounded-md border border-border px-2 py-1 text-xs hover:bg-accent", onClick: () => decide(u.id, "reject") }, "Reject"))), h("pre", { className: "mt-2 max-h-36 overflow-auto rounded bg-muted/30 p-2 font-mono text-xs" }, u.diff || "No diff")))) : h("div", { className: "rounded-lg border border-dashed border-border bg-muted/10 p-3 text-xs text-muted-foreground" }, "No pending updates"));
  }

  function ProjectDetail({ detail, loading, onRefresh, addToast }) {
    const [modal, setModal] = useState(null);
    if (loading) return h(EmptyState, { title: "Loading project" }, "Reading project.md...");
    if (!detail) return h(EmptyState, { title: "Pick a project" }, "Select a project to inspect its project.md state.");
    const tasks = detail.structured_tasks || [];
    const decisions = detail.decisions || [];
    const discoveries = detail.discoveries || [];
    async function refreshAfter(message) { addToast(message); if (onRefresh) await onRefresh(); }
    function openTask() { setModal({ type: "task", title: "Add task", fields: [{ key: "title", label: "Task title", required: true, autoFocus: true }, { key: "phase", label: "Phase", type: "select", options: ["DEFINE", "DESIGN", "BUILD", "VERIFY", "SHIP"] }] }); }
    function openDecision() { setModal({ type: "decision", title: "Add decision", fields: [{ key: "decision", label: "Decision", required: true, autoFocus: true }, { key: "rationale", label: "Rationale", required: true }, { key: "outcome", label: "Outcome" }] }); }
    function openDiscovery() { setModal({ type: "discovery", title: "Add discovery", fields: [{ key: "text", label: "Discovery", type: "textarea", required: true, autoFocus: true }] }); }
    function blockTask(task) { setModal({ type: "block", title: "Block task", task, fields: [{ key: "reason", label: "Reason", type: "textarea", required: true, autoFocus: true }] }); }
    async function submitModal(data) {
      try {
        if (modal.type === "task") await fetchJSON(`${API}/projects/${detail.id}/tasks`, { method: "POST", body: { path: detail.path, title: data.title, phase: data.phase } });
        if (modal.type === "decision") await fetchJSON(`${API}/projects/${detail.id}/decisions`, { method: "POST", body: { path: detail.path, decision: data.decision, rationale: data.rationale, outcome: data.outcome } });
        if (modal.type === "discovery") await fetchJSON(`${API}/projects/${detail.id}/discoveries`, { method: "POST", body: { path: detail.path, text: data.text } });
        if (modal.type === "block") await fetchJSON(`${API}/projects/${detail.id}/tasks/${modal.task.id}/block`, { method: "POST", body: { path: detail.path, reason: data.reason } });
        const label = modal.type === "block" ? "Blocked task" : "Saved " + modal.type;
        setModal(null); await refreshAfter(label);
      } catch (err) { addToast(err.message || String(err), "destructive"); }
    }
    async function onTaskAction(task, action) {
      if (action === "block") { blockTask(task); return; }
      try {
        await fetchJSON(`${API}/projects/${detail.id}/tasks/${task.id}/${action}`, { method: "POST", body: { path: detail.path } });
        await refreshAfter(action === "done" ? "Marked task done" : "Unblocked task");
      } catch (err) { addToast(err.message || String(err), "destructive"); }
    }
    return h("div", { className: "flex flex-col gap-4" },
      h(DetailHeader, { detail }),
      h(CurrentState, { detail }),
      h("div", { className: "grid gap-4 xl:grid-cols-2" },
        h(SectionCard, { title: "Tasks", action: h(Button, { className: BUTTON_SM, onClick: openTask }, "Add task") }, h(TaskList, { tasks, onTaskAction })),
        h(SectionCard, { title: "Key Decisions", action: h(Button, { className: BUTTON_SM, onClick: openDecision }, "Add decision") }, h(DecisionList, { decisions }))),
      h("div", { className: "grid gap-4 xl:grid-cols-2" },
        h(SectionCard, { title: "Discoveries", action: h(Button, { className: BUTTON_SM, onClick: openDiscovery }, "Add discovery") }, h(DiscoveryList, { discoveries })),
        h(SectionCard, { title: "Requirements" }, h(Requirements, { req: detail.requirements }))),
      h(QueuePanel, { detail, addToast, onRefresh }),
      h("details", { className: "rounded-xl border border-border bg-background/40" }, h("summary", { className: "cursor-pointer px-4 py-3 text-sm font-medium" }, "Raw project.md"), h("pre", { className: "max-h-[32rem] overflow-auto border-t border-border p-4 font-mono text-xs leading-relaxed" }, detail.raw || "")),
      modal ? h(FormModal, { title: modal.title, description: modal.type === "block" ? "Blocked tasks require an explicit reason." : null, fields: modal.fields, onCancel: () => setModal(null), onSubmit: submitModal, submitLabel: modal.type === "block" ? "Block task" : "Save" }) : null);
  }

  function LaunchPanel({ detail, health, onLaunch }) {
    const [task, setTask] = useState("");
    const [role, setRole] = useState("");
    const [roles, setRoles] = useState([]);
    const [launching, setLaunching] = useState(false);
    useEffect(() => { fetchJSON(`${API}/roster`).then((res) => { if (res.roster) setRoles(res.roster); }).catch(() => {}); }, []);
    async function launch() { setLaunching(true); try { await onLaunch(task, role); setTask(""); } finally { setLaunching(false); } }
    const ready = detail && task.trim() && (!health || !health.tmux || health.tmux.available);
    return h(Card, { className: "rounded-xl" }, h(CardHeader, { className: CARD_HEADER }, h(CardTitle, { className: "text-sm" }, "Orchestrator")), h(CardContent, { className: CARD_CONTENT_STACK + " text-sm" },
      !detail ? h("p", { className: "text-muted-foreground" }, "Select a project to launch an agent run.") : null,
      health && health.tmux && !health.tmux.available ? h("div", { className: "rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-xs text-destructive" }, "tmux is required for run management.") : null,
      h("textarea", { className: TEXTAREA_BASE + " min-h-20", placeholder: "Task description...", value: task, disabled: !detail, onChange: (e) => setTask(e.target.value) }),
      h("select", { className: INPUT_SM, value: role, disabled: !detail, onChange: (e) => setRole(e.target.value) }, h("option", { value: "" }, "Default role"), roles.map((r) => h("option", { key: r.id, value: r.id }, r.name))),
      h(Button, { className: BUTTON_SM + " w-full", disabled: !ready || launching, onClick: launch }, launching ? "Launching..." : "Launch run")));
  }

  function RunPanel({ detail }) {
    const [runs, setRuns] = useState([]);
    const [loading, setLoading] = useState(false);
    async function load() { if (!detail) return; setLoading(true); try { const res = await fetchJSON(`${API}/projects/${detail.id}/runs`); setRuns((res.runs || []).slice(0, 8)); } finally { setLoading(false); } }
    useEffect(() => { if (!detail) return; load(); const timer = setInterval(load, 3000); return () => clearInterval(timer); }, [detail && detail.id]);
    async function kill(id) { await fetchJSON(`${API}/projects/${detail.id}/runs/${id}/kill`, { method: "POST" }); await load(); }
    return h(Card, { className: "rounded-xl" }, h(CardHeader, { className: cn(CARD_HEADER, "flex flex-row items-center justify-between") }, h(CardTitle, { className: "text-sm" }, "Orchestrator Runs"), h(Button, { variant: "ghost", className: BUTTON_SM, disabled: !detail || loading, onClick: load }, loading ? "Refreshing..." : "Refresh")), h(CardContent, { className: CARD_CONTENT_STACK + " text-xs" },
      !detail ? h("p", { className: "text-muted-foreground" }, "Select a project to view runs.") : null,
      detail && !runs.length ? h("p", { className: "rounded-lg border border-dashed border-border bg-muted/10 p-3 text-muted-foreground" }, "No runs yet. Launch one from the Orchestrator panel.") : null,
      runs.map((r) => h("div", { key: r.id, className: "rounded-lg border border-border bg-background/40 p-3" }, h("div", { className: "flex items-center justify-between gap-2" }, h("code", { className: "font-mono" }, String(r.id || "").slice(0, 8)), h("span", { className: cn("rounded-full border px-2 py-0.5 text-[10px] font-medium", statusClass(r.status)) }, r.status || "unknown")), r.prompt ? h("div", { className: "mt-2 truncate text-muted-foreground" }, r.prompt) : null, r.status === "running" ? h("button", { className: "mt-2 rounded-md border border-border px-2 py-1 text-xs hover:bg-accent", onClick: () => kill(r.id) }, "Stop run") : null))));
  }

  function LifecyclePanels({ detail }) {
    const [gates, setGates] = useState(null), [ship, setShip] = useState(null), [repo, setRepo] = useState(null), [loading, setLoading] = useState(false);
    async function loadLifecycle() { if (!detail) return; setLoading(true); try { try { setGates(await fetchJSON(`${API}/gates`)); } catch (_) { setGates({ error: "Quality gates unavailable" }); } try { setShip(await fetchJSON(`${API}/projects/${detail.id}/ship?path=${encodeURIComponent(detail.path)}`)); } catch (_) { setShip({ error: "Ship checklist unavailable" }); } try { setRepo(await fetchJSON(`${API}/github/repo?path=${encodeURIComponent(detail.path)}`)); } catch (_) { setRepo({ error: "GitHub unavailable" }); } } finally { setLoading(false); } }
    return h(Card, { className: "rounded-xl" }, h(CardHeader, { className: CARD_HEADER }, h(CardTitle, { className: "text-sm" }, "Verify & Ship")), h(CardContent, { className: CARD_CONTENT_STACK + " text-xs" },
      h(Button, { className: BUTTON_SM + " w-full", disabled: !detail || loading, onClick: loadLifecycle }, loading ? "Loading..." : "Load Quality Gates, GitHub, Ship Checklist"),
      gates ? h("div", { className: "rounded-lg border border-border bg-background/40 p-3" }, "Quality Gates: ", gates.error || ((gates.gates || []).length + " configured")) : h("div", { className: "rounded-lg border border-dashed border-border bg-muted/10 p-3 text-muted-foreground" }, "Quality Gates ready to load."),
      repo ? h("div", { className: "rounded-lg border border-border bg-background/40 p-3" }, "GitHub: ", repo.error || repo.full_name || repo.repo || "detected") : null,
      ship ? h("div", { className: "rounded-lg border border-border bg-background/40 p-3" }, "Ship Checklist: ", ship.error || ((ship.items || []).filter((i) => i.checked).length + "/" + (ship.items || []).length + " complete")) : null));
  }

  function RootManager({ roots, rootStatus, onChange }) {
    const [input, setInput] = useState("");
    function add() { const value = input.trim(); if (!value) return; onChange([...(roots || []), value]); setInput(""); }
    return h("div", { className: "flex flex-col gap-3" },
      h("p", { className: "text-xs leading-relaxed text-muted-foreground" }, "Duplicate roots are ignored. Roots control which project.md files appear."),
      (roots || []).map((root) => { const status = (rootStatus || []).find((item) => item.path === root); return h("div", { key: root, className: "flex items-center justify-between gap-2 rounded-lg border border-border bg-background/40 p-2" }, h("div", { className: "min-w-0" }, h("code", { className: "block truncate font-mono text-xs" }, shortPath(root)), status ? h("div", { className: cn("mt-1 text-[10px]", status.ok ? "text-emerald-400" : "text-destructive") }, status.ok ? `${status.project_count} project(s)` : status.reason) : null), h(Button, { variant: "ghost", className: BUTTON_SM, onClick: () => onChange(roots.filter((r) => r !== root)) }, "Remove")); }),
      h("div", { className: "flex gap-2" }, h("input", { value: input, onChange: (e) => setInput(e.target.value), placeholder: "Add root path", className: "min-w-0 flex-1 " + INPUT_SM, onKeyDown: (e) => { if (e.key === "Enter") { e.preventDefault(); add(); } } }), h(Button, { className: BUTTON_SM, onClick: add }, "Add")));
  }

  function TutorialModal({ onCancel }) {
    const [step, setStep] = useState(0);
    const steps = [
      ["Overview", "Hermes Projects turns project.md into a live dashboard for planning, updates, and agent runs. This tutorial is optional help; the dashboard is fully usable without it."],
      ["Discover", "Use Roots, Search projects, Filter by phase, and Rescan to control which project.md files appear."],
      ["Create", "Use New Project to initialize a tracked project with required fields validated inline."],
      ["Read", "Select a project to inspect current state, tasks, requirements, decisions, discoveries, and session context."],
      ["Update", "Use Add task, Add decision, Add discovery, and task action buttons to safely update project.md."],
      ["Queue", "Use Diff preview / Queue to stage full-file proposals, review pending updates, and approve with snapshot protection."],
      ["Run", "Use Launch run and Orchestrator Runs to start and monitor tmux-backed Hermes work."],
      ["Verify", "Use Verify & Ship for quality gates, GitHub status, and release readiness."],
      ["Shortcuts", "Ctrl+R rescans, Ctrl+N points you to root management, and Escape closes dialogs or clears selection."],
    ];
    useEffect(() => { function onKey(e) { if (e.key === "Escape") onCancel(); } document.addEventListener("keydown", onKey); return () => document.removeEventListener("keydown", onKey); }, []);
    return h("div", { className: MODAL_OVERLAY, role: "dialog", "aria-label": "Projects tutorial", onClick: onCancel }, h("div", { className: MODAL_PANEL, onClick: (e) => e.stopPropagation() }, h("div", { className: "mb-3 text-[11px] uppercase tracking-[0.18em] text-muted-foreground" }, `Step ${step + 1} of ${steps.length}`), h("h3", { className: "text-lg font-semibold tracking-tight" }, steps[step][0]), h("p", { className: "mt-2 text-sm leading-relaxed text-muted-foreground" }, steps[step][1]), h("div", { className: "mt-5 flex justify-end gap-2" }, h(Button, { variant: "ghost", className: BUTTON_SM, onClick: onCancel }, "Close"), step > 0 ? h(Button, { variant: "ghost", className: BUTTON_SM, onClick: () => setStep(step - 1) }, "Back") : null, h(Button, { className: BUTTON_SM, onClick: () => step < steps.length - 1 ? setStep(step + 1) : onCancel() }, step < steps.length - 1 ? "Next" : "Done"))));
  }

  function CreateProjectModal({ roots, onCreate, onCancel }) {
    return h(FormModal, { title: "Create ProjectsMD project", description: "Create a project.md in a new or existing directory.", onCancel, onSubmit: onCreate, submitLabel: "Create project", fields: [
      { key: "root", label: "Project directory", required: true, autoFocus: true, placeholder: (roots && roots[0] ? roots[0] + "/new-project" : "~/projects/new-project") },
      { key: "name", label: "Project name", required: true, placeholder: "My Project" },
      { key: "owner", label: "Owner", placeholder: "Adam" },
      { key: "description", label: "Description", required: true, type: "textarea", placeholder: "What this project is" },
      { key: "core_value", label: "Core value", required: true, placeholder: "The one thing that matters" },
      { key: "tags", label: "Tags", placeholder: "hermes, dashboard" },
    ] });
  }

  class ErrorBoundary extends React.Component {
    constructor(props) { super(props); this.state = { error: null, copied: false }; }
    static getDerivedStateFromError(error) { return { error }; }
    componentDidCatch(error, info) { console.error("Projects plugin crashed:", error, info); }
    render() { if (!this.state.error) return this.props.children; const msg = String(this.state.error?.message || this.state.error); return h(Card, { className: "border-destructive/50" }, h(CardContent, { className: "p-6 text-sm" }, h("div", { className: "mb-1 font-semibold text-destructive" }, "Projects tab crashed"), h("div", { className: "mb-3 text-xs text-muted-foreground" }, msg), h(Button, { onClick: () => this.setState({ error: null }) }, "Retry"))); }
  }

  function ProjectsPageInner() {
    const [health, setHealth] = useState(null), [projects, setProjects] = useState([]), [selectedPath, setSelectedPath] = useState(null), [detail, setDetail] = useState(null);
    const [loading, setLoading] = useState(true), [detailLoading, setDetailLoading] = useState(false), [error, setError] = useState(null), [toasts, setToasts] = useState([]);
    const [query, setQuery] = useState(""), [phaseFilter, setPhaseFilter] = useState(""), [showCreateProject, setShowCreateProject] = useState(false), [showTutorial, setShowTutorial] = useState(false);
    function addToast(message, variant) { const id = Date.now() + Math.random(); setToasts((prev) => prev.concat({ id, message, variant: variant || "default" })); setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 3000); }
    const selectedProject = useMemo(() => projects.find((project) => project.path === selectedPath), [projects, selectedPath]);
    const visibleProjects = useMemo(() => { const q = query.trim().toLowerCase(); return projects.filter((project) => { const haystack = [project.name, project.path, project.owner, (project.tags || []).join(" "), project.next_action].join(" ").toLowerCase(); if (q && haystack.indexOf(q) === -1) return false; if (phaseFilter && String(project.phase || "").toLowerCase() !== phaseFilter) return false; return true; }); }, [projects, query, phaseFilter]);
    const totals = useMemo(() => projects.reduce((acc, project) => { const t = project.tasks || {}; acc.done += t.done || 0; acc.pending += t.pending || 0; acc.blocked += t.blocked || 0; acc.total += t.total || 0; return acc; }, { done: 0, pending: 0, blocked: 0, total: 0 }), [projects]);
    async function loadDetail(silent) { if (!selectedPath) { setDetail(null); return; } if (!silent) { setDetailLoading(true); setError(null); } try { setDetail(await fetchJSON(`${API}/projects/detail?path=${encodeURIComponent(selectedPath)}`)); } catch (err) { if (!silent) setError(err.message || String(err)); } finally { if (!silent) setDetailLoading(false); } }
    async function loadProjects(silent) { if (!silent) { setLoading(true); setError(null); } try { const healthData = await fetchJSON(`${API}/health`); const projectData = await fetchJSON(`${API}/projects`); const nextProjects = projectData.projects || []; setHealth(healthData); setProjects(nextProjects); setSelectedPath((current) => current && nextProjects.some((project) => project.path === current) ? current : (nextProjects[0]?.path || null)); } catch (err) { if (!silent) setError((err.message || String(err)) + ". Restart hermes dashboard if you just installed or updated the plugin."); } finally { if (!silent) setLoading(false); } }
    useEffect(() => { loadProjects(); }, []);
    useEffect(() => { loadDetail(); }, [selectedPath]);
    useEffect(() => { function refresh() { if (!document.hidden) loadProjects(true); } const timer = setInterval(refresh, 2000); window.addEventListener("focus", refresh); document.addEventListener("visibilitychange", refresh); return () => { clearInterval(timer); window.removeEventListener("focus", refresh); document.removeEventListener("visibilitychange", refresh); }; }, []);
    useEffect(() => { if (!selectedPath) return; function refresh() { if (!document.hidden) loadDetail(true); } const timer = setInterval(refresh, 2000); return () => clearInterval(timer); }, [selectedPath]);
    useEffect(() => { function onKey(e) { if (e.key === "r" && e.ctrlKey) { e.preventDefault(); loadProjects(); } if (e.key === "n" && e.ctrlKey) { e.preventDefault(); addToast("Use the Roots panel to add a project root."); } if (e.key === "Escape") { setShowTutorial(false); setSelectedPath(null); } } document.addEventListener("keydown", onKey); return () => document.removeEventListener("keydown", onKey); }, []);
    return h("div", { className: PAGE },
      h("div", { className: "flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between" }, h("div", null, h("div", { className: "mb-1 text-[11px] uppercase tracking-[0.22em] text-muted-foreground" }, "ProjectsMD for Hermes Agent"), h("div", { className: "flex items-center gap-2" }, h("span", { className: "text-xl" }, "⚡"), h("h1", { className: "text-2xl font-semibold tracking-tight" }, "Hermes Projects")), h("p", { className: "mt-1 text-sm text-muted-foreground" }, "Browse project.md files, update project state, and orchestrate agents across your work.")), h("div", { className: CONTROL_ROW }, health && health.projectsmd ? h(Badge, { variant: health.projectsmd.available ? "outline" : "destructive" }, health.projectsmd.available ? "projectsmd available" : "projectsmd missing") : null, h(Button, { variant: "ghost", className: BUTTON_SM, onClick: () => setShowTutorial(true) }, "Tutorial"), h(Button, { className: BUTTON_SM, onClick: () => setShowCreateProject(true) }, "New Project"), h(Button, { variant: "ghost", className: BUTTON_SM, onClick: () => loadProjects(), disabled: loading }, loading ? "Scanning..." : "Rescan"), h("a", { href: "https://hermes-agent.nousresearch.com/docs", target: "_blank", className: "rounded-md border border-border px-3 py-1.5 text-xs text-muted-foreground hover:bg-accent hover:text-foreground" }, "Docs"))),
      error ? h("div", { role: "alert", className: "rounded-xl border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive" }, error) : null,
      h("div", { className: "grid gap-3 sm:grid-cols-2 xl:grid-cols-4" }, h(StatCard, { label: "Projects", value: projects.length, detail: health && health.roots ? `${health.roots.length} roots scanned` : "" }), h(StatCard, { label: "Tasks", value: totals.total, detail: `${totals.done} done, ${totals.pending} pending`, help: "Counts come from project.md checkboxes." }), h(StatCard, { label: "Blocked", value: totals.blocked, detail: totals.blocked ? "Needs attention" : "No blockers found", help: "Blocked means explicit [!] or blocked metadata." }), h(StatCard, { label: "Selected", value: selectedProject ? selectedProject.phase || "unknown" : "—", detail: selectedProject ? shortPath(selectedProject.root) : "No project selected" })),
      h(Card, { className: "rounded-xl" }, h(CardContent, { className: "grid gap-3 p-3 sm:grid-cols-[minmax(0,1fr)_12rem]" }, h("input", { "aria-label": "Search projects", value: query, onChange: (e) => setQuery(e.target.value), placeholder: "Search projects by name, path, owner, tag...", className: INPUT_BASE }), h("select", { "aria-label": "Filter by phase", value: phaseFilter, onChange: (e) => setPhaseFilter(e.target.value), className: INPUT_BASE }, h("option", { value: "" }, "All phases"), ["define", "design", "build", "verify", "ship", "paused"].map((phase) => h("option", { key: phase, value: phase }, phase))))),
      health ? h(Card, { className: "rounded-xl" }, h(CardHeader, { className: CARD_HEADER }, h(CardTitle, { className: "text-sm" }, "Setup checklist")), h(CardContent, { className: CARD_CONTENT + " grid gap-2 text-xs sm:grid-cols-2 lg:grid-cols-4" }, [["projectsmd", health.projectsmd && health.projectsmd.available, "Install: cargo install --path ."], ["tmux", health.tmux && health.tmux.available, "Install tmux for orchestrator runs"], ["hermes", health.hermes && health.hermes.available, "Install Hermes Agent"], ["roots", (health.root_status || []).some((r) => r.ok), "Add a readable project root"]].map((item) => h("div", { key: item[0], className: cn("rounded-lg border p-3", item[1] ? "border-emerald-500/30 bg-emerald-500/5" : "border-destructive/40 bg-destructive/10") }, h("div", { className: "font-medium" }, item[1] ? "✓ " : "! ", item[0]), h("div", { className: "mt-1 text-muted-foreground" }, item[1] ? "Ready" : item[2]))))) : null,
      h("div", { className: SECTION_GRID }, h(Card, { className: "rounded-xl xl:sticky xl:top-4 xl:max-h-[calc(100vh-8rem)] xl:overflow-auto" }, h(CardHeader, { className: CARD_HEADER }, h(CardTitle, { className: "text-base" }, "Project files")), h(CardContent, { className: CARD_CONTENT }, h(ProjectList, { projects: visibleProjects, selectedPath, onSelect: setSelectedPath, loading }))), h("div", { className: "min-w-0" }, h(ProjectDetail, { detail, loading: detailLoading, addToast, onRefresh: async () => { await loadDetail(true); await loadProjects(true); } })), h("div", { className: "flex flex-col gap-4" }, h(LaunchPanel, { detail, health, onLaunch: async (task, role) => { if (!detail) return; const res = await fetchJSON(`${API}/projects/${detail.id}/runs`, { method: "POST", body: { path: detail.path, task, role_id: role } }); addToast("Run " + res.run_id + " started"); } }), h(RunPanel, { detail }), h(LifecyclePanels, { detail }), h(Card, { className: "rounded-xl" }, h(CardHeader, { className: CARD_HEADER }, h(CardTitle, { className: "text-sm" }, "Roots")), h(CardContent, { className: CARD_CONTENT }, h(RootManager, { roots: (health && health.roots) || [], rootStatus: (health && health.root_status) || [], onChange: async (nextRoots) => { try { await fetchJSON(`${API}/config`, { method: "PUT", body: { project_roots: nextRoots } }); await loadProjects(); } catch (err) { setError(err.message || String(err)); } } }))))),
      showCreateProject ? h(CreateProjectModal, { roots: (health && health.roots) || [], onCancel: () => setShowCreateProject(false), onCreate: async (data) => { const res = await fetchJSON(`${API}/projects`, { method: "POST", body: data }); setShowCreateProject(false); addToast("Created project " + (res.name || data.name)); await loadProjects(); if (res.path) setSelectedPath(res.path); } }) : null,
      showTutorial ? h(TutorialModal, { onCancel: () => setShowTutorial(false) }) : null,
      h(ToastContainer, { toasts }));
  }

  function ProjectsPage() { return h(ErrorBoundary, null, h(ProjectsPageInner)); }

  window.__HERMES_PLUGINS__.register("projectsmd", ProjectsPage, { priority: 50, min_version: "1.0.0", description: "ProjectsMD-powered project browsing and agent orchestration", category: "productivity" });
})();
