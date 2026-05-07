"""Tests for plugin config."""
from __future__ import annotations

import os
import tempfile


from projectsmd_dashboard.config import default_config, load_config, save_config, validate_roots


class TestConfig:
    def test_default_config_has_roots(self):
        config = default_config()
        assert "project_roots" in config
        assert isinstance(config["project_roots"], list)
        assert config["auto_validate"] is True
        assert config["favorites"] == []
        assert config["recent_project_paths"] == []
        assert config["sort"] == "updated_desc"
        assert config["filters"]["query"] == ""

    def test_load_save_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["HERMES_HOME"] = tmp
            try:
                config = default_config()
                config["project_roots"] = ["/tmp/projects"]
                save_config(config)
                loaded = load_config()
                assert loaded["project_roots"] == ["/tmp/projects"]
            finally:
                del os.environ["HERMES_HOME"]

    def test_load_missing_returns_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["HERMES_HOME"] = tmp
            try:
                loaded = load_config()
                assert loaded["auto_validate"] is True
            finally:
                del os.environ["HERMES_HOME"]

    def test_validate_roots_reports_status_and_project_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = os.path.join(tmp, "root")
            project = os.path.join(root, "demo")
            os.makedirs(project)
            with open(os.path.join(project, "project.md"), "w", encoding="utf-8") as fh:
                fh.write("---\nproject: Demo\n---\n")

            statuses = validate_roots([root, os.path.join(tmp, "missing")])

        assert statuses[0]["ok"] is True
        assert statuses[0]["project_count"] == 1
        assert statuses[1]["ok"] is False
        assert statuses[1]["reason"] == "not_found"
