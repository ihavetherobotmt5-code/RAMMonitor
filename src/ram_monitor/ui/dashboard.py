"""DashboardView — Fluent dashboard using `ResponsiveGridLayout`.

Public API (UNCHANGED from V1):
    DashboardView(parent, config).apply_metrics(SystemMetrics)
"""
from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout, QWidget
from ram_monitor.config import CONFIG, Config
from ram_monitor.core.models import SystemMetrics
from ram_monitor.ui.charts import HistoryChart
from ram_monitor.ui.fluent_theme import FluentTheme
from ram_monitor.ui.process_panel import TopProcessesPanel
from ram_monitor.ui.responsive_grid import ResponsiveGridLayout
from ram_monitor.ui.stats_cards import StatCard
from ram_monitor.utils.formatters import format_bytes, format_frequency, format_percent, format_uptime

class DashboardView(QWidget):
    """The single page shown inside `MainWindow`."""
    def __init__(self, parent: Optional[QWidget] = None, config: Config = CONFIG, theme: Optional[FluentTheme] = None) -> None:
        super().__init__(parent)
        self._config = config
        self._theme = theme or FluentTheme.default()
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self._build_ui()

    def apply_metrics(self, m: SystemMetrics) -> None:
        self._card_ram_pct.set_value(m.memory_percent, sub_text=f"{format_bytes(m.used_bytes, binary=False)} used")
        self._card_ram_used.set_value(float(m.used_bytes), sub_text=f"{format_bytes(m.available_bytes, binary=False)} available")
        self._card_cpu_pct.set_value(m.cpu_percent, sub_text=format_frequency(m.cpu_freq_mhz))
        self._card_proc.set_value(float(m.process_count), sub_text=f"up {format_uptime(m.uptime_seconds)}")
        self._chart_ram.push(m.memory_percent)
        self._chart_cpu.push(m.cpu_percent)
        self._processes.update_processes(m.top_processes)

    def _build_ui(self) -> None:
        self._grid = ResponsiveGridLayout(self, theme=self._theme)
        self._section_overview = QLabel("Overview", self)
        self._section_overview.setObjectName("SectionHeader")
        self._grid.add_section_title(self._section_overview)
        self._card_ram_pct = StatCard(label="RAM", accent=self._config.color_ram, formatter=lambda v: format_percent(v), config=self._config, theme=self._theme)
        self._card_ram_used = StatCard(label="RAM Used", accent=self._config.color_ram, formatter=lambda v: format_bytes(int(v), binary=False), max_value=1.0, config=self._config, theme=self._theme)
        self._card_ram_used.set_ring_visible(False)
        self._card_ram_used.set_meter_visible(False)
        self._card_cpu_pct = StatCard(label="CPU", accent=self._config.color_cpu, formatter=lambda v: format_percent(v), config=self._config, theme=self._theme)
        self._card_proc = StatCard(label="Processes", accent=self._config.color_accent, formatter=lambda v: f"{int(v)}", max_value=1.0, config=self._config, theme=self._theme)
        self._card_proc.set_ring_visible(False)
        self._card_proc.set_meter_visible(False)
        for card in (self._card_ram_pct, self._card_ram_used, self._card_cpu_pct, self._card_proc):
            self._grid.add_card(card)
        self._chart_ram = HistoryChart(color=self._config.color_ram, y_max=100.0, y_label="%", parent=self)
        self._chart_cpu = HistoryChart(color=self._config.color_cpu, y_max=100.0, y_label="%", parent=self)
        self._chart_ram.setMinimumHeight(240)
        self._chart_cpu.setMinimumHeight(240)
        self._section_charts = QLabel("Performance History", self)
        self._section_charts.setObjectName("SectionHeader")
        self._grid.add_section_title(self._section_charts)
        self._grid.add_chart(self._wrap_chart("RAM History", self._chart_ram))
        self._grid.add_chart(self._wrap_chart("CPU History", self._chart_cpu))
        self._reserved = None
        self._grid.set_reserved(self._reserved)
        self._section_processes = QLabel("Top Processes", self)
        self._section_processes.setObjectName("SectionHeader")
        self._grid.add_section_title(self._section_processes)
        self._processes = TopProcessesPanel(self, config=self._config)
        self._processes.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._grid.set_process_panel(self._processes)
        self._grid.relayout(force=True)

    def _wrap_chart(self, title: str, chart: HistoryChart) -> QWidget:
        s = self._theme.spacing
        frame = QFrame(self)
        frame.setObjectName("Surface")
        v = QVBoxLayout(frame)
        v.setContentsMargins(s.md, s.sm, s.md, s.sm)
        v.setSpacing(s.sm)
        label = QLabel(title, frame)
        label.setObjectName("SectionTitle")
        v.addWidget(label)
        v.addWidget(chart, stretch=1)
        return frame
