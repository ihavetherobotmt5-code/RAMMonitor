"""Fluent StatCard — ring meter + horizontal bar + smart animation.

M2-1: Status-based color coding (green/amber/red).
P0-1: Single reused QPropertyAnimation.
P0-2: WA_OpaquePaintEvent prevents repaint cascade.
M2-8: Accessibility — focusable, accessible names.
"""
from __future__ import annotations
from typing import Callable, Optional
from PySide6.QtCore import QPropertyAnimation, QPointF, Qt, Signal, Property
from PySide6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget
from ram_monitor.config import CONFIG, Config
from ram_monitor.ui.fluent_theme import FluentTheme
from ram_monitor.utils.formatters import format_percent

class _RingMeter(QWidget):
    """The circular gradient ring. Repaints only itself, never the parent."""
    def __init__(self, accent: str, max_value: float = 100.0, parent: Optional[QWidget] = None, config: Config = CONFIG, theme: Optional[FluentTheme] = None) -> None:
        super().__init__(parent)
        self._config = config
        self._theme = theme or FluentTheme.default()
        self._accent = QColor(accent)
        self._max_value = max_value
        self._current_value: float = 0.0
        self._displayed_value: float = 0.0
        self.setFixedSize(72, 72)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self._cached_font = QFont(self._theme.typography.family.strip('"').split(',')[0])
        self._cached_font.setPointSize(11)
        self._cached_font.setWeight(QFont.Weight.DemiBold)
        stroke_w = 6.0
        self._cached_track_pen = QPen(QColor(self._theme.colors.surface_alt))
        self._cached_track_pen.setWidthF(stroke_w)
        self._cached_track_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        center = QPointF(36.0, 36.0)
        radius = (72 - 16) / 2.0
        def _make_status_pen(status_color_hex: str) -> QPen:
            grad = QLinearGradient(center.x() - radius, center.y() - radius, center.x() + radius, center.y() + radius)
            base = QColor(status_color_hex)
            grad.setColorAt(0.0, base)
            grad.setColorAt(1.0, QColor(self._theme.colors.accent_strong))
            pen = QPen(QBrush(grad), stroke_w)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            return pen
        self._cached_value_pens = {
            "good": _make_status_pen(self._theme.colors.status_good),
            "warn": _make_status_pen(self._theme.colors.status_warn),
            "bad": _make_status_pen(self._theme.colors.status_bad),
        }
        self._cached_default_pen = _make_status_pen(self._accent.name())
        self._cached_text_color = QColor(self._theme.colors.text_primary)
        from PySide6.QtCore import QRectF
        self._cached_arc_rect = QRectF(center.x() - radius, center.y() - radius, 2 * radius, 2 * radius)
        self._anim = QPropertyAnimation(self, b"displayedValue", self)
        self._anim.setDuration(self._config.animation_duration_ms)
        from PySide6.QtCore import QEasingCurve
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self.update)

    def set_value(self, value: float, animate: bool) -> None:
        old = self._displayed_value
        self._current_value = value
        if not animate:
            self._anim.stop()
            self._displayed_value = value
            self.update()
            return
        self._anim.stop()
        self._anim.setStartValue(float(old))
        self._anim.setEndValue(float(value))
        self._anim.start()

    @Property(float)
    def displayedValue(self) -> float:
        return self._displayed_value
    @displayedValue.setter
    def displayedValue(self, v: float) -> None:
        self._displayed_value = v

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        start_angle = 135.0
        span = 270.0
        p.setPen(self._cached_track_pen)
        p.drawArc(self._cached_arc_rect, int(start_angle * 16), int(span * 16))
        if self._max_value > 0:
            pct = max(0.0, min(self._displayed_value / self._max_value, 1.0))
        else:
            pct = 0.0
        value_span = span * pct
        if value_span > 0.05:
            if self._max_value > 0:
                if self._displayed_value < 60.0: pen = self._cached_value_pens["good"]
                elif self._displayed_value < 85.0: pen = self._cached_value_pens["warn"]
                else: pen = self._cached_value_pens["bad"]
            else:
                pen = self._cached_default_pen
            p.setPen(pen)
            p.drawArc(self._cached_arc_rect, int(start_angle * 16), int(value_span * 16))
        p.end()

    @property
    def current_value(self) -> float:
        return self._current_value

class StatCard(QFrame):
    """A Fluent metric tile: ring meter + label / value / sub-text / thin bar."""
    value_changed = Signal(float)

    def __init__(self, label: str, accent: str = CONFIG.color_accent, formatter: Optional[Callable[[float], str]] = None, max_value: float = 100.0, parent: Optional[QWidget] = None, config: Config = CONFIG, theme: Optional[FluentTheme] = None) -> None:
        super().__init__(parent)
        self._config = config
        self._theme = theme or FluentTheme.default()
        self._formatter = formatter or (lambda v: format_percent(v))
        self._max_value = max_value
        self._current_value: float = 0.0
        self.setObjectName("Card")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(label)
        self._label = QLabel(label, self)
        self._label.setObjectName("CardLabel")
        self._label.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self._label.setAccessibleName(f"{label} metric label")
        self._value_label = QLabel("\u2014", self)
        self._value_label.setObjectName("CardValue")
        self._value_label.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self._value_label.setAccessibleName(f"{label} value")
        self._sub_label = QLabel("", self)
        self._sub_label.setObjectName("CardSub")
        self._sub_label.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self._sub_label.setAccessibleName(f"{label} details")
        self._ring = _RingMeter(accent=accent, max_value=max_value, parent=self, config=config, theme=self._theme)
        self._meter = QProgressBar(self)
        self._meter.setRange(0, 1000)
        self._meter.setValue(0)
        self._meter.setTextVisible(False)
        self._meter.setStyleSheet(f"QProgressBar::chunk {{ background-color: {accent}; border-radius: 4px; }}")
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(4)
        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        top_row.addWidget(self._ring, 0)
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.addWidget(self._label)
        text_col.addWidget(self._value_label)
        text_col.addWidget(self._sub_label)
        text_col.addStretch(1)
        top_row.addLayout(text_col, 1)
        root.addLayout(top_row)
        root.addSpacing(6)
        root.addWidget(self._meter)
        self.setLayout(root)

    def set_value(self, value: float, sub_text: str = "") -> None:
        old = self._current_value
        delta_pct = abs(value - old) / self._max_value * 100.0 if self._max_value > 0 else 0.0
        animate = delta_pct > self._config.animation_threshold_pct
        self._current_value = value
        self._value_label.setText(self._formatter(value))
        if sub_text: self._sub_label.setText(sub_text)
        self._ring.set_value(value, animate=animate)
        if self._max_value > 0:
            target = int(max(0.0, min(value / self._max_value, 1.0)) * 1000)
        else:
            target = 0
        self._meter.setValue(target)
        self.value_changed.emit(value)

    def set_sub_text(self, text: str) -> None:
        self._sub_label.setText(text)

    def set_ring_visible(self, visible: bool) -> None:
        self._ring.setVisible(visible)

    def set_meter_visible(self, visible: bool) -> None:
        self._meter.setVisible(visible)

    @property
    def current_value(self) -> float:
        return self._current_value
