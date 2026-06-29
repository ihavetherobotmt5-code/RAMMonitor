"""MainWindow — owns the dashboard and the MonitorWorker thread.

Lifecycle:
    __init__  → creates dashboard, creates worker (not yet started)
    show()    → starts worker
    closeEvent→ stops worker, waits ≤2 s for clean exit

The worker is parented to the window so Qt's object tree cleans it up if
the user kills the app via the OS. We still call `request_stop()` + `wait()`
explicitly so the worker doesn't get mid-collection GC.

M1 changes (preserved API):
* A `QSplitter` reserves a 0-width sidebar slot for M4. No sidebar content
  is instantiated — just the slot. The dashboard takes the full width.
* Public API (`MainWindow(config, collector)`, `start_monitoring()`,
  `dashboard` property, `worker` property) is UNCHANGED.

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

    def __init__(
        self,
        config: Config = CONFIG,
        collector: Optional[MetricsCollector] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        from ram_monitor.ui.fluent_theme import FluentTheme
        self._theme = FluentTheme.default()

        self.setWindowTitle(config.window_title)
        self.resize(config.window_width, config.window_height)
        self.setMinimumSize(720, 520)

        # -- Splitter: dashboard + reserved sidebar slot for M4 -------------
        # The sidebar widget is a placeholder — 0 width, no content. M4
        # will populate it with navigation / Compact Mode toggle. We use
        # a QSplitter (not a QHBoxLayout) so the sidebar can be collapsible
        # in M4 without restructuring the window.
        self._splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self._dashboard = DashboardView(parent=self._splitter, config=config)

        # Reserved sidebar slot — invisible in M1, populated in M4.
        self._sidebar_slot = QWidget(self._splitter)
        self._sidebar_slot.setMaximumWidth(0)  # collapsed
        self._sidebar_slot.setVisible(False)   # not even shown in M1

        self._splitter.addWidget(self._dashboard)
        self._splitter.addWidget(self._sidebar_slot)
        self._splitter.setStretchFactor(0, 1)  # dashboard expands
        self._splitter.setStretchFactor(1, 0)  # sidebar doesn't
        self._splitter.setSizes([config.window_width, 0])
        self._splitter.setHandleWidth(0)  # no visible drag handle in M1

        self.setCentralWidget(self._splitter)

        # -- Worker thread --------------------------------------------------
        self._collector: MetricsCollector = collector or MetricsCollector(config)
        self._worker: MonitorWorker = MonitorWorker(
            config=config,
            collector=self._collector,
            parent=self,
        )
        self._worker.metrics_ready.connect(self._on_metrics, Qt.ConnectionType.QueuedConnection)
        self._worker.collection_error.connect(self._on_error, Qt.ConnectionType.QueuedConnection)

        # -- M2-5: Compact Mode window ------------------------------------
        # A small always-on-top floating window. Shares the same worker
        # signal — no duplicate polling. Toggle via toggle_compact_mode().
        self._compact_window = CompactModeWindow(
            config=config, theme=getattr(self, '_theme', None), parent=self,
        )
        # Forward metrics to the compact window on every tick.
        self._worker.metrics_ready.connect(
            self._compact_window.apply_metrics, Qt.ConnectionType.QueuedConnection,
        )

        # M2-8: Keyboard shortcuts for accessibility.
        # Ctrl+M: Toggle compact mode
        self._shortcut_compact = QShortcut(QKeySequence("Ctrl+M"), self)
        self._shortcut_compact.activated.connect(self.toggle_compact_mode)
        # Ctrl+Q: Quit
        self._shortcut_quit = QShortcut(QKeySequence("Ctrl+Q"), self)
        self._shortcut_quit.activated.connect(self.close)

    # -- Public API (UNCHANGED) -------------------------------------------

    def start_monitoring(self) -> None:
        """Kick off the worker. Safe to call once after `show()`."""
        if not self._worker.isRunning():
            self._worker.start()

    # -- M2-5: Compact Mode ----------------------------------------------

    def toggle_compact_mode(self) -> None:
        """Show or hide the compact floating monitor.

        The compact window shares the same MonitorWorker signal — no
        duplicate polling, no restart needed. Geometry is remembered
        via QSettings.
        """
        self._compact_window.toggle()

    @property
    def compact_window(self) -> CompactModeWindow:
        """The compact mode window (for testing / scripting)."""
        return self._compact_window

    # -- Slots ------------------------------------------------------------

    def _on_metrics(self, metrics: SystemMetrics) -> None:
        # The signal carries `object`; narrow the type for clarity. If a
        # future bug sends the wrong type, fail loudly rather than crash Qt.
        if not isinstance(metrics, SystemMetrics):
            _log.error("Received non-SystemMetrics payload: %r", type(metrics))
            return
        self._dashboard.apply_metrics(metrics)
        # M2-5: Compact window also receives metrics (connected via signal
        # in __init__, but we also forward here for redundancy in case the
        # compact window was created after the signal connection).
        self._compact_window.apply_metrics(metrics)

    def _on_error(self, message: str) -> None:
        # Transient collection errors are expected; log and move on. We do
        # NOT show a dialog (the spec forbids popups) — the next tick will
        # likely succeed and silently overwrite any stale UI state.
        _log.warning("Collection error: %s", message)

    # -- Qt overrides -----------------------------------------------------

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

    # -- Convenience for tests / scripting --------------------------------

    @property
    def dashboard(self) -> DashboardView:
        return self._dashboard

    @property
    def worker(self) -> MonitorWorker:
        return self._worker

    @property
    def sidebar_slot(self) -> QWidget:
        """Reserved for M4. Returns the placeholder widget."""
        return self._sidebar_slot
