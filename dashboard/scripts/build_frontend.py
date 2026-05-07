#!/usr/bin/env python3
"""Build the ProjectsMD dashboard plugin frontend.

Hermes loads dashboard/dist/index.js directly. For now the source bundle lives in
dashboard/src/app.js and this script copies it to dist after lightweight safety
checks. Later slices can replace this with a real bundler while preserving the
same command.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "app.js"
DIST = ROOT / "dist" / "index.js"

FORBIDDEN = ["innerHTML", "dangerouslySetInnerHTML", "alert(", "prompt(", "location.reload"]


def main() -> int:
    text = SRC.read_text(encoding="utf-8")
    missing = [token for token in ["window.__HERMES_PLUGIN_SDK__", "window.__HERMES_PLUGINS__.register"] if token not in text]
    if missing:
        raise SystemExit(f"Source bundle missing required Hermes plugin hooks: {', '.join(missing)}")
    found = [token for token in FORBIDDEN if token in text]
    if found:
        raise SystemExit(f"Source bundle contains forbidden browser APIs: {', '.join(found)}")
    DIST.parent.mkdir(parents=True, exist_ok=True)
    DIST.write_text(text, encoding="utf-8")
    print(f"Built {DIST.relative_to(ROOT.parent)} from {SRC.relative_to(ROOT.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
