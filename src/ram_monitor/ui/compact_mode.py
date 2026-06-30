"""CompactModeWindow — a small always-on-top floating monitor.

M2-5: A lightweight secondary window that shows only RAM% and CPU% with
minimal visual chrome. Designed to sit in a corner of the screen while
the user works in other apps.
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
    """A small always-on-top floating RAM/CPU monitor."""
    def __init__(self, config: Config = CONFIG, theme: Optional[FluentTheme] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._config = config
        self._theme = theme or FluentTheme.default()
        self._ram_percent: float = 0.0
        self._cpu_percent: float = 0.0
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self.setFixedSize(180, 80)
        self._settings = QSettings("RAMMonitor", "CompactMode")
        self._restore_geometry()
        self._cached_font_label = QFont(self._theme.typography.family.strip('"').split(',')[0])
        self._cached_font_label.setPointSize(9)
        self._cached_font_label.setWeight(QFont.Weight.Medium)
        self._cached_font_value = QFont(self._theme.typography.family.strip('"').split(',')[0])
        self._cached_font_value.setPointSize(16)
        self._cached_font_value.setWeight(QFont.Weight.Bold)
        self._cached_pen_text = QPen(QColor(self._theme.colors.text_primary))
        self._cached_pen_secondary = QPen(QColor(self._theme.colors.text_secondary))
        self._cached_pen_ram = QPen(QColor(self._theme.colors.ram))
        self._cached_pen_cpu = QPen(QColor(self._theme.colors.cpu))
        self._drag_offset: Optional[QPoint] = None

    def apply_metrics(self, m: SystemMetrics) -> None:
        self._ram_percent = m.memory_percent
        self._cpu_percent = m.cpu_percent
        self.update()

    def toggle(self) -> None:
        if self.isVisible(): self.hide()
        else: self.show(); self.raise_()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        from PySide6.QtGui import QPainterPath
        from PySide6.QtCore import QRectF
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), 8, 8)
        p.fillPath(path, QColor(self._theme.colors.surface))
        p.setPen(self._cached_pen_secondary); p.setFont(self._cached_font_label); p.drawText(10, 22, "RAM")
        p.setPen(self._cached_pen_ram); p.setFont(self._cached_font_value); p.drawText(10, 48, format_percent(self._ram_percent))
        p.setPen(self._cached_pen_secondary); p.setFont(self._cached_font_label); p.drawText(100, 22, "CPU")
        p.setPen(self._cached_pen_cpu); p.setFont(self._cached_font_value); p.drawText(100, 48, format_percent(self._cpu_percent))
        p.end()

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
            self._drag_offset = None; self._save_geometry(); event.accept()

    def _restore_geometry(self) -> None:
        pos = self._settings.value("pos")
        if pos is not None:
            try: self.move(pos)
            except Exception: pass
    def _save_geometry(self) -> None:
        self._settings.setValue("pos", self.pos())
    def closeEvent(self, event) -> None:
        self._save_geometry()
        super().closeEvent(event)
