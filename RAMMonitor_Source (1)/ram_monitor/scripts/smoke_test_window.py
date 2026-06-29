"""Smoke test: construct MainWindow offscreen, push one metrics tick,
verify it doesn't crash and the dashboard received the data.

Run:
    LD_LIBRARY_PATH=/home/z/.local/lib QT_QPA_PLATFORM=offscreen \
        .venv/bin/python scripts/smoke_test_window.py
"""
from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from ram_monitor.config import CONFIG
from ram_monitor.core.models import ProcessInfo, SystemMetrics
from ram_monitor.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    w = MainWindow(config=CONFIG)
    w.show()

    # Push one fake metrics payload directly (bypass the worker).
    fake = SystemMetrics(
        total_bytes=8_000_000_000,
        available_bytes=4_000_000_000,
        used_bytes=4_000_000_000,
        memory_percent=50.0,
        cpu_percent=12.3,
        cpu_freq_mhz=3400.0,
        process_count=142,
        uptime_seconds=3661,
        top_processes=(
            ProcessInfo(pid=1, name="chrome.exe", used_bytes=2_150_000_000,
                        share_percent=26.875, delta_bytes=550_000_000),
            ProcessInfo(pid=2, name="code.exe", used_bytes=850_000_000,
                        share_percent=10.625, delta_bytes=-128_000_000),
            ProcessInfo(pid=3, name="explorer.exe", used_bytes=120_000_000,
                        share_percent=1.5, delta_bytes=0),
        ),
    )
    w._on_metrics(fake)

    # Verify the dashboard received the data.
    d = w.dashboard
    assert d._card_ram_pct.current_value == 50.0
    assert d._card_cpu_pct.current_value == 12.3
    assert d._chart_ram.latest == 50.0
    assert d._chart_cpu.latest == 12.3

    # Push a second tick to exercise the chart ring and process-table update.
    fake2 = SystemMetrics(
        total_bytes=8_000_000_000, available_bytes=3_800_000_000,
        used_bytes=4_200_000_000, memory_percent=52.5,
        cpu_percent=15.7, cpu_freq_mhz=3400.0,
        process_count=145, uptime_seconds=3663,
        top_processes=(
            ProcessInfo(pid=1, name="chrome.exe", used_bytes=2_300_000_000,
                        share_percent=28.75, delta_bytes=150_000_000),
            ProcessInfo(pid=2, name="code.exe", used_bytes=820_000_000,
                        share_percent=10.25, delta_bytes=-30_000_000),
        ),
    )
    w._on_metrics(fake2)
    assert d._chart_ram.latest == 52.5
    assert d._chart_cpu.latest == 15.7

    # Cleanly close (exercises closeEvent → worker shutdown).
    w.close()

    print("SMOKE OK: MainWindow constructed, 2 ticks pushed, charts updated, closed cleanly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
