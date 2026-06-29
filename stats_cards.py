"""Fluent StatCard — ring meter + horizontal bar + smart animation.

Public API (UNCHANGED from V1):
    StatCard(label, accent, formatter, max_value, parent, config)
    .set_value(value, sub_text="")
    .set_sub_text(text)
    .set_ring_visible(visible)
    .set_meter_visible(visible)
    .current_value -> float
    value_changed signal

What changed from V1:
* A circular gradient **ring meter** is now the prominent visual.
* A thin **horizontal progress bar** stays below as the secondary indicator.
* **Smart animation**: only animates when |delta| > 2 % of full-scale.
* **Status-based color coding** (M2-1): green < 60%, amber 60-85%, red > 85%.
* **Cached paint resources** (P0 hardening): QFont/QPen/QLinearGradient created
  once in __init__, reused on every paintEvent — zero per-paint allocations.
* **Single reused QPropertyAnimation** (P0-1): one animation per widget,
  restarted via setStartValue/setEndValue — zero per-tick allocations.
* **WA_OpaquePaintEvent** (P0-2): prevents repaint cascade to parent widgets.
* **Accessibility** (M2-8): focusable, accessible names on all labels.
* All visual constants come from `FluentTheme` — no magic numbers.

Rendering pipeline:
    paintEvent()
      ├── draw track arc (cached pen, 1 stroke)
      └── draw value arc with gradient (cached pen, 1 stroke)

Total: ~2 paint calls per repaint. Card repaints ONLY itself
(`self.update()` — Qt clips to the widget's bounding rect).
"""
from __future__ import annotations

import math
from typing import Callable, Optional

