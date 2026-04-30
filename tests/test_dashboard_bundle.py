"""Frontend bundle smoke tests.

These are string-level assertions against the built JS bundle to prevent
the SDK mistake that broke the first screen (using sdk.Card instead of
SDK.components.Card).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import pytest


class TestManifest:
    def test_manifest_valid(self):
        manifest = json.loads((REPO_ROOT / "dashboard" / "manifest.json").read_text())
        assert manifest["name"] == "projectsmd"
        assert manifest["label"] == "Projects"
        assert manifest["tab"]["path"] == "/projects"
        assert manifest["entry"] == "dist/index.js"
        assert manifest["api"] == "plugin_api.py"


class TestBundle:
    def test_bundle_uses_sdk_components(self):
        bundle = (REPO_ROOT / "dashboard" / "dist" / "index.js").read_text()
        assert "SDK.components" in bundle
        assert "SDK.hooks" in bundle
        assert "SDK.utils" in bundle
        assert "SDK.fetchJSON" in bundle

    def test_bundle_registers_plugin(self):
        bundle = (REPO_ROOT / "dashboard" / "dist" / "index.js").read_text()
        assert "window.__HERMES_PLUGINS__.register" in bundle
        assert '"projectsmd"' in bundle

    def test_bundle_has_error_boundary(self):
        bundle = (REPO_ROOT / "dashboard" / "dist" / "index.js").read_text()
        assert "ErrorBoundary" in bundle

    def test_bundle_is_iife(self):
        bundle = (REPO_ROOT / "dashboard" / "dist" / "index.js").read_text()
        assert bundle.strip().startswith("(function ()")
        assert bundle.strip().endswith("})();")
