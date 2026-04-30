#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 -m unittest tests.test_dashboard_plugin -v
node --check "$repo_root/dashboard/dist/index.js"
python3 - <<'PY'
import importlib.util
import json
from pathlib import Path

root = Path.cwd()
manifest = json.loads((root / 'dashboard' / 'manifest.json').read_text())
assert manifest['name'] == 'projectsmd'
assert manifest['label'] == 'Projects'
assert manifest['tab']['path'] == '/projects'
assert manifest['entry'] == 'dist/index.js'
assert manifest['api'] == 'plugin_api.py'

spec = importlib.util.spec_from_file_location('plugin_api', root / 'dashboard' / 'plugin_api.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert hasattr(module, 'router')
print('dashboard smoke ok')
PY

printf 'Dashboard smoke passed.\n'
printf 'If you changed plugin_api.py routes, restart hermes dashboard for them to mount.\n'
