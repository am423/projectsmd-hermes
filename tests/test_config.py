"""Tests for plugin config."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from projectsmd_dashboard.config import default_config, load_config, save_config


class TestConfig:
    def test_default_config_has_roots(self):
        config = default_config()
        assert "project_roots" in config
        assert isinstance(config["project_roots"], list)
        assert config["auto_validate"] is True

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
