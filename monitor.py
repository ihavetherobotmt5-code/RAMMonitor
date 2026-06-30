"""MonitorWorker — the polling thread.

Runs in its own `QThread`, calls `MetricsCollector.collect()` every
`poll_interval_seconds`, and emits a `metrics_ready` signal. The GUI
thread receives the signal via Qt's queued-connection mechanism — no
locks, no manual marshalling.

Shutdown contract:
    Calling `request_stop()` sets an internal `Event`, the loop exits at
    the next opportunity (<= one poll interval later), and the thread
    returns. `MainWindow.closeEvent()` calls `request_stop()` then
    `wait(2000)` to guarantee clean teardown.
"""
from __future__ import annotations

import threading
import time
from typing import Optional

from PySide6.QtCore import QThread, Signal

from ram_monitor.config import CONFIG, Config
from ram_monitor.core.metrics import MetricsCollector
from ram_monitor.core.models import SystemMetrics
from ram_monitor.utils.logger import get_logger

_log = get_logger()


class MonitorWorker(QThread):
    """Background polling thread. Emits one signal per tick."""

    #: Emitted on every successful collection. Carries the full snapshot.
    metrics_ready = Signal(object)

    #: Emitted once if the collector raises — UI can show a small banner.
    collection_error = Signal(str)

    def __init__(
        self,
        config: Config = CONFIG,
        collector: Optional[MetricsCollector] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._config: Config = config
        self._collector: MetricsCollector = collector or MetricsCollector(config)
        self._stop_event: threading.Event = threading.Event()
        self._prime_cpu_percent()

    # -- Public API -------------------------------------------------------

    def request_stop(self) -> None:
        """Ask the loop to exit. Non-blocking; pair with `wait()`."""
        self._stop_event.set()

    # -- QThread override -------------------------------------------------

    def run(self) -> None:
        """Polling loop. Runs until `request_stop()` is called."""
        interval = self._config.poll_interval_seconds
        _log.debug("MonitorWorker started; interval=%.2fs", interval)
        while not self._stop_event.is_set():
            t0 = time.perf_counter()
            try:
                metrics = self._collector.collect()
                self.metrics_ready.emit(metrics)
            except Exception as exc:
                _log.exception("Collection failed: %s", exc)
                self.collection_error.emit(str(exc))
            elapsed = time.perf_counter() - t0
            remaining = max(0.0, interval - elapsed)
            self._stop_event.wait(remaining)
        _log.debug("MonitorWorker exited cleanly")

    # -- Internals --------------------------------------------------------

    @staticmethod
    def _prime_cpu_percent() -> None:
        """Discard the first cpu_percent() reading (always 0.0)."""
        try:
            import psutil
            psutil.cpu_percent(interval=None)
        except Exception:
            pass
