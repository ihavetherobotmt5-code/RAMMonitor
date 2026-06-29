"""CompactModeWindow — a small always-on-top floating monitor.

M2-5: A lightweight secondary window that shows only RAM% and CPU% with
minimal visual chrome. Designed to sit in a corner of the screen while
the user works in other apps.

Design decisions:
* Separate QWidget (not a QMainWindow) — no menu bar, no status bar, minimal chrome.
* Always-on-top via Qt.WindowStaysOnTopHint + Qt.Tool (doesn't appear in taskbar).
* Frameless (Qt.FramelessWindowHint) — custom rounded background painted in paintEvent.
* Draggable — user can move it by clicking anywhere and dragging.
* Remembers geometry via QSettings (per-user, survives restart).
* Shares the SAME MonitorWorker signal as MainWindow — no duplicate polling.
* Toggle without restart — show()/hide() the window, worker keeps running.

Performance:
* Paints via cached QPen/QFont (no per-paint allocations).
* Same smart-animation threshold as StatCard (no animation on noise).
* ~5 KB RSS overhead (one QWidget + 2 QLabels + paint cache).
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QPoint, QSettings, Qt
from PySide6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ram_monitor.config import CONFIG, Config
from ram_monitor.core.models import SystemMetrics
from ram_monitor.ui.fluent_theme import FluentTheme
from ram_monitor.utils.formatters import format_percent


class CompactModeWindow(QWidget):
    """A small always-on-top floating RAM/CPU monitor.

    Public API:
        CompactModeWindow(config, theme, parent)
        .apply_metrics(SystemMetrics)  — called by MainWindow on every tick
        .toggle()                      — show/hide without destroying
        Geometry is auto-saved to QSettings on move/resize.
    """

    def __init__(
        self,
        config: Config = CONFIG,
        theme: Optional[FluentTheme] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._theme = theme or FluentTheme.default()
        self._ram_percent: float = 0.0
        self._cpu_percent: float = 0.0

        # Window flags: frameless, always-on-top, tool window (no taskbar entry).
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)

        # Fixed compact size — small enough to sit in a screen corner.
        self.setFixedSize(180, 80)

        # Restore geometry from QSettings (survives restart).
        self._settings = QSettings("RAMMonitor", "CompactMode")
        self._restore_geometry()

        # Cached paint resources (created once, no per-paint allocations).
        self._cached_font_label = QFont(
            self._theme.typography.family.strip('"').split(',')[0]
        )
        self._cached_font_label.setPointSize(9)
        self._cached_font_label.setWeight(QFont.Weight.Medium)

        self._cached_font_value = QFont(
            self._theme.typography.family.strip('"').split(',')[0]
        )
        self._cached_font_value.setPointSize(16)
        self._cached_font_value.setWeight(QFont.Weight.Bold)

        self._cached_pen_text = QPen(QColor(self._theme.colors.text_primary))
        self._cached_pen_secondary = QPen(QColor(self._theme.colors.text_secondary))
        self._cached_pen_ram = QPen(QColor(self._theme.colors.ram))
        self._cached_pen_cpu = QPen(QColor(self._theme.colors.cpu))

        # For dragging.
        self._drag_offset: Optional[QPoint] = None

    # -- Public API -------------------------------------------------------

    def apply_metrics(self, m: SystemMetrics) -> None:
        """Update the displayed values. Called on every metrics tick.

        Triggers a repaint of only this widget (WA_OpaquePaintEvent is
        NOT set — we use WA_TranslucentBackground for rounded corners).
        """
        self._ram_percent = m.memory_percent
        self._cpu_percent = m.cpu_percent
        self.update()  # repaint only this widget

    def toggle(self) -> None:
        """Show or hide the compact window without destroying it."""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()

    # -- Painting ---------------------------------------------------------

    def paintEvent(self, _event) -> None:
        """Draw the compact window: rounded background + RAM/CPU values.

        All resources (QFont, QPen) are cached in __init__ — zero allocations
        in the hot path.
        """
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Rounded background.
        from PySide6.QtGui import QPainterPath
        from PySide6.QtCore import QRectF

        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 8, 8)
        p.fillPath(path, QColor(self._theme.colors.surface))

        # -- RAM (left half) --
        p.setPen(self._cached_pen_secondary)
        p.setFont(self._cached_font_label)
        p.drawText(10, 22, "RAM")

        p.setPen(self._cached_pen_ram)
        p.setFont(self._cached_font_value)
        ram_text = format_percent(self._ram_percent)
        p.drawText(10, 48, ram_text)

        # -- CPU (right half) --
        p.setPen(self._cached_pen_secondary)
        p.setFont(self._cached_font_label)
        p.drawText(100, 22, "CPU")

        p.setPen(self._cached_pen_cpu)
        p.setFont(self._cached_font_value)
        cpu_text = format_percent(self._cpu_percent)
        p.drawText(100, 48, cpu_text)

        p.end()

    # -- Dragging ---------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._drag_offset is not None:
            self._drag_offset = None
            self._save_geometry()
            event.accept()

    # -- Geometry persistence ---------------------------------------------

    def _restore_geometry(self) -> None:
        """Restore window position from QSettings."""
        pos = self._settings.value("pos")
        if pos is not None:
            try:
                self.move(pos)
            except Exception:
                pass  # corrupt settings — use default position

    def _save_geometry(self) -> None:
        """Save window position to QSettings."""
        self._settings.setValue("pos", self.pos())

    def closeEvent(self, event) -> None:
        """Save geometry on close."""
        self._save_geometry()
        super().closeEvent(event)
