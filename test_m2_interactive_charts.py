"""Tests for M2-3: Interactive Charts (Crosshair + Tooltip)."""
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


@pytest.fixture(scope="session")
def qapp():
    if not _QT_OK:
        pytest.skip("PySide6 unavailable")
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


@pytest.mark.skipif(not _QT_OK, reason="PySide6 unavailable")
class TestInteractiveChart:
    def test_crosshair_exists_and_hidden(self, qapp) -> None:
        from ram_monitor.ui.charts import HistoryChart
        c = HistoryChart(color="#60CDFF")
        assert c._crosshair_v is not None
        assert not c._crosshair_v.isVisible()

    def test_tooltip_exists_and_hidden(self, qapp) -> None:
        from ram_monitor.ui.charts import HistoryChart
        c = HistoryChart(color="#60CDFF")
        assert c._tooltip is not None
        assert not c._tooltip.isVisible()

    def test_ys_cached_is_none_before_first_push(self, qapp) -> None:
        from ram_monitor.ui.charts import HistoryChart
        c = HistoryChart(color="#60CDFF")
        assert c._ys_cached is None

    def test_ys_cached_populated_after_push(self, qapp) -> None:
        from ram_monitor.ui.charts import HistoryChart
        import numpy as np
        c = HistoryChart(color="#60CDFF")
        c.push(50.0)
        assert c._ys_cached is not None
        assert isinstance(c._ys_cached, np.ndarray)
        assert len(c._ys_cached) == CONFIG.history_length

    def test_mouse_moved_no_crash_with_empty_data(self, qapp) -> None:
        from ram_monitor.ui.charts import HistoryChart
        from PySide6.QtCore import QPointF
        c = HistoryChart(color="#60CDFF")
        c._on_mouse_moved(QPointF(0, 0))
        assert not c._crosshair_v.isVisible()

    def test_mouse_moved_shows_crosshair_with_data(self, qapp) -> None:
        from ram_monitor.ui.charts import HistoryChart
        from PySide6.QtCore import QPointF
        c = HistoryChart(color="#60CDFF")
        for i in range(10):
            c.push(50.0 + i * 2)
        view_pos = QPointF(0, 50)
        scene_pos = c.plotItem.vb.mapViewToScene(view_pos)
        c._on_mouse_moved(scene_pos)
        assert c._crosshair_v.isVisible()
        assert c._tooltip.isVisible()

    def test_mouse_moved_outside_range_hides_crosshair(self, qapp) -> None:
        from ram_monitor.ui.charts import HistoryChart
        from PySide6.QtCore import QPointF
        c = HistoryChart(color="#60CDFF")
        for i in range(10):
            c.push(50.0 + i)
        view_pos = QPointF(100, 50)
        scene_pos = c.plotItem.vb.mapViewToScene(view_pos)
        c._on_mouse_moved(scene_pos)
        assert not c._crosshair_v.isVisible()

    def test_leave_event_hides_crosshair(self, qapp) -> None:
        from ram_monitor.ui.charts import HistoryChart
        from PySide6.QtCore import QEvent, QPointF
        c = HistoryChart(color="#60CDFF")
        for i in range(10):
            c.push(50.0 + i)
        view_pos = QPointF(0, 50)
        scene_pos = c.plotItem.vb.mapViewToScene(view_pos)
        c._on_mouse_moved(scene_pos)
        assert c._crosshair_v.isVisible()
        c.leaveEvent(QEvent(QEvent.Type.Leave))
        assert not c._crosshair_v.isVisible()

    def test_clear_history_hides_crosshair(self, qapp) -> None:
        from ram_monitor.ui.charts import HistoryChart
        from PySide6.QtCore import QPointF
        c = HistoryChart(color="#60CDFF")
        for i in range(10):
            c.push(50.0 + i)
        view_pos = QPointF(0, 50)
        scene_pos = c.plotItem.vb.mapViewToScene(view_pos)
        c._on_mouse_moved(scene_pos)
        c.clear_history()
        assert not c._crosshair_v.isVisible()
        assert c._ys_cached is None

    def test_tooltip_text_format(self, qapp) -> None:
        from ram_monitor.ui.charts import HistoryChart
        from PySide6.QtCore import QPointF
        c = HistoryChart(color="#60CDFF")
        for i in range(10):
            c.push(50.0 + i * 2)
        view_pos = QPointF(0, 68)
        scene_pos = c.plotItem.vb.mapViewToScene(view_pos)
        c._on_mouse_moved(scene_pos)
        text = c._tooltip.toPlainText()
        assert "now" in text
        assert "68" in text

    def test_no_cpu_polling(self, qapp) -> None:
        from ram_monitor.ui.charts import HistoryChart
        c = HistoryChart(color="#60CDFF")
        assert hasattr(c.scene(), 'sigMouseMoved')
