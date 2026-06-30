"""HistoryChart — pyqtgraph wrapper with a bounded ring buffer.

* Anti-aliased rendering for smooth lines at any DPI.
* A gradient area-fill under the curve (accent color -> transparent).
* Skip-if-unchanged optimization to avoid repaints at idle.
* M2-3: Interactive crosshair + tooltip — hover to inspect any historical
  value. Event-driven (no polling), zero allocations per mouse event.
"""
from __future__ import annotations

from collections import deque
from typing import Optional

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPen

from ram_monitor.config import CONFIG, Config


class HistoryChart(pg.PlotWidget):
    """A scrolling line chart with a bounded history buffer."""

    def __init__(
        self,
        color: str = CONFIG.color_accent,
        y_max: float = 100.0,
        y_label: str = "%",
        history_length: int = CONFIG.history_length,
        parent=None,
        config: Config = CONFIG,
    ) -> None:
        super().__init__(parent=parent, background=None)
        self._config = config
        self._y_max = y_max
        self._history: deque[float] = deque(maxlen=history_length)
        self._history_length = history_length
        self._x: np.ndarray = np.arange(-history_length + 1, 1, dtype=float)
        self._ys_cached: Optional[np.ndarray] = None

        self.setMouseEnabled(x=False, y=False)
        self.setMenuEnabled(False)
        self.hideButtons()
        self.showGrid(x=False, y=True, alpha=0.08)
        self.setYRange(0, y_max, padding=0.02)
        self.setXRange(-history_length + 1, 0, padding=0.0)

        for axis in ("left", "bottom"):
            ax = self.getAxis(axis)
            ax.setPen(QColor(0, 0, 0, 0))
            ax.setTextPen(QColor(config.color_text_secondary))
        self.getAxis("bottom").setStyle(showValues=False)

        self.setAntialiasing(True)

        pen = QPen(QColor(color))
        pen.setWidthF(1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self._curve: pg.PlotDataItem = self.plot(pen=pen)

        base_color = QColor(color)
        top_color = QColor(base_color)
        top_color.setAlpha(100)
        bottom_color = QColor(base_color)
        bottom_color.setAlpha(0)

        self._fill_gradient: QLinearGradient = QLinearGradient(0, 0, 0, 1)
        self._fill_gradient.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectBoundingMode)
        self._fill_gradient.setColorAt(0.0, top_color)
        self._fill_gradient.setColorAt(1.0, bottom_color)

        self._curve.setFillLevel(0)
        self._curve.setFillBrush(QBrush(self._fill_gradient))

        crosshair_pen = QPen(QColor(255, 255, 255, 160))
        crosshair_pen.setWidthF(1.0)
        crosshair_pen.setStyle(Qt.PenStyle.DashLine)
        self._crosshair_v: pg.InfiniteLine = pg.InfiniteLine(
            angle=90, pen=crosshair_pen, movable=False,
        )
        self._crosshair_v.setVisible(False)
        self.addItem(self._crosshair_v)

        tooltip_color = QColor(config.color_text_primary)
        tooltip_fill = QColor(config.color_surface)
        tooltip_fill.setAlpha(220)
        self._tooltip: pg.TextItem = pg.TextItem(
            text="", color=tooltip_color, fill=tooltip_fill,
            anchor=(0.0, 1.0),
        )
        self._tooltip.setZValue(100)
        self._tooltip.setVisible(False)
        self.addItem(self._tooltip)

        self.scene().sigMouseMoved.connect(self._on_mouse_moved)

    def push(self, value: float) -> None:
        if self._history and self._history[-1] == value:
            return
        self._history.append(float(value))
        n = len(self._history)
        ys = np.fromiter(self._history, dtype=float, count=n)
        if n < self._history.maxlen:
            pad = np.zeros(self._history.maxlen - n, dtype=float)
            ys = np.concatenate((pad, ys))
        self._ys_cached = ys
        self._curve.setData(y=ys)

    def clear_history(self) -> None:
        self._history.clear()
        self._ys_cached = None
        self._curve.setData(y=np.zeros(self._history.maxlen, dtype=float))
        self._crosshair_v.setVisible(False)
        self._tooltip.setVisible(False)

    @property
    def latest(self) -> Optional[float]:
        if not self._history:
            return None
        return self._history[-1]

    def _on_mouse_moved(self, scene_pos) -> None:
        if self._ys_cached is None or len(self._ys_cached) == 0:
            return
        view_pos = self.plotItem.vb.mapSceneToView(scene_pos)
        x = view_pos.x()
        x_min = -self._history_length + 1
        x_max = 0
        if x < x_min or x > x_max:
            self._crosshair_v.setVisible(False)
            self._tooltip.setVisible(False)
            return
        sample_idx = int(round(x))
        sample_idx = max(x_min, min(x_max, sample_idx))
        array_idx = sample_idx + (self._history_length - 1)
        if array_idx < 0 or array_idx >= len(self._ys_cached):
            return
        value = float(self._ys_cached[array_idx])
        self._crosshair_v.setPos(sample_idx)
        self._crosshair_v.setVisible(True)
        if sample_idx == 0:
            time_str = "now"
        else:
            seconds_ago = int(-sample_idx * self._config.poll_interval_seconds)
            time_str = f"\u2212{seconds_ago}s"
        self._tooltip.setText(f"{time_str}:  {value:.1f}%")
        self._tooltip.setPos(sample_idx, value)
        self._tooltip.setVisible(True)

    def leaveEvent(self, event) -> None:
        self._crosshair_v.setVisible(False)
        self._tooltip.setVisible(False)
        super().leaveEvent(event)
