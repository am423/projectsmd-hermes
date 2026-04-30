#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
hermes_home="${HERMES_HOME:-$HOME/.hermes}"
plugin_dir="$hermes_home/plugins/projectsmd"

mkdir -p "$(dirname "$plugin_dir")"
ln -sfn "$repo_root" "$plugin_dir"

printf 'Installed ProjectsMD dashboard plugin:\n  %s -> %s\n' "$plugin_dir" "$repo_root"
printf 'Restart `hermes dashboard` so plugin_api.py routes are mounted.\n'
