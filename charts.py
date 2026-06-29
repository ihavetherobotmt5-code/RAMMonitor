"""HistoryChart — pyqtgraph wrapper with a bounded ring buffer.

pyqtgraph is the fastest pure-Python charting library for Qt; on a 60-point
series at 1.5 s cadence it uses essentially zero CPU. The class below adds:

* A fixed-length ring buffer (`collections.deque(maxlen=...)`) so memory
  usage stays flat no matter how long the app runs.
* A clean API: `push(y)` appends a value and triggers a repaint.
* Anti-aliased rendering for smooth lines at any DPI.
* A gradient area-fill under the curve (accent color -> transparent) so
  trends are instantly visible as a colored "shape" rather than just a line.
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
        # M2-3: Cached padded ys array — updated by push(), read by the
        # mouse handler. This gives O(1) value lookup with ZERO allocations
        # during mouse motion.
        self._ys_cached: Optional[np.ndarray] = None

        # -- Visual setup -------------------------------------------------
        self.setMouseEnabled(x=False, y=False)
        self.setMenuEnabled(False)
        self.hideButtons()
        self.showGrid(x=False, y=True, alpha=0.08)
        self.setYRange(0, y_max, padding=0.02)
        self.setXRange(-history_length + 1, 0, padding=0.0)

        # Strip every default decoration — we want a pure data line.
        for axis in ("left", "bottom"):
            ax = self.getAxis(axis)
            ax.setPen(QColor(0, 0, 0, 0))
            ax.setTextPen(QColor(config.color_text_secondary))
        self.getAxis("bottom").setStyle(showValues=False)

        # -- M2 3.2: Curve with anti-aliasing + gradient fill ------------
        self.setAntialiasing(True)

        pen = QPen(QColor(color))
        pen.setWidthF(1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self._curve: pg.PlotDataItem = self.plot(pen=pen)

        # Gradient fill under the curve.
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

        # -- M2-3: Interactive crosshair + tooltip -----------------------
        # All resources created ONCE in __init__ — zero allocations in the
        # mouse move handler.
        crosshair_pen = QPen(QColor(255, 255, 255, 160))  # semi-transparent white
        crosshair_pen.setWidthF(1.0)
        crosshair_pen.setStyle(Qt.PenStyle.DashLine)
        self._crosshair_v: pg.InfiniteLine = pg.InfiniteLine(
            angle=90, pen=crosshair_pen, movable=False,
        )
        self._crosshair_v.setVisible(False)
        self.addItem(self._crosshair_v)

        # Tooltip: semi-transparent dark background, white text.
        tooltip_color = QColor(config.color_text_primary)
        tooltip_fill = QColor(config.color_surface)
        tooltip_fill.setAlpha(220)
        self._tooltip: pg.TextItem = pg.TextItem(
            text="", color=tooltip_color, fill=tooltip_fill,
            anchor=(0.0, 1.0),  # anchor bottom-left of text to the data point
        )
        self._tooltip.setZValue(100)  # render above the curve
        self._tooltip.setVisible(False)
        self.addItem(self._tooltip)

        # Event-driven mouse tracking — NO QTimer polling.
        # sigMouseMoved fires only when the mouse actually moves.
        self.scene().sigMouseMoved.connect(self._on_mouse_moved)

    # -- Public API -------------------------------------------------------

    def push(self, value: float) -> None:
        """Append a new sample and repaint. O(1) amortized.

        Also caches the padded ys array for O(1) lookup by the crosshair
        mouse handler — zero allocations during mouse motion.
        """
        if self._history and self._history[-1] == value:
            return
        self._history.append(float(value))
        n = len(self._history)
        ys = np.fromiter(self._history, dtype=float, count=n)
        if n < self._history.maxlen:
            pad = np.zeros(self._history.maxlen - n, dtype=float)
            ys = np.concatenate((pad, ys))
        self._ys_cached = ys  # cache for the mouse handler
        self._curve.setData(y=ys)

    def clear_history(self) -> None:
        """Reset the buffer (used when the collector is re-created)."""
        self._history.clear()
        self._ys_cached = None
        self._curve.setData(y=np.zeros(self._history.maxlen, dtype=float))
        # Hide crosshair + tooltip — no data to show.
        self._crosshair_v.setVisible(False)
        self._tooltip.setVisible(False)

    @property
    def latest(self) -> Optional[float]:
        """Most recent sample, or None if the buffer is empty."""
        if not self._history:
            return None
        return self._history[-1]

    # -- M2-3: Interactive crosshair + tooltip -----------------------------

    def _on_mouse_moved(self, scene_pos) -> None:
        """Handle mouse movement — show crosshair + tooltip at the nearest sample.

        Event-driven (called by sigMouseMoved). ZERO allocations:
        - No new objects created
        - No list/deque copies
        - Value looked up from self._ys_cached (O(1) numpy indexing)
        - Text set via setText (reuses existing TextItem)
        """
        if self._ys_cached is None or len(self._ys_cached) == 0:
            return

        # Convert scene coordinates to plot view coordinates.
        view_pos = self.plotItem.vb.mapSceneToView(scene_pos)
        x = view_pos.x()

        # Clamp x to the valid data range [-history_length+1, 0].
        x_min = -self._history_length + 1
        x_max = 0
        if x < x_min or x > x_max:
            # Mouse is outside the data range — hide crosshair + tooltip.
            self._crosshair_v.setVisible(False)
            self._tooltip.setVisible(False)
            return

        # Find the nearest sample index (round to integer x).
        sample_idx = int(round(x))
        sample_idx = max(x_min, min(x_max, sample_idx))

        # Map sample_idx to the cached ys array index.
        # x=0 is newest (rightmost) -> index = history_length - 1
        # x=-59 is oldest (leftmost) -> index = 0
        array_idx = sample_idx + (self._history_length - 1)
        if array_idx < 0 or array_idx >= len(self._ys_cached):
            return

        value = float(self._ys_cached[array_idx])

        # Show crosshair at the sample's x position.
        self._crosshair_v.setPos(sample_idx)
        self._crosshair_v.setVisible(True)

        # Build tooltip text: "-45s: 62.4%" or "now: 62.4%"
        if sample_idx == 0:
            time_str = "now"
        else:
            seconds_ago = int(-sample_idx * self._config.poll_interval_seconds)
            time_str = f"\u2212{seconds_ago}s"
        self._tooltip.setText(f"{time_str}:  {value:.1f}%")
        self._tooltip.setPos(sample_idx, value)
        self._tooltip.setVisible(True)

    def leaveEvent(self, event) -> None:
        """Hide crosshair + tooltip when the mouse leaves the chart."""
        self._crosshair_v.setVisible(False)
        self._tooltip.setVisible(False)
        super().leaveEvent(event)
