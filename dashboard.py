"""DashboardView — Fluent dashboard using `ResponsiveGridLayout`.

Public API (UNCHANGED from V1):
    DashboardView(parent, config).apply_metrics(SystemMetrics)

What changed from V1:
* The static `QVBoxLayout` / `QHBoxLayout` composition was replaced by a
  `ResponsiveGridLayout` that reflows across 5 breakpoints.
* Cards are now `StatCard` instances with the M1 ring meter + smart
  animation. They're added to the grid via `add_card()`.
* M2-4: Section headers ("Overview", "Performance History", "Top Processes")
  create visual hierarchy between groups.
* Layout never rebuilds during a monitoring tick. Only `set_value` /
  `push` / `update_processes` are called on existing widgets.

Layout per tier (driven by `ResponsiveGridLayout`):
    xxl (>=2560): 4-card row, charts side-by-side
    xl (>=1280): 4-card row, charts side-by-side
    lg (900-1279): 4-card row, charts side-by-side (tighter)
    md (700-899): 2x2 cards, charts stacked
    sm (<700): 1-col stack of everything
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ram_monitor.config import CONFIG, Config
from ram_monitor.core.models import SystemMetrics
from ram_monitor.ui.charts import HistoryChart
from ram_monitor.ui.fluent_theme import FluentTheme
from ram_monitor.ui.process_panel import TopProcessesPanel
from ram_monitor.ui.responsive_grid import ResponsiveGridLayout
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
        theme: Optional[FluentTheme] = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._theme = theme or FluentTheme.default()
        # P0-2: WA_OpaquePaintEvent on the dashboard container so child
        # widget repaints (charts, cards) don't cascade up to MainWindow.
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self._build_ui()

    # -- Public API (UNCHANGED) -------------------------------------------

    def apply_metrics(self, m: SystemMetrics) -> None:
        """Push one snapshot into every child widget. Idempotent & O(rows).

        This method is called on every `MonitorWorker.metrics_ready` signal.
        It NEVER touches the layout — only `set_value` / `push` / update
        calls on existing widgets. Layout reflow happens exclusively in
        `ResponsiveGridLayout`'s resize-event handler.
        """
        # -- Cards ---------------------------------------------------------
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

        # -- Charts --------------------------------------------------------
        self._chart_ram.push(m.memory_percent)
        self._chart_cpu.push(m.cpu_percent)

        # -- Process panel -------------------------------------------------
        self._processes.update_processes(m.top_processes)

    # -- UI construction --------------------------------------------------

    def _build_ui(self) -> None:
        # The ResponsiveGridLayout owns the QGridLayout on this widget.
        self._grid = ResponsiveGridLayout(self, theme=self._theme)

        # -- M2-4: Section title "Overview" above the cards ----------------
        # Commercial dashboards use section headers to create visual rhythm.
        # These are static QLabels — created once, never updated per-tick.
        self._section_overview = QLabel("Overview", self)
        self._section_overview.setObjectName("SectionHeader")
        self._grid.add_section_title(self._section_overview)

        # -- 4 stat cards --------------------------------------------------
        self._card_ram_pct = StatCard(
            label="RAM", accent=self._config.color_ram,
            formatter=lambda v: format_percent(v),
            config=self._config, theme=self._theme,
        )
        self._card_ram_used = StatCard(
            label="RAM Used", accent=self._config.color_ram,
            formatter=lambda v: format_bytes(int(v), binary=False),
            max_value=1.0,  # meter is suppressed
            config=self._config, theme=self._theme,
        )
        # P1-3: Use public accessors instead of reaching into _ring/_meter
        # (Law of Demeter fix). Same V1 behavior, cleaner coupling.
        self._card_ram_used.set_ring_visible(False)
        self._card_ram_used.set_meter_visible(False)

        self._card_cpu_pct = StatCard(
            label="CPU", accent=self._config.color_cpu,
            formatter=lambda v: format_percent(v),
            config=self._config, theme=self._theme,
        )
        self._card_proc = StatCard(
            label="Processes", accent=self._config.color_accent,
            formatter=lambda v: f"{int(v)}",
            max_value=1.0,
            config=self._config, theme=self._theme,
        )
        self._card_proc.set_ring_visible(False)
        self._card_proc.set_meter_visible(False)

        for card in (
            self._card_ram_pct, self._card_ram_used,
            self._card_cpu_pct, self._card_proc,
        ):
            self._grid.add_card(card)

        # -- 2 history charts (wrapped in surface frames for visual consistency) --
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
        self._chart_ram.setMinimumHeight(240)
        self._chart_cpu.setMinimumHeight(240)

        # -- M2-4: Section title "Performance History" above the charts ----
        self._section_charts = QLabel("Performance History", self)
        self._section_charts.setObjectName("SectionHeader")
        self._grid.add_section_title(self._section_charts)

        self._grid.add_chart(self._wrap_chart("RAM History", self._chart_ram))
        self._grid.add_chart(self._wrap_chart("CPU History", self._chart_cpu))

        # -- Reserved cell for M3's "Why did RAM change?" panel --
        # P0-3 fix: No placeholder widget is created in M1. The reserved cell
        # mechanism (ResponsiveGridLayout.set_reserved) accepts None, which
        # means no cell is added to the layout. M3 will populate this when
        # the Insights panel is implemented. No debug text, no empty state,
        # no visual noise — the dashboard simply doesn't have this section yet.
        self._reserved = None  # M3 will replace this with an actual widget
        self._grid.set_reserved(self._reserved)

        # -- Process panel (always full-width at the bottom) --
        # -- M2-4: Section title "Top Processes" above the table --
        self._section_processes = QLabel("Top Processes", self)
        self._section_processes.setObjectName("SectionHeader")
        self._grid.add_section_title(self._section_processes)

        self._processes = TopProcessesPanel(self, config=self._config)
        self._processes.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred,
        )
        self._grid.set_process_panel(self._processes)

        # Trigger the initial layout based on current size.
        self._grid.relayout(force=True)

    def _wrap_chart(self, title: str, chart: HistoryChart) -> QWidget:
        """Wrap a chart in a labeled surface frame for visual consistency.

        M2-4: Uses theme spacing tokens instead of hardcoded margins.
        """
        s = self._theme.spacing
        frame = QFrame(self)
        frame.setObjectName("Surface")
        v = QVBoxLayout(frame)
        v.setContentsMargins(s.md, s.sm, s.md, s.sm)  # 12px sides, 8px top/bottom
        v.setSpacing(s.sm)  # 8px between title and chart
        label = QLabel(title, frame)
        label.setObjectName("SectionTitle")
        v.addWidget(label)
        v.addWidget(chart, stretch=1)
        return frame
