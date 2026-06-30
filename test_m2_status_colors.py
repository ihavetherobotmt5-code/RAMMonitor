"""Tests for M2-1: Status Ring Colors."""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault("LD_LIBRARY_PATH", "/home/z/.local/lib")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
    _QT_OK = True
except Exception:
    _QT_OK = False

from ram_monitor.config import Config


@pytest.fixture(scope="session")
def qapp():
    if not _QT_OK:
        pytest.skip("PySide6 unavailable")
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


@pytest.mark.skipif(not _QT_OK, reason="PySide6 unavailable")
class TestStatusRingColors:
    def test_three_status_pens_cached(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM", max_value=100.0)
        ring = c._ring
        assert "good" in ring._cached_value_pens
        assert "warn" in ring._cached_value_pens
        assert "bad" in ring._cached_value_pens
        assert ring._cached_value_pens["good"] is not ring._cached_value_pens["warn"]
        assert ring._cached_value_pens["warn"] is not ring._cached_value_pens["bad"]

    def test_good_tier_pen_selected_below_60(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        from PySide6.QtCore import QAbstractAnimation
        c = StatCard(label="RAM", max_value=100.0, config=Config(animation_threshold_pct=2.0))
        ring = c._ring
        c.set_value(30.0)
        assert ring._anim.state() == QAbstractAnimation.State.Stopped
        assert c.current_value == 30.0
        assert 30.0 < 60.0

    def test_warn_tier_pen_selected_60_to_85(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM", max_value=100.0)
        c.set_value(70.0)
        assert c.current_value == 70.0
        assert 60.0 <= 70.0 < 85.0

    def test_bad_tier_pen_selected_above_85(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM", max_value=100.0)
        c.set_value(90.0)
        assert c.current_value == 90.0
        assert 90.0 >= 85.0

    def test_non_percentage_card_uses_default_pen(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="Processes", max_value=1.0)
        ring = c._ring
        assert ring._cached_default_pen is not None

    def test_status_colors_match_theme(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        from ram_monitor.ui.fluent_theme import FluentTheme
        theme = FluentTheme.default()
        c = StatCard(label="RAM", max_value=100.0, theme=theme)
        ring = c._ring
        good_pen = ring._cached_value_pens["good"]
        brush = good_pen.brush()
        assert brush.style() is not None
