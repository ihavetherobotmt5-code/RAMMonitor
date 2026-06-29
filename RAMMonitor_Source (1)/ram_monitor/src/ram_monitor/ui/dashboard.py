"""DashboardView — composes the cards, charts, and process panel.

Layout (top-to-bottom):
    ┌──────────────────────────────────────────────────────────┐
    │  [RAM %] [RAM used] [CPU %] [Processes / Uptime]        │  ← 4 stat cards
    ├──────────────────────────────────────────────────────────┤
    │  RAM history chart    │  CPU history chart               │  ← 2 charts
    ├──────────────────────────────────────────────────────────┤
    │  Top processes table                                    │  ← process panel
    └──────────────────────────────────────────────────────────┘

The dashboard is a "dumb view": it has no internal state, no signals. It
exposes `apply_metrics(SystemMetrics)` and the parent window calls it on
every `MonitorWorker.metrics_ready` signal.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ram_monitor.config import CONFIG, Config
from ram_monitor.core.models import SystemMetrics
from ram_monitor.ui.charts import HistoryChart
from ram_monitor.ui.process_panel import TopProcessesPanel
from ram_monitor.ui.stats_cards import StatCard
from ram_monitor.utils.formatters import (
    format_bytes,
    format_frequency,
    format_percent,
    format_uptime,
)


class DashboardView(QWidget):
    """The single page shown inside `MainWindow`."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        config: Config = CONFIG,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._build_ui()

    # ── Public API ─────────────────────────────────────────────────────────

    def apply_metrics(self, m: SystemMetrics) -> None:
        """Push one snapshot into every child widget. Idempotent & O(rows)."""
        # ── Cards ──────────────────────────────────────────────────────────
        self._card_ram_pct.set_value(
            m.memory_percent,
            sub_text=f"{format_bytes(m.used_bytes, binary=False)} used",
        )
        self._card_ram_used.set_value(
            float(m.used_bytes),
            sub_text=f"{format_bytes(m.available_bytes, binary=False)} available",
        )
        self._card_cpu_pct.set_value(
            m.cpu_percent,
            sub_text=format_frequency(m.cpu_freq_mhz),
        )
        self._card_proc.set_value(
            float(m.process_count),
            sub_text=f"up {format_uptime(m.uptime_seconds)}",
        )

        # ── Charts ────────────────────────────────────────────────────────
        self._chart_ram.push(m.memory_percent)
        self._chart_cpu.push(m.cpu_percent)

        # ── Process panel ─────────────────────────────────────────────────
        self._processes.update_processes(m.top_processes)

    # ── UI construction ───────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # ── Cards row ─────────────────────────────────────────────────────
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        self._card_ram_pct = StatCard(
            label="RAM", accent=self._config.color_ram,
            formatter=lambda v: format_percent(v),
        )
        self._card_ram_used = StatCard(
            label="RAM Used", accent=self._config.color_ram,
            formatter=lambda v: format_bytes(int(v), binary=False),
            max_value=1.0,  # meter is suppressed — see below
        )
        # We don't want a meter on the "used" card; hide it.
        self._card_ram_used._meter.setVisible(False)
        self._card_cpu_pct = StatCard(
            label="CPU", accent=self._config.color_cpu,
            formatter=lambda v: format_percent(v),
        )
        self._card_proc = StatCard(
            label="Processes", accent=self._config.color_accent,
            formatter=lambda v: f"{int(v)}",
            max_value=1.0,
        )
        self._card_proc._meter.setVisible(False)

        for card in (
            self._card_ram_pct, self._card_ram_used,
            self._card_cpu_pct, self._card_proc,
        ):
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            card.setMinimumHeight(110)
            cards_row.addWidget(card)
        root.addLayout(cards_row)

        # ── Charts row ────────────────────────────────────────────────────
        charts_row = QHBoxLayout()
        charts_row.setSpacing(12)

        self._chart_ram = HistoryChart(
            color=self._config.color_ram,
            y_max=100.0,
            y_label="%",
            parent=self,
        )
        self._chart_cpu = HistoryChart(
            color=self._config.color_cpu,
            y_max=100.0,
            y_label="%",
            parent=self,
        )
        self._chart_ram.setMinimumHeight(180)
        self._chart_cpu.setMinimumHeight(180)
        charts_row.addWidget(self._wrap_chart("RAM History", self._chart_ram))
        charts_row.addWidget(self._wrap_chart("CPU History", self._chart_cpu))
        root.addLayout(charts_row, stretch=1)

        # ── Process panel ─────────────────────────────────────────────────
        self._processes = TopProcessesPanel(self, config=self._config)
        self._processes.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred,
        )
        root.addWidget(self._processes, stretch=1)

    def _wrap_chart(self, title: str, chart: HistoryChart) -> QWidget:
        """Wrap a chart in a labeled surface frame for visual consistency."""
        frame = QFrame(self)
        frame.setObjectName("Surface")
        v = QVBoxLayout(frame)
        v.setContentsMargins(12, 10, 12, 10)
        v.setSpacing(6)
        label = QLabel(title, frame)
        label.setObjectName("SectionTitle")
        v.addWidget(label)
        v.addWidget(chart, stretch=1)
        return frame
