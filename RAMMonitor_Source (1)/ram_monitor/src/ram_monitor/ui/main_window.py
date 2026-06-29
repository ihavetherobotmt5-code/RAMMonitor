"""MainWindow — owns the dashboard and the MonitorWorker thread.

Lifecycle:
    __init__  → creates dashboard, creates worker (not yet started)
    show()    → starts worker
    closeEvent→ stops worker, waits ≤2 s for clean exit

The worker is parented to the window so Qt's object tree cleans it up if
the user kills the app via the OS. We still call `request_stop()` + `wait()`
explicitly so the worker doesn't get mid-collection GC.
"""
from __future__ import annotations

import sys
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import QMainWindow, QWidget

from ram_monitor.config import CONFIG, Config
from ram_monitor.core.metrics import MetricsCollector
from ram_monitor.core.models import SystemMetrics
from ram_monitor.core.monitor import MonitorWorker
from ram_monitor.ui.dashboard import DashboardView
from ram_monitor.ui.styles import build_stylesheet
from ram_monitor.utils.logger import get_logger

_log = get_logger()


class MainWindow(QMainWindow):
    """Top-level window. Owns the worker thread and the dashboard view."""

    def __init__(
        self,
        config: Config = CONFIG,
        collector: Optional[MetricsCollector] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._config = config

        self.setWindowTitle(config.window_title)
        self.resize(config.window_width, config.window_height)
        self.setMinimumSize(720, 520)

        # ── Central widget ────────────────────────────────────────────────
        self._dashboard = DashboardView(parent=self, config=config)
        self.setCentralWidget(self._dashboard)

        # ── Worker thread ─────────────────────────────────────────────────
        self._collector: MetricsCollector = collector or MetricsCollector(config)
        self._worker: MonitorWorker = MonitorWorker(
            config=config,
            collector=self._collector,
            parent=self,
        )
        self._worker.metrics_ready.connect(self._on_metrics, Qt.ConnectionType.QueuedConnection)
        self._worker.collection_error.connect(self._on_error, Qt.ConnectionType.QueuedConnection)

    # ── Public API ─────────────────────────────────────────────────────────

    def start_monitoring(self) -> None:
        """Kick off the worker. Safe to call once after `show()`."""
        if not self._worker.isRunning():
            self._worker.start()

    # ── Slots ──────────────────────────────────────────────────────────────

    def _on_metrics(self, metrics: SystemMetrics) -> None:
        # The signal carries `object`; narrow the type for clarity. If a
        # future bug sends the wrong type, fail loudly rather than crash Qt.
        if not isinstance(metrics, SystemMetrics):
            _log.error("Received non-SystemMetrics payload: %r", type(metrics))
            return
        self._dashboard.apply_metrics(metrics)

    def _on_error(self, message: str) -> None:
        # Transient collection errors are expected; log and move on. We do
        # NOT show a dialog (the spec forbids popups) — the next tick will
        # likely succeed and silently overwrite any stale UI state.
        _log.warning("Collection error: %s", message)

    # ── Qt overrides ──────────────────────────────────────────────────────

    def closeEvent(self, event: QCloseEvent) -> None:
        """Cleanly stop the worker before the window is destroyed."""
        try:
            if self._worker.isRunning():
                self._worker.request_stop()
                if not self._worker.wait(2000):
                    _log.warning("MonitorWorker did not stop within 2 s; terminating")
                    self._worker.terminate()
                    self._worker.wait(500)
        except Exception:  # noqa: BLE001 — never crash on close
            _log.exception("Error during worker shutdown")
        finally:
            super().closeEvent(event)

    # ── Convenience for tests / scripting ─────────────────────────────────

    @property
    def dashboard(self) -> DashboardView:
        return self._dashboard

    @property
    def worker(self) -> MonitorWorker:
        return self._worker
