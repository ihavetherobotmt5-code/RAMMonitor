"""Tests for M2-7: Animation Audit."""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault("LD_LIBRARY_PATH", "/home/z/.local/lib")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QAbstractAnimation
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
class TestAnimationAudit:
    def test_single_animation_per_ring_meter(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM", max_value=100.0)
        ring = c._ring
        assert ring._anim is not None
        anim_before = ring._anim
        c.set_value(50.0)
        c.set_value(55.0)
        c.set_value(60.0)
        assert ring._anim is anim_before

    def test_no_lambda_in_animation_connection(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM", max_value=100.0)
        c.set_value(50.0)

    def test_animation_state_transitions(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM", max_value=100.0, config=Config(animation_threshold_pct=2.0))
        ring = c._ring
        assert ring._anim.state() == QAbstractAnimation.State.Stopped
        c.set_value(50.0)
        assert ring._anim.state() == QAbstractAnimation.State.Running
        c.set_value(50.5)
        assert ring._anim.state() == QAbstractAnimation.State.Stopped

    def test_animation_duration_matches_config(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        config = Config(animation_duration_ms=300)
        c = StatCard(label="RAM", max_value=100.0, config=config)
        assert c._ring._anim.duration() == 300

    def test_easing_curve_is_outcubic(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        from PySide6.QtCore import QEasingCurve
        c = StatCard(label="RAM", max_value=100.0)
        assert c._ring._anim.easingCurve() == QEasingCurve.Type.OutCubic

    def test_no_per_tick_allocation(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        import tracemalloc
        c = StatCard(label="RAM", max_value=100.0)
        tracemalloc.start()
        snap1 = tracemalloc.take_snapshot()
        for i in range(100):
            c.set_value(50.0 + (i % 20))
        snap2 = tracemalloc.take_snapshot()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        diff = snap2.compare_to(snap1, "lineno")
        stats_cards_growth = sum(
            s.size_diff for s in diff
            if "stats_cards.py" in str(s) and s.size_diff > 0
        )
        assert stats_cards_growth < 50_000
