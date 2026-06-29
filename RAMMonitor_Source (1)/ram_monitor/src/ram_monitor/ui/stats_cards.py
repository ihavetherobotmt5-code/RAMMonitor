"""StatCard — a single metric tile (label, big value, sub-line, thin meter).

Each card is a self-contained `QFrame` with a public `set_value()` slot.
The dashboard composes 4 of these (RAM %, RAM used, CPU %, processes/uptime)
into a horizontal strip.

The "smooth animation" requirement is implemented as a QPropertyAnimation
on the progress bar's `value` property — interpolating from old to new over
`Config.animation_duration_ms`. This is the only animation in the app,
which keeps the GPU/CPU cost essentially zero.
"""
from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import (
    QPropertyAnimation,
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from ram_monitor.config import CONFIG, Config
from ram_monitor.utils.formatters import format_percent


class StatCard(QFrame):
    """A metric tile: label / value / sub-text / thin progress meter.

    Args:
        label:   Short heading, e.g. "RAM".
        accent:  Hex color for the progress meter chunk.
        formatter: Callable[[float], str] applied to the numeric value
                   before display. Default: format as percent.
        max_value: Upper bound for the meter (so 0..100 → full width).
        parent:   Optional Qt parent.
    """

    #: Emitted when the displayed value changes — used by tests / introspection.
    value_changed = Signal(float)

    def __init__(
        self,
        label: str,
        accent: str = CONFIG.color_accent,
        formatter: Optional[Callable[[float], str]] = None,
        max_value: float = 100.0,
        parent: Optional[QWidget] = None,
        config: Config = CONFIG,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._formatter = formatter or (lambda v: format_percent(v))
        self._max_value = max_value
        self._current_value: float = 0.0

        self.setObjectName("Card")
        self.setFrameShape(QFrame.Shape.NoFrame)

        # ── Build child widgets ────────────────────────────────────────────
        self._label = QLabel(label, self)
        self._label.setObjectName("CardLabel")

        self._value_label = QLabel("—", self)
        self._value_label.setObjectName("CardValue")

        self._sub_label = QLabel("", self)
        self._sub_label.setObjectName("CardSub")

        self._meter = QProgressBar(self)
        self._meter.setRange(0, 1000)  # 0.1 % granularity
        self._meter.setValue(0)
        self._meter.setTextVisible(False)
        # Tint the chunk with the card's accent color.
        self._meter.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {accent}; border-radius: 3px; }}"
        )

        # ── Layout ────────────────────────────────────────────────────────
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)
        layout.addWidget(self._label)
        layout.addWidget(self._value_label)
        layout.addWidget(self._sub_label)
        layout.addSpacing(6)
        layout.addWidget(self._meter)
        layout.addStretch(1)
        self.setLayout(layout)

        # ── Animation ─────────────────────────────────────────────────────
        self._meter_anim: Optional[QPropertyAnimation] = None

    # ── Public API ─────────────────────────────────────────────────────────

    def set_value(self, value: float, sub_text: str = "") -> None:
        """Update the displayed value with a smooth meter transition."""
        self._current_value = value
        self._value_label.setText(self._formatter(value))
        if sub_text:
            self._sub_label.setText(sub_text)

        # Map value → 0..1000 meter range.
        if self._max_value > 0:
            target = int(max(0.0, min(value / self._max_value, 1.0)) * 1000)
        else:
            target = 0

        # Cancel any in-flight animation, start a new one. This is cheap
        # because QPropertyAnimation is lightweight and we only run one.
        if self._meter_anim is not None:
            self._meter_anim.stop()
        anim = QPropertyAnimation(self._meter, b"value", self)
        anim.setDuration(self._config.animation_duration_ms)
        anim.setStartValue(self._meter.value())
        anim.setEndValue(target)
        anim.start()
        # Keep a reference so the animation isn't GC'd mid-flight.
        self._meter_anim = anim

        self.value_changed.emit(value)

    def set_sub_text(self, text: str) -> None:
        """Update only the secondary line. No animation."""
        self._sub_label.setText(text)

    @property
    def current_value(self) -> float:
        return self._current_value
