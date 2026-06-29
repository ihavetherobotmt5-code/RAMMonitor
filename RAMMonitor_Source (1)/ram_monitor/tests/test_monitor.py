"""Smoke test for the MonitorWorker — verifies signal plumbing.

We can't run a full Qt event loop in headless CI without a display, but
we CAN verify that:
* The worker can be constructed.
* Its signal exists and has the right name.
* Calling `collect()` once and emitting works end-to-end with a slot.

The Qt-backed test uses the `pytest-qt`-style pattern but avoids the
external dependency by spinning a minimal `QCoreApplication`.
"""
from __future__ import annotations

import os
import sys
from typing import Optional

import pytest

# Skip ALL tests in this module if we can't construct a QApplication (e.g.
# no display on a headless CI box). PySide6 will raise if neither
# DISPLAY (Linux) nor Windows is available.
try:
    from PySide6.QtCore import QCoreApplication, QTimer
    from PySide6.QtWidgets import QApplication
    _QT_OK = True
except Exception:  # pragma: no cover
    _QT_OK = False

from ram_monitor.config import Config
from ram_monitor.core.metrics import MetricsCollector
from ram_monitor.core.models import SystemMetrics


@pytest.mark.skipif(not _QT_OK, reason="PySide6 unavailable")
class TestMonitorWorkerPlumbing:
    def test_worker_constructs_and_signals_exist(self, qapp) -> None:
        from ram_monitor.core.monitor import MonitorWorker
        w = MonitorWorker(Config(poll_interval_seconds=10.0))
        assert hasattr(w, "metrics_ready")
        assert hasattr(w, "collection_error")
        assert hasattr(w, "request_stop")
        # Don't start the thread — we only want to verify construction.

    def test_signal_delivers_metrics(self, qapp) -> None:
        from PySide6.QtCore import QEventLoop
        from ram_monitor.core.monitor import MonitorWorker
        received: list[SystemMetrics] = []

        class StubCollector(MetricsCollector):
            def collect(self) -> SystemMetrics:
                return SystemMetrics(
                    total_bytes=8_000_000_000, available_bytes=4_000_000_000,
                    used_bytes=4_000_000_000, memory_percent=50.0,
                    cpu_percent=12.0, cpu_freq_mhz=3000.0,
                    process_count=10, uptime_seconds=100.0,
                    top_processes=(),
                )

        w = MonitorWorker(Config(poll_interval_seconds=0.05), collector=StubCollector())
        w.metrics_ready.connect(lambda m: received.append(m))

        # We need a running Qt event loop for QTimer.singleShot to fire —
        # QThread.wait() blocks the calling thread and prevents the timer
        # callback from running. Spin a QEventLoop instead, and quit it when
        # the worker finishes.
        loop = QEventLoop()
        w.finished.connect(loop.quit)
        w.start()
        # Schedule a stop after 200 ms (enough for ~4 ticks at 50 ms interval).
        QTimer.singleShot(200, w.request_stop)
        # Safety: don't hang the test forever if the worker misbehaves.
        QTimer.singleShot(3000, loop.quit)
        loop.exec()

        # The worker should have exited (or be exiting). Wait briefly for cleanup.
        assert w.wait(2000), "Worker did not exit within 2 s"
        assert len(received) >= 1
        assert isinstance(received[0], SystemMetrics)


# ── pytest fixture: shared QApplication ──────────────────────────────────

@pytest.fixture(scope="session")
def qapp():
    """Session-scoped QApplication. Yields None if Qt can't init."""
    if not _QT_OK:
        pytest.skip("PySide6 unavailable")
    # Use offscreen platform so we don't need an X server.
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication(sys.argv)
    yield app
