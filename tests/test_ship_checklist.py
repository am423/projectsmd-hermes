"""Tests for ship checklist."""
from __future__ import annotations

import tempfile
from pathlib import Path


from projectsmd_dashboard.ship_checklist import (
    ShipItem,
    _default_ship_checklist,
    check_ship_item,
    load_ship_checklist,
    save_ship_checklist,
    ship_status,
    uncheck_ship_item,
)


def test_default_ship_checklist():
    items = _default_ship_checklist()
    assert len(items) >= 4
    assert any(i.id == "tests" for i in items)


def test_save_and_load_ship_checklist():
    with tempfile.TemporaryDirectory() as tmp:
        md = Path(tmp) / "project.md"
        md.write_text("# Test", encoding="utf-8")
        items = [ShipItem(id="x", label="X", done=True)]
        save_ship_checklist(md, items)
        loaded = load_ship_checklist(md)
        assert len(loaded) == 1
        assert loaded[0].done is True


def test_check_and_uncheck_item():
    with tempfile.TemporaryDirectory() as tmp:
        md = Path(tmp) / "project.md"
        md.write_text("# Test", encoding="utf-8")
        items = _default_ship_checklist()
        save_ship_checklist(md, items)
        item = check_ship_item(md, "tests")
        assert item is not None
        assert item.done is True
        item2 = uncheck_ship_item(md, "tests")
        assert item2 is not None
        assert item2.done is False


def test_ship_status():
    with tempfile.TemporaryDirectory() as tmp:
        md = Path(tmp) / "project.md"
        md.write_text("# Test", encoding="utf-8")
        items = _default_ship_checklist()
        save_ship_checklist(md, items)
        status = ship_status(md)
        assert status["ready"] is False
        assert status["done"] == 0
        for item in items:
            check_ship_item(md, item.id)
        status = ship_status(md)
        assert status["ready"] is True
        assert status["done"] == status["total"]
