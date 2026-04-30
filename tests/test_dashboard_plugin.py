import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


class DashboardManifestTests(unittest.TestCase):
    def test_manifest_registers_projects_tab(self):
        manifest_path = REPO_ROOT / "dashboard" / "manifest.json"
        manifest = json.loads(manifest_path.read_text())

        self.assertEqual(manifest["name"], "projectsmd")
        self.assertEqual(manifest["label"], "Projects")
        self.assertEqual(manifest["tab"]["path"], "/projects")
        self.assertEqual(manifest["entry"], "dist/index.js")
        self.assertEqual(manifest["api"], "plugin_api.py")

    def test_frontend_bundle_uses_hermes_plugin_sdk(self):
        bundle = (REPO_ROOT / "dashboard" / "dist" / "index.js").read_text()
        self.assertIn("window.__HERMES_PLUGIN_SDK__", bundle)
        self.assertIn("SDK.components", bundle)
        self.assertIn("SDK.hooks", bundle)
        self.assertIn("window.__HERMES_PLUGINS__.register", bundle)
        self.assertIn("projectsmd", bundle)

    def test_plugin_api_exports_router(self):
        api_path = REPO_ROOT / "dashboard" / "plugin_api.py"
        spec = importlib.util.spec_from_file_location("projectsmd_plugin_api", api_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        self.assertTrue(hasattr(module, "router"))

    def test_api_functions_are_callable_directly(self):
        from projectsmd_dashboard.api import health, projects

        self.assertTrue(health()["ok"])
        response = projects()
        self.assertIn("projects", response)
        self.assertIn("roots", response)


class ProjectScanTests(unittest.TestCase):
    def test_scan_projects_finds_project_md_and_counts_tasks(self):
        from projectsmd_dashboard.project_scan import scan_projects

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "demo"
            project_dir.mkdir()
            (project_dir / "project.md").write_text(
                """---
project: Demo Project
status: build
created: 2026-04-30
updated: 2026-04-30
owner: Adam
---

## Current State

**Phase:** build
**Next action:** Ship the dashboard tab
**Blockers:** None

## Tasks

### Phase: BUILD

- [x] Scaffold plugin
- [ ] Render project list
- [ ] Fix blocker <!-- blocked: waiting on docs -->
""",
                encoding="utf-8",
            )

            projects = scan_projects([root])

        self.assertEqual(len(projects), 1)
        project = projects[0]
        self.assertEqual(project["name"], "Demo Project")
        self.assertEqual(project["status"], "build")
        self.assertEqual(project["phase"], "build")
        self.assertEqual(project["tasks"]["done"], 1)
        self.assertEqual(project["tasks"]["pending"], 2)
        self.assertEqual(project["tasks"]["blocked"], 1)
        self.assertEqual(project["next_action"], "Ship the dashboard tab")

    def test_project_detail_includes_sections_and_raw_text(self):
        from projectsmd_dashboard.project_scan import get_project_detail

        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp) / "demo"
            project_dir.mkdir()
            path = project_dir / "project.md"
            path.write_text(
                """---
project: Demo
status: define
---

## What This Is

A demo project.

## Current State

**Phase:** define
**Next action:** Decide scope

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use plugin | Follows Hermes docs | Pending |
""",
                encoding="utf-8",
            )
            detail = get_project_detail(path)

        self.assertEqual(detail["name"], "Demo")
        self.assertIn("What This Is", detail["sections"])
        self.assertIn("Current State", detail["sections"])
        self.assertIn("project: Demo", detail["raw"])


if __name__ == "__main__":
    unittest.main()
