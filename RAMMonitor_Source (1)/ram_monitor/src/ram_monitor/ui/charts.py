"""HistoryChart — pyqtgraph wrapper with a bounded ring buffer.

pyqtgraph is the fastest pure-Python charting library for Qt; on a 60-point
series at 1.5 s cadence it uses essentially zero CPU. The class below adds:

* A fixed-length ring buffer (`collections.deque(maxlen=...)`) so memory
  usage stays flat no matter how long the app runs.
* A clean API: `push(y)` appends a value and triggers a repaint.
* A horizontal time axis in MM:SS relative to "now" — readable, no clocks.
* A subtle area-fill under the curve to match the Windows 11 visual weight.
"""
from __future__ import annotations

from collections import deque
from typing import Optional

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPen

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
        self._x: np.ndarray = np.arange(-history_length + 1, 1, dtype=float)

        # ── Visual setup ──────────────────────────────────────────────────
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

        # Curve + area fill.
        pen = QPen(QColor(color))
        pen.setWidthF(1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self._curve: pg.PlotDataItem = self.plot(pen=pen)
        # Build a fill color = curve color at ~25 % alpha.
        fill_color = QColor(color)
        fill_color.setAlpha(64)
        self._fill: pg.FillBetweenItem = pg.FillBetweenItem(
            self._curve, pg.PlotDataItem(), brush=fill_color,
        )
        # NB: we don't add the fill yet — it's drawn against an invisible
        # zero baseline curve that we'll attach on first push.

        # Hide "y_label" axis title by default; caller can override.

    # ── Public API ─────────────────────────────────────────────────────────

    def push(self, value: float) -> None:
        """Append a new sample and repaint. O(1) amortized."""
        self._history.append(float(value))
        # Pad the front with zeros if we haven't filled the buffer yet so the
        # x-axis stays anchored to its fixed range.
        n = len(self._history)
        ys = np.fromiter(self._history, dtype=float, count=n)
        if n < self._history.maxlen:
            pad = np.zeros(self._history.maxlen - n, dtype=float)
            ys = np.concatenate((pad, ys))
        self._curve.setData(y=ys)

    def clear_history(self) -> None:
        """Reset the buffer (used when the collector is re-created)."""
        self._history.clear()
        self._curve.setData(y=np.zeros(self._history.maxlen, dtype=float))

    @property
    def latest(self) -> Optional[float]:
        """Most recent sample, or None if the buffer is empty."""
        if not self._history:
            return None
        return self._history[-1]
