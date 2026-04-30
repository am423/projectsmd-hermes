(function () {
  const sdk = window.__HERMES_PLUGIN_SDK__;
  const React = sdk && sdk.React;
  const register = window.__HERMES_PLUGINS__ && window.__HERMES_PLUGINS__.register;

  if (!sdk || !React || !register) {
    console.error("ProjectsMD plugin: Hermes plugin SDK is not available");
    return;
  }

  const { useEffect, useMemo, useState } = React;
  const Card = sdk.Card || "div";
  const CardHeader = sdk.CardHeader || "div";
  const CardTitle = sdk.CardTitle || "h2";
  const CardContent = sdk.CardContent || "div";
  const Button = sdk.Button || "button";
  const Badge = sdk.Badge || "span";

  const h = React.createElement;

  async function fetchJson(url) {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`${response.status} ${response.statusText}`);
    }
    return response.json();
  }

  function taskSummary(project) {
    const tasks = project.tasks || { done: 0, pending: 0, blocked: 0, total: 0 };
    return `${tasks.done}/${tasks.total} done · ${tasks.pending} pending · ${tasks.blocked} blocked`;
  }

  function ProjectList({ projects, selectedPath, onSelect }) {
    if (!projects.length) {
      return h("div", { className: "projectsmd-empty" },
        h("p", null, "No project.md files found in configured roots."),
        h("p", null, "Set PROJECTSMD_ROOTS or create a project with projectsmd init."));
    }

    return h("div", { className: "projectsmd-list" }, projects.map((project) =>
      h("button", {
        key: project.path,
        className: `projectsmd-project-card ${selectedPath === project.path ? "is-selected" : ""}`,
        onClick: () => onSelect(project.path)
      },
        h("div", { className: "projectsmd-project-card-title" }, project.name || project.root),
        h("div", { className: "projectsmd-project-card-meta" },
          h("span", null, `Phase: ${project.phase || "unknown"}`),
          h("span", null, taskSummary(project))
        ),
        project.next_action ? h("div", { className: "projectsmd-next" }, project.next_action) : null
      )
    ));
  }

  function SectionBlock({ title, body }) {
    if (!body) return null;
    return h("section", { className: "projectsmd-section" },
      h("h3", null, title),
      h("pre", null, body)
    );
  }

  function ProjectDetail({ detail, loading }) {
    if (loading) return h("div", { className: "projectsmd-panel" }, "Loading project...");
    if (!detail) return h("div", { className: "projectsmd-panel" }, "Select a project to inspect it.");
    const sections = detail.sections || {};
    const tasks = detail.tasks || {};

    return h("div", { className: "projectsmd-detail" },
      h("div", { className: "projectsmd-detail-header" },
        h("div", null,
          h("h2", null, detail.name),
          h("div", { className: "projectsmd-path" }, detail.path)
        ),
        h("div", { className: "projectsmd-badges" },
          h(Badge, null, detail.phase || "unknown"),
          h(Badge, null, `${tasks.done || 0}/${tasks.total || 0} done`),
          tasks.blocked ? h(Badge, null, `${tasks.blocked} blocked`) : null
        )
      ),
      h("div", { className: "projectsmd-current-state" },
        h("h3", null, "Current State"),
        h("div", null, h("strong", null, "Next action: "), detail.next_action || "Not set"),
        h("div", null, h("strong", null, "Blockers: "), detail.blockers || "None")
      ),
      h(SectionBlock, { title: "What This Is", body: sections["What This Is"] }),
      h(SectionBlock, { title: "Tasks", body: sections.Tasks }),
      h(SectionBlock, { title: "Key Decisions", body: sections["Key Decisions"] }),
      h(SectionBlock, { title: "Discoveries", body: sections.Discoveries }),
      h("details", { className: "projectsmd-raw" },
        h("summary", null, "Raw project.md"),
        h("pre", null, detail.raw || "")
      )
    );
  }

  function LaunchPanel() {
    return h("div", { className: "projectsmd-launch" },
      h("h3", null, "Orchestrator"),
      h("p", null, "Read-only browser is active. Tmux orchestrator launch is the next implementation slice."),
      h(Button, { disabled: true }, "Launch Orchestrator")
    );
  }

  function ProjectsPage() {
    const [health, setHealth] = useState(null);
    const [projects, setProjects] = useState([]);
    const [selectedPath, setSelectedPath] = useState(null);
    const [detail, setDetail] = useState(null);
    const [loading, setLoading] = useState(true);
    const [detailLoading, setDetailLoading] = useState(false);
    const [error, setError] = useState(null);

    const selectedProject = useMemo(() => projects.find((project) => project.path === selectedPath), [projects, selectedPath]);

    async function loadProjects() {
      setLoading(true);
      setError(null);
      try {
        const [healthData, projectData] = await Promise.all([
          fetchJson("/api/plugins/projectsmd/health"),
          fetchJson("/api/plugins/projectsmd/projects")
        ]);
        setHealth(healthData);
        setProjects(projectData.projects || []);
        if (!selectedPath && projectData.projects && projectData.projects.length) {
          setSelectedPath(projectData.projects[0].path);
        }
      } catch (err) {
        setError(err.message || String(err));
      } finally {
        setLoading(false);
      }
    }

    useEffect(() => { loadProjects(); }, []);

    useEffect(() => {
      if (!selectedPath) {
        setDetail(null);
        return;
      }
      setDetailLoading(true);
      fetchJson(`/api/plugins/projectsmd/projects/detail?path=${encodeURIComponent(selectedPath)}`)
        .then(setDetail)
        .catch((err) => setError(err.message || String(err)))
        .finally(() => setDetailLoading(false));
    }, [selectedPath]);

    return h("div", { className: "projectsmd-page" },
      h("div", { className: "projectsmd-header" },
        h("div", null,
          h("h1", null, "Projects"),
          h("p", null, "ProjectsMD project.md browser for Hermes Agent.")
        ),
        h(Button, { onClick: loadProjects, disabled: loading }, loading ? "Scanning..." : "Rescan")
      ),
      error ? h("div", { className: "projectsmd-error" }, error) : null,
      h("div", { className: "projectsmd-health" },
        health ? h("span", null, `projectsmd: ${health.projectsmd && health.projectsmd.available ? "available" : "missing"}`) : null,
        selectedProject ? h("span", null, selectedProject.root) : null
      ),
      h("div", { className: "projectsmd-grid" },
        h(Card, { className: "projectsmd-card" },
          h(CardHeader, null, h(CardTitle, null, "Project files")),
          h(CardContent, null, h(ProjectList, { projects, selectedPath, onSelect: setSelectedPath }))
        ),
        h(Card, { className: "projectsmd-card projectsmd-main" },
          h(CardHeader, null, h(CardTitle, null, "Project detail")),
          h(CardContent, null, h(ProjectDetail, { detail, loading: detailLoading }))
        ),
        h(Card, { className: "projectsmd-card" },
          h(CardHeader, null, h(CardTitle, null, "Launch")),
          h(CardContent, null, h(LaunchPanel))
        )
      )
    );
  }

  window.__HERMES_PLUGINS__.register("projectsmd", ProjectsPage);
})();
