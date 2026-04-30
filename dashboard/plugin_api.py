"""Dashboard plugin API shim for Hermes Agent.

Hermes imports this file from dashboard/plugin_api.py and mounts the exported
router at /api/plugins/projectsmd.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from projectsmd_dashboard.api import router  # noqa: E402,F401
