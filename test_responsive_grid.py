"""Tests for `ResponsiveGridLayout` — reflow behavior, no display required."""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault("LD_LIBRARY_PATH", "/home/z/.local/lib")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QWidget
    _QT_OK = True
except Exception:
    _QT_OK = False

from ram_monitor.ui.fluent_theme import FluentTheme
from ram_monitor.ui.responsive_grid import ResponsiveGridLayout


@pytest.fixture(scope="session")
def qapp():
    if not _QT_OK:
        pytest.skip("PySide6 unavailable")
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


def _make_widget(qapp) -> QWidget:
    w = QWidget()
    w.resize(200, 100)
    return w


@pytest.mark.skipif(not _QT_OK, reason="PySide6 unavailable")
class TestTierClassification:
    def test_tier_xl(self, qapp) -> None:
        host = QWidget(); host.resize(1920, 1080)
        grid = ResponsiveGridLayout(host)
        grid.relayout(force=True)
        assert grid.current_tier == "xxl"

    def test_tier_lg(self, qapp) -> None:
        host = QWidget(); host.resize(1000, 800)
        grid = ResponsiveGridLayout(host)
        grid.relayout(force=True)
        assert grid.current_tier == "lg"

    def test_tier_md(self, qapp) -> None:
        host = QWidget(); host.resize(800, 600)
        grid = ResponsiveGridLayout(host)
        grid.relayout(force=True)
        assert grid.current_tier == "md"

    def test_tier_sm(self, qapp) -> None:
        host = QWidget(); host.resize(500, 400)
        grid = ResponsiveGridLayout(host)
        grid.relayout(force=True)
        assert grid.current_tier == "sm"

    def test_boundary_1280_is_xl(self, qapp) -> None:
        host = QWidget(); host.resize(1280, 800)
        grid = ResponsiveGridLayout(host)
        grid.relayout(force=True)
        assert grid.current_tier == "xl"

    def test_boundary_1279_is_lg(self, qapp) -> None:
        host = QWidget(); host.resize(1279, 800)
        grid = ResponsiveGridLayout(host)
        grid.relayout(force=True)
        assert grid.current_tier == "lg"


@pytest.mark.skipif(not _QT_OK, reason="PySide6 unavailable")
class TestArrangement:
    def test_xl_4_cards_share_one_row(self, qapp) -> None:
        host = QWidget(); host.resize(1400, 800)
        grid = ResponsiveGridLayout(host)
        cards = [_make_widget(qapp) for _ in range(4)]
        for c in cards:
            grid.add_card(c)
        g = host.layout()
        for i, card in enumerate(cards):
            idx = g.indexOf(card)
            r, c, rs, cs = g.getItemPosition(idx)
            assert r == 0, f"Card {i} should be in row 0, got row {r}"
            assert c == i

    def test_md_4_cards_form_2x2(self, qapp) -> None:
        host = QWidget(); host.resize(800, 800)
        grid = ResponsiveGridLayout(host)
        cards = [_make_widget(qapp) for _ in range(4)]
        for c in cards:
            grid.add_card(c)
        g = host.layout()
        expected = [(0, 0), (0, 1), (1, 0), (1, 1)]
        for i, card in enumerate(cards):
            idx = g.indexOf(card)
            r, c, rs, cs = g.getItemPosition(idx)
            assert (r, c) == expected[i]

    def test_sm_4_cards_stack_vertically(self, qapp) -> None:
        host = QWidget(); host.resize(500, 800)
        grid = ResponsiveGridLayout(host)
        cards = [_make_widget(qapp) for _ in range(4)]
        for c in cards:
            grid.add_card(c)
        g = host.layout()
        for i, card in enumerate(cards):
            idx = g.indexOf(card)
            r, c, rs, cs = g.getItemPosition(idx)
            assert r == i

    def test_xl_2_charts_share_one_row(self, qapp) -> None:
        host = QWidget(); host.resize(1400, 800)
        grid = ResponsiveGridLayout(host)
        grid.add_chart(_make_widget(qapp))
        grid.add_chart(_make_widget(qapp))
        g = host.layout()
        positions = []
        for i in range(g.count()):
            item = g.itemAt(i)
            if item and item.widget():
                w = item.widget()
                idx = g.indexOf(w)
                r, c, rs, cs = g.getItemPosition(idx)
                positions.append((r, c))
        assert all(p[0] == 0 for p in positions)


@pytest.mark.skipif(not _QT_OK, reason="PySide6 unavailable")
class TestRecomputeGuards:
    def test_relayout_no_force_returns_same_tier(self, qapp) -> None:
        host = QWidget(); host.resize(1400, 800)
        grid = ResponsiveGridLayout(host)
        grid.add_card(_make_widget(qapp))
        tier_before = grid.current_tier
        grid.relayout(force=False)
        assert grid.current_tier == tier_before

    def test_relayout_force_keeps_tier_but_reapplies(self, qapp) -> None:
        host = QWidget(); host.resize(1400, 800)
        grid = ResponsiveGridLayout(host)
        grid.add_card(_make_widget(qapp))
        grid.relayout(force=True)
        assert grid.current_tier is not None

    def test_tier_change_updates_tier(self, qapp) -> None:
        host = QWidget(); host.resize(1400, 800)
        grid = ResponsiveGridLayout(host)
        grid.add_card(_make_widget(qapp))
        assert grid.current_tier == "xl"
        host.resize(500, 400)
        grid.relayout(force=False)
        assert grid.current_tier == "sm"


@pytest.mark.skipif(not _QT_OK, reason="PySide6 unavailable")
class TestWidgetSurvival:
    def test_cards_survive_tier_change(self, qapp) -> None:
        host = QWidget(); host.resize(1400, 800)
        grid = ResponsiveGridLayout(host)
        cards = [_make_widget(qapp) for _ in range(4)]
        for c in cards:
            grid.add_card(c)
        host.resize(500, 400)
        grid.relayout(force=False)
        for c in cards:
            assert host.layout().indexOf(c) >= 0
        host.resize(1400, 800)
        grid.relayout(force=False)
        for c in cards:
            assert host.layout().indexOf(c) >= 0


@pytest.mark.skipif(not _QT_OK, reason="PySide6 unavailable")
class TestProcessPanelPlacement:
    def test_panel_always_at_bottom(self, qapp) -> None:
        host = QWidget(); host.resize(1400, 800)
        grid = ResponsiveGridLayout(host)
        for _ in range(4):
            grid.add_card(_make_widget(qapp))
        grid.add_chart(_make_widget(qapp))
        grid.add_chart(_make_widget(qapp))
        panel = _make_widget(qapp)
        grid.set_process_panel(panel)
        g = host.layout()
        idx = g.indexOf(panel)
        r, c, rs, cs = g.getItemPosition(idx)
        assert r == 2


@pytest.mark.skipif(not _QT_OK, reason="PySide6 unavailable")
class TestReservedCell:
    def test_reserved_appears_on_xl(self, qapp) -> None:
        host = QWidget(); host.resize(1400, 800)
        grid = ResponsiveGridLayout(host)
        grid.add_card(_make_widget(qapp))
        reserved = _make_widget(qapp)
        grid.set_reserved(reserved)
        g = host.layout()
        assert g.indexOf(reserved) >= 0

    def test_reserved_hidden_on_sm(self, qapp) -> None:
        host = QWidget(); host.resize(500, 400)
        grid = ResponsiveGridLayout(host)
        grid.add_card(_make_widget(qapp))
        reserved = _make_widget(qapp)
        grid.set_reserved(reserved)
        g = host.layout()
        assert g.indexOf(reserved) == -1
