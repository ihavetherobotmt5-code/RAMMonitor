"""MainWindow — owns the dashboard and the MonitorWorker thread.

M2-5: Compact Mode window — toggle via Ctrl+M or toggle_compact_mode().
M2-8: Keyboard shortcuts — Ctrl+M (compact), Ctrl+Q (quit).
"""
from __future__ import annotations
import sys
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import QMainWindow, QSplitter, QWidget
from ram_monitor.config import CONFIG, Config
from ram_monitor.core.metrics import MetricsCollector
from ram_monitor.core.models import SystemMetrics
from ram_monitor.core.monitor import MonitorWorker
from ram_monitor.ui.dashboard import DashboardView
from ram_monitor.ui.compact_mode import CompactModeWindow
from ram_monitor.ui.styles import build_stylesheet
from ram_monitor.utils.logger import get_logger

_log = get_logger()

class MainWindow(QMainWindow):
    """Top-level window. Owns the worker thread and the dashboard view."""
    def __init__(self, config: Config = CONFIG, collector: Optional[MetricsCollector] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._config = config
        from ram_monitor.ui.fluent_theme import FluentTheme
        self._theme = FluentTheme.default()
        self.setWindowTitle(config.window_title)
        self.resize(config.window_width, config.window_height)
        self.setMinimumSize(720, 520)
        self._splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self._dashboard = DashboardView(parent=self._splitter, config=config)
        self._sidebar_slot = QWidget(self._splitter)
        self._sidebar_slot.setMaximumWidth(0)
        self._sidebar_slot.setVisible(False)
        self._splitter.addWidget(self._dashboard)
        self._splitter.addWidget(self._sidebar_slot)
        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 0)
        self._splitter.setSizes([config.window_width, 0])
        self._splitter.setHandleWidth(0)
        self.setCentralWidget(self._splitter)
        self._collector: MetricsCollector = collector or MetricsCollector(config)
        self._worker: MonitorWorker = MonitorWorker(config=config, collector=self._collector, parent=self)
        self._worker.metrics_ready.connect(self._on_metrics, Qt.ConnectionType.QueuedConnection)
        self._worker.collection_error.connect(self._on_error, Qt.ConnectionType.QueuedConnection)
        self._compact_window = CompactModeWindow(config=config, theme=getattr(self, '_theme', None), parent=self)
        self._worker.metrics_ready.connect(self._compact_window.apply_metrics, Qt.ConnectionType.QueuedConnection)
        self._shortcut_compact = QShortcut(QKeySequence("Ctrl+M"), self)
        self._shortcut_compact.activated.connect(self.toggle_compact_mode)
        self._shortcut_quit = QShortcut(QKeySequence("Ctrl+Q"), self)
        self._shortcut_quit.activated.connect(self.close)

    def start_monitoring(self) -> None:
        if not self._worker.isRunning(): self._worker.start()

    def toggle_compact_mode(self) -> None:
        self._compact_window.toggle()

    @property
    def compact_window(self) -> CompactModeWindow:
        return self._compact_window

    def _on_metrics(self, metrics: SystemMetrics) -> None:
        if not isinstance(metrics, SystemMetrics):
            _log.error("Received non-SystemMetrics payload: %r", type(metrics)); return
        self._dashboard.apply_metrics(metrics)
        self._compact_window.apply_metrics(metrics)

    def _on_error(self, message: str) -> None:
        _log.warning("Collection error: %s", message)

    def closeEvent(self, event: QCloseEvent) -> None:
        try:
            if self._worker.isRunning():
                self._worker.request_stop()
                if not self._worker.wait(2000):
                    _log.warning("MonitorWorker did not stop within 2 s; terminating")
                    self._worker.terminate()
                    self._worker.wait(500)
        except Exception:
            _log.exception("Error during worker shutdown")
        finally:
            super().closeEvent(event)

    @property
    def dashboard(self) -> DashboardView:
        return self._dashboard
    @property
    def worker(self) -> MonitorWorker:
        return self._worker
    @property
    def sidebar_slot(self) -> QWidget:
        return self._sidebar_slot
