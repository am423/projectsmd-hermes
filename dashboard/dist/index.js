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
  const fetchJSON = SDK.fetchJSON || ((url) => fetch(url).then((r) => {
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
    return r.json();
  }));

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

  function SectionBlock({ title, body }) {
    if (!String(body || "").trim()) return null;
    return h(Card, null,
      h(CardHeader, { className: "pb-2" }, h(CardTitle, { className: "text-sm" }, title)),
      h(CardContent, { className: "pt-0" },
        h("pre", { className: "max-h-96 overflow-auto whitespace-pre-wrap rounded-md bg-muted/40 p-3 font-mono text-xs leading-relaxed text-foreground" }, body)));
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

    const sections = detail.sections || {};
    return h("div", { className: "flex flex-col gap-4" },
      h(DetailHeader, { detail }),
      h(CurrentState, { detail }),
      h("div", { className: "grid gap-4 xl:grid-cols-2" },
        h(SectionBlock, { title: "What This Is", body: sections["What This Is"] }),
        h(SectionBlock, { title: "Key Decisions", body: sections["Key Decisions"] })),
      h(SectionBlock, { title: "Tasks", body: sections.Tasks }),
      h(SectionBlock, { title: "Discoveries", body: sections.Discoveries }),
      h("details", { className: "rounded-lg border border-border bg-background/40" },
        h("summary", { className: "cursor-pointer p-3 text-sm font-medium" }, "Raw project.md"),
        h("pre", { className: "max-h-[32rem] overflow-auto border-t border-border p-3 font-mono text-xs leading-relaxed" }, detail.raw || "")));
  }

  function LaunchPanel({ hasSelection }) {
    return h(Card, null,
      h(CardHeader, { className: "pb-2" }, h(CardTitle, { className: "text-sm" }, "Orchestrator")),
      h(CardContent, { className: "pt-0 text-sm" },
        h("p", { className: "mb-3 text-muted-foreground" },
          "Launch controls are intentionally disabled in this slice. The page is now a project browser only."),
        h(Button, { disabled: true, className: "w-full" }, hasSelection ? "Launch coming next" : "Select a project first")));
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
          h(LaunchPanel, { hasSelection: Boolean(selectedPath) }),
          h(Card, null,
            h(CardHeader, { className: "pb-2" }, h(CardTitle, { className: "text-sm" }, "Roots")),
            h(CardContent, { className: "pt-0" },
              h("div", { className: "flex flex-col gap-2" },
                (health && health.roots || []).map((root) => h("code", {
                  key: root,
                  className: "rounded bg-muted/50 px-2 py-1 font-mono text-xs text-muted-foreground",
                }, shortPath(root)))))))));
  }

  function ProjectsPage() {
    return h(ErrorBoundary, null, h(ProjectsPageInner));
  }

  window.__HERMES_PLUGINS__.register("projectsmd", ProjectsPage);
})();