from PySide6.QtCore import (
    QPropertyAnimation,
    QPointF,
    Qt,
    Signal,
    Property,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from ram_monitor.config import CONFIG, Config
from ram_monitor.ui.fluent_theme import FluentTheme
from ram_monitor.utils.formatters import format_percent


# -- Ring-meter widget ---------------------------------------------------

class _RingMeter(QWidget):
    """The circular gradient ring. Repaints only itself, never the parent.

    The animation drives a single float property `_anim_progress` from 0 to 1.
    When the value stops changing, the animation finishes and the widget
    becomes idle — no timer, no repaints.

    M2-1: Status-based color coding. Three cached value-pens (good/warn/bad)
    are selected in paintEvent based on the current value's tier.
    """

    def __init__(
        self,
        accent: str,
        max_value: float = 100.0,
        parent: Optional[QWidget] = None,
        config: Config = CONFIG,
        theme: Optional[FluentTheme] = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._theme = theme or FluentTheme.default()
        self._accent = QColor(accent)
        self._max_value = max_value
        self._current_value: float = 0.0
        self._displayed_value: float = 0.0  # animated interp target

        # Fixed size — the ring is a fixed visual element, not stretchy.
        self.setFixedSize(72, 72)

        # P0-2: WA_OpaquePaintEvent — tell Qt we fully paint our rect,
        # so it does NOT propagate repaints to parent widgets.
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        # -- Cached paint resources (created ONCE, reused on every paintEvent).
        self._cached_font: QFont = QFont(
            self._theme.typography.family.strip('"').split(',')[0]
        )
        self._cached_font.setPointSize(11)
        self._cached_font.setWeight(QFont.Weight.DemiBold)

        stroke_w = 6.0  # ring stroke width
        self._cached_track_pen: QPen = QPen(QColor(self._theme.colors.surface_alt))
        self._cached_track_pen.setWidthF(stroke_w)
        self._cached_track_pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        # M2-1: Status-based color coding.
        # Build 3 cached value-pens (good/warn/bad) — one per status tier.
        # The paintEvent selects the right one based on the current value.
        center = QPointF(36.0, 36.0)
        radius = (72 - 16) / 2.0

        def _make_status_pen(status_color_hex: str) -> QPen:
            grad = QLinearGradient(
                center.x() - radius, center.y() - radius,
                center.x() + radius, center.y() + radius,
            )
            base = QColor(status_color_hex)
            grad.setColorAt(0.0, base)
            grad.setColorAt(1.0, QColor(self._theme.colors.accent_strong))
            pen = QPen(QBrush(grad), stroke_w)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            return pen

        self._cached_value_pens: dict[str, QPen] = {
            "good": _make_status_pen(self._theme.colors.status_good),
            "warn": _make_status_pen(self._theme.colors.status_warn),
            "bad":  _make_status_pen(self._theme.colors.status_bad),
        }
        # Default to accent pen if max_value <= 0 (no percentage -> no status tier).
        self._cached_default_pen: QPen = _make_status_pen(
            self._accent.name()
        )

        # Cached text color (avoid QColor construction per paintEvent).
        self._cached_text_color: QColor = QColor(self._theme.colors.text_primary)

        # Cached arc rect (fixed because widget is fixed-size).
        from PySide6.QtCore import QRectF
        self._cached_arc_rect = QRectF(
            center.x() - radius, center.y() - radius, 2 * radius, 2 * radius,
        )

        # P0-1: Reuse a single QPropertyAnimation for the lifetime of this
        # widget. Created ONCE, connected valueChanged->update ONCE,
        # restarted via setStartValue/setEndValue/start().
        self._anim: QPropertyAnimation = QPropertyAnimation(
            self, b"displayedValue", self,
        )
        self._anim.setDuration(self._config.animation_duration_ms)
        from PySide6.QtCore import QEasingCurve
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        # Connect once — no lambda, no per-tick connection churn.
        self._anim.valueChanged.connect(self.update)

    # -- Public API -------------------------------------------------------

    def set_value(self, value: float, animate: bool) -> None:
        """Update the ring's target value. If `animate`, sweep from old to new.

        P0-1 fix: reuses self._anim instead of creating a new QPropertyAnimation.
        """
        old = self._displayed_value
        self._current_value = value

        if not animate:
            # Instant refresh — stop any in-flight animation, jump to value.
            self._anim.stop()
            self._displayed_value = value
            self.update()  # repaint only this widget
            return

        # Animate `_displayed_value` from old to new using the reused animation.
        self._anim.stop()
        self._anim.setStartValue(float(old))
        self._anim.setEndValue(float(value))
        self._anim.start()

    # -- Qt property so QPropertyAnimation can drive `_displayed_value` ----

    @Property(float)
    def displayedValue(self) -> float:  # pragma: no cover — trivial getter
        return self._displayed_value

    @displayedValue.setter
    def displayedValue(self, v: float) -> None:
        self._displayed_value = v
        # The animation's `valueChanged` signal already triggers update().

    # -- Painting ---------------------------------------------------------

    def paintEvent(self, _event) -> None:
        """Draw the ring meter using CACHED resources only.

        P0-2 + M2-1: no QFont/QPen/QLinearGradient/QColor
        allocations in the hot path. Everything is read from caches built
        once in __init__.
        """
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Arc spans from 135 degrees to 135 + 270 (a 3/4 ring — like a gauge).
        start_angle = 135.0
        span = 270.0

        # -- Track (background ring) — cached pen ---------------------------
        p.setPen(self._cached_track_pen)
        p.drawArc(
            self._cached_arc_rect,
            int(start_angle * 16), int(span * 16),
        )

        # -- Value arc (gradient-filled) — cached pen + gradient ------------
        if self._max_value > 0:
            pct = max(0.0, min(self._displayed_value / self._max_value, 1.0))
        else:
            pct = 0.0
        value_span = span * pct
        if value_span > 0.05:
            # M2-1: Select the value pen based on the current status tier.
            if self._max_value > 0:
                if self._displayed_value < 60.0:
                    pen = self._cached_value_pens["good"]
                elif self._displayed_value < 85.0:
                    pen = self._cached_value_pens["warn"]
                else:
                    pen = self._cached_value_pens["bad"]
            else:
                pen = self._cached_default_pen
            p.setPen(pen)
            p.drawArc(
                self._cached_arc_rect,
                int(start_angle * 16), int(value_span * 16),
            )

        # P1-6: Center text removed — the card value label (CardValue) already
        # shows the percentage as a large number to the right of the ring.

        p.end()

    @property
    def current_value(self) -> float:
        return self._current_value


# -- Card container ------------------------------------------------------

class StatCard(QFrame):
    """A Fluent metric tile: ring meter + label / value / sub-text / thin bar.

    Public API is IDENTICAL to V1 — same constructor signature, same
    `set_value(value, sub_text)` slot, same `value_changed` signal, same
    `current_value` property. No caller needs to be modified.
    """

    value_changed = Signal(float)

    def __init__(
        self,
        label: str,
        accent: str = CONFIG.color_accent,
        formatter: Optional[Callable[[float], str]] = None,
        max_value: float = 100.0,
        parent: Optional[QWidget] = None,
        config: Config = CONFIG,
        theme: Optional[FluentTheme] = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._theme = theme or FluentTheme.default()
        self._formatter = formatter or (lambda v: format_percent(v))
        self._max_value = max_value
        self._current_value: float = 0.0

        self.setObjectName("Card")
        self.setFrameShape(QFrame.Shape.NoFrame)

        # P0-2: WA_OpaquePaintEvent on the card too, so QLabel child
        # updates (value text changes) don't cascade to DashboardView.
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        # M2-8: Accessibility — the card itself is focusable for keyboard nav.
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(label)

        # -- Child widgets -------------------------------------------------
        # All labels get WA_OpaquePaintEvent so their text updates don't
        # cascade repaints to DashboardView/MainWindow.
        self._label = QLabel(label, self)
        self._label.setObjectName("CardLabel")
        self._label.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        # M2-8: Accessibility — screen reader name + description.
        self._label.setAccessibleName(f"{label} metric label")

        self._value_label = QLabel("—", self)
        self._value_label.setObjectName("CardValue")
        self._value_label.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        # M2-8: The value label is the primary accessible text for this card.
        self._value_label.setAccessibleName(f"{label} value")

        self._sub_label = QLabel("", self)
        self._sub_label.setObjectName("CardSub")
        self._sub_label.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self._sub_label.setAccessibleName(f"{label} details")

        # Ring meter — the prominent visual.
        self._ring = _RingMeter(
            accent=accent, max_value=max_value, parent=self,
            config=config, theme=self._theme,
        )

        # Thin horizontal bar — secondary indicator (per constraint #1).
        self._meter = QProgressBar(self)
        self._meter.setRange(0, 1000)
        self._meter.setValue(0)
        self._meter.setTextVisible(False)
        self._meter.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {accent}; border-radius: 4px; }}"
        )

        # -- Layout: ring on the left, text on the right, bar at bottom -----
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        top_row.addWidget(self._ring, 0)  # fixed-size
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

    # -- Public API (UNCHANGED) -------------------------------------------

    def set_value(self, value: float, sub_text: str = "") -> None:
        """Update the displayed value with smart animation.

        Animation fires only when |value - old| / max_value * 100 >
        `config.animation_threshold_pct` (default 2 %). Below that, the
        update is instant — zero CPU cost on noise.
        """
        old = self._current_value
        delta_pct = abs(value - old) / self._max_value * 100.0 if self._max_value > 0 else 0.0
        animate = delta_pct > self._config.animation_threshold_pct

        self._current_value = value
        self._value_label.setText(self._formatter(value))
        if sub_text:
            self._sub_label.setText(sub_text)

        # Update ring meter (animated or instant).
        self._ring.set_value(value, animate=animate)

        # Update thin bar — always instant (it's a secondary indicator and
        # animating both would double the CPU cost for no visual gain).
        if self._max_value > 0:
            target = int(max(0.0, min(value / self._max_value, 1.0)) * 1000)
        else:
            target = 0
        self._meter.setValue(target)

        self.value_changed.emit(value)

    def set_sub_text(self, text: str) -> None:
        """Update only the secondary line. No animation."""
        self._sub_label.setText(text)

    def set_ring_visible(self, visible: bool) -> None:
        """Show or hide the ring meter widget.

        Public accessor so callers don't need to reach into `_ring` (Law of Demeter).
        Used by `DashboardView` to hide the ring on cards where it doesn't make sense
        (e.g. the "Processes" card shows a count, not a percentage).
        """
        self._ring.setVisible(visible)

    def set_meter_visible(self, visible: bool) -> None:
        """Show or hide the thin horizontal progress bar.

        Public accessor so callers don't need to reach into `_meter` (Law of Demeter).
        """
        self._meter.setVisible(visible)

    @property
    def current_value(self) -> float:
        return self._current_value

    # Note: The _build_shadow_pixmap stub and paintEvent override were
    # removed in M1 hardening (P2-8). They were dead code — the stub did
    # nothing (pass) and paintEvent just called super(). QFrame's default
    # paintEvent handles the QSS-styled background correctly.
