"""Tests for `ram_monitor.ui.stats_cards`."""
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
from ram_monitor.utils.formatters import format_percent


@pytest.fixture(scope="session")
def qapp():
    if not _QT_OK:
        pytest.skip("PySide6 unavailable")
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


@pytest.mark.skipif(not _QT_OK, reason="PySide6 unavailable")
class TestStatCardAPI:
    def test_constructor_signature(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM", accent="#60CDFF", formatter=lambda v: format_percent(v),
                     max_value=100.0, parent=None, config=Config())
        assert c is not None
        assert c.current_value == 0.0

    def test_set_value_signature(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM")
        c.set_value(42.0, sub_text="2.0 GB used")
        assert c.current_value == 42.0

    def test_set_sub_text(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM")
        c.set_sub_text("hello")

    def test_value_changed_signal_emitted(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM")
        received: list[float] = []
        c.value_changed.connect(lambda v: received.append(v))
        c.set_value(50.0)
        assert received == [50.0]

    def test_current_value_property(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM")
        assert c.current_value == 0.0
        c.set_value(75.0)
        assert c.current_value == 75.0


@pytest.mark.skipif(not _QT_OK, reason="PySide6 unavailable")
class TestSmartAnimationThreshold:
    def test_small_delta_skips_animation(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM", max_value=100.0, config=Config(animation_threshold_pct=2.0))
        c.set_value(50.0)
        ring = c._ring
        c.set_value(50.5)
        assert ring._anim.state() == QAbstractAnimation.State.Stopped

    def test_large_delta_triggers_animation(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM", max_value=100.0, config=Config(animation_threshold_pct=2.0))
        c.set_value(50.0)
        c.set_value(55.0)
        assert c._ring._anim.state() == QAbstractAnimation.State.Running

    def test_threshold_boundary_just_below(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM", max_value=100.0, config=Config(animation_threshold_pct=2.0))
        c.set_value(50.0)
        c.set_value(52.0)
        assert c._ring._anim.state() == QAbstractAnimation.State.Stopped

    def test_threshold_boundary_just_above(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM", max_value=100.0, config=Config(animation_threshold_pct=2.0))
        c.set_value(50.0)
        c.set_value(52.01)
        assert c._ring._anim.state() == QAbstractAnimation.State.Running

    def test_negative_delta_above_threshold_animates(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM", max_value=100.0, config=Config(animation_threshold_pct=2.0))
        c.set_value(80.0)
        c.set_value(70.0)
        assert c._ring._anim.state() == QAbstractAnimation.State.Running

    def test_threshold_zero_means_always_animate(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM", max_value=100.0, config=Config(animation_threshold_pct=0.0))
        c.set_value(50.0)
        c.set_value(50.01)
        assert c._ring._anim.state() == QAbstractAnimation.State.Running

    def test_custom_threshold_respected(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM", max_value=100.0, config=Config(animation_threshold_pct=5.0))
        c.set_value(50.0)
        c.set_value(54.0)
        assert c._ring._anim.state() == QAbstractAnimation.State.Stopped
        c.set_value(60.0)
        assert c._ring._anim.state() == QAbstractAnimation.State.Running


@pytest.mark.skipif(not _QT_OK, reason="PySide6 unavailable")
class TestRingMeterAndBar:
    def test_ring_meter_receives_value(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM", max_value=100.0)
        c.set_value(42.0)
        assert c._ring.current_value == 42.0

    def test_thin_bar_receives_value(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM", max_value=100.0)
        c.set_value(50.0)
        assert c._meter.value() == 500

    def test_thin_bar_clamps_overflow(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM", max_value=100.0)
        c.set_value(150.0)
        assert c._meter.value() == 1000

    def test_thin_bar_clamps_underflow(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM", max_value=100.0)
        c.set_value(-10.0)
        assert c._meter.value() == 0


@pytest.mark.skipif(not _QT_OK, reason="PySide6 unavailable")
class TestNoGraphicsDropShadowEffect:
    def test_card_has_no_shadow_effect(self, qapp) -> None:
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM")
        effects = c.graphicsEffect()
        assert effects is None or not isinstance(effects, QGraphicsDropShadowEffect)

    def test_ring_has_no_shadow_effect(self, qapp) -> None:
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM")
        assert c._ring.graphicsEffect() is None


@pytest.mark.skipif(not _QT_OK, reason="PySide6 unavailable")
class TestThemeIntegration:
    def test_uses_theme_colors(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        c = StatCard(label="RAM", accent="#60CDFF")
        assert c._ring._accent.name().lower() == "#60cdff"

    def test_theme_propagation(self, qapp) -> None:
        from ram_monitor.ui.stats_cards import StatCard
        from ram_monitor.ui.fluent_theme import FluentTheme
        custom_theme = FluentTheme()
        c = StatCard(label="RAM", theme=custom_theme)
        assert c._theme is custom_theme
