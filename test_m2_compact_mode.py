"""Tests for M2-5: Compact Mode."""
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

from ram_monitor.config import CONFIG
from ram_monitor.core.models import ProcessInfo, SystemMetrics


@pytest.fixture(scope="session")
def qapp():
    if not _QT_OK:
        pytest.skip("PySide6 unavailable")
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


@pytest.mark.skipif(not _QT_OK, reason="PySide6 unavailable")
class TestCompactMode:
    def test_compact_window_exists(self, qapp) -> None:
        from PySide6.QtCore import Qt
        from ram_monitor.ui.compact_mode import CompactModeWindow
        w = CompactModeWindow()
        assert w is not None
        assert w.windowFlags() & Qt.WindowType.WindowStaysOnTopHint

    def test_compact_window_fixed_size(self, qapp) -> None:
        from ram_monitor.ui.compact_mode import CompactModeWindow
        w = CompactModeWindow()
        assert w.width() == 180
        assert w.height() == 80

    def test_apply_metrics_updates_values(self, qapp) -> None:
        from ram_monitor.ui.compact_mode import CompactModeWindow
        w = CompactModeWindow()
        m = SystemMetrics(
            total_bytes=8_000_000_000, available_bytes=4_000_000_000,
            used_bytes=4_000_000_000, memory_percent=55.0,
            cpu_percent=22.5, cpu_freq_mhz=3400.0,
            process_count=142, uptime_seconds=3661,
            top_processes=(),
        )
        w.apply_metrics(m)
        assert w._ram_percent == 55.0
        assert w._cpu_percent == 22.5

    def test_toggle_shows_and_hides(self, qapp) -> None:
        from ram_monitor.ui.compact_mode import CompactModeWindow
        w = CompactModeWindow()
        assert not w.isVisible()
        w.toggle()
        assert w.isVisible()
        w.toggle()
        assert not w.isVisible()

    def test_main_window_has_compact_mode(self, qapp) -> None:
        from ram_monitor.ui.main_window import MainWindow
        mw = MainWindow(config=CONFIG)
        assert hasattr(mw, 'toggle_compact_mode')
        assert hasattr(mw, 'compact_window')
        assert mw.compact_window is not None

    def test_no_duplicate_polling(self, qapp) -> None:
        from ram_monitor.ui.main_window import MainWindow
        mw = MainWindow(config=CONFIG)
        assert mw.worker is not None
        assert not hasattr(mw.compact_window, '_worker')

    def test_cached_paint_resources(self, qapp) -> None:
        from ram_monitor.ui.compact_mode import CompactModeWindow
        w = CompactModeWindow()
        assert w._cached_font_label is not None
        assert w._cached_font_value is not None
        assert w._cached_pen_ram is not None
        assert w._cached_pen_cpu is not None
        assert w._cached_pen_text is not None
