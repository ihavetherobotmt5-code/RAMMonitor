"""Smoke test for the MonitorWorker — verifies signal plumbing."""
from __future__ import annotations

import os
import sys

import pytest

try:
    from PySide6.QtCore import QCoreApplication, QTimer
    from PySide6.QtWidgets import QApplication
    _QT_OK = True
except Exception:
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
        loop = QEventLoop()
        w.finished.connect(loop.quit)
        w.start()
        QTimer.singleShot(200, w.request_stop)
        QTimer.singleShot(3000, loop.quit)
        loop.exec()
        assert w.wait(2000), "Worker did not exit within 2 s"
        assert len(received) >= 1
        assert isinstance(received[0], SystemMetrics)


@pytest.fixture(scope="session")
def qapp():
    if not _QT_OK:
        pytest.skip("PySide6 unavailable")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication(sys.argv)
    yield app
