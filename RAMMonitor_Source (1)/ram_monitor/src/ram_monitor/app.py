"""Application bootstrap.

Single entry point: `python -m ram_monitor` (see `__main__.py`).

Responsibilities:
* Construct `QApplication` with high-DPI enabled.
* Apply the Windows 11 dark stylesheet.
* On Windows 11, request the native dark title bar and rounded corners via
  the `darkdetect`-free, ctypes-backed helper below.
* Construct `MainWindow`, show it, start monitoring, run the event loop.

The Windows 11 dark-title-bar trick uses `ctypes.windll.dwmapi` directly —
no extra dependency, fails silently on Linux/macOS (we're in a build env).
"""
from __future__ import annotations

import os
import sys
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from ram_monitor.config import CONFIG, Config
from ram_monitor.core.metrics import MetricsCollector
from ram_monitor.ui.main_window import MainWindow
from ram_monitor.ui.styles import build_stylesheet
from ram_monitor.utils.logger import get_logger

_log = get_logger()


def _enable_windows_11_dark_titlebar(window) -> None:
    """Set the title bar to dark mode on Windows 11 (build 22000+).

    No-op on other platforms. We use ctypes directly to avoid pulling in
    `pywin32` as a runtime dependency — PyInstaller bundles would otherwise
    gain ~5 MB just for one syscall.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        from ctypes import wintypes

        hwnd = int(window.winId())
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20  # Win11 22H2+
        value = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(value), ctypes.sizeof(value),
        )
    except Exception:  # pragma: no cover — defensive
        _log.debug("Could not set dark title bar (continuing)", exc_info=True)


def _enable_windows_11_rounded_corners() -> None:
    """Best-effort: Windows 11 already rounds window corners by default
    when DWM compositing is on. Nothing to do — kept as a hook for future
    per-window corner preference APIs if needed.
    """
    return None


def create_application(config: Config = CONFIG) -> QApplication:
    """Build the QApplication with our preferred attributes set."""
    # High-DPI scaling must be set before QApplication is constructed.
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough,
    )
    app = QApplication(sys.argv)
    app.setApplicationName("RAM Monitor")
    app.setApplicationDisplayName("RAM Monitor")
    app.setOrganizationName("RAMMonitor")
    app.setStyle("Fusion")

    # Default font — Segoe UI on Windows, falls back to system default elsewhere.
    font = QFont("Segoe UI Variable", 9)
    app.setFont(font)

    app.setStyleSheet(build_stylesheet(config))
    return app


def run(
    config: Config = CONFIG,
    collector: Optional[MetricsCollector] = None,
) -> int:
    """Run the application until the user closes the window. Returns exit code."""
    app = create_application(config)

    window = MainWindow(config=config, collector=collector)
    window.show()
    _enable_windows_11_dark_titlebar(window)
    _enable_windows_11_rounded_corners()
    window.start_monitoring()

    _log.debug("Entering Qt event loop")
    exit_code = app.exec()
    _log.debug("Qt event loop exited with code %d", exit_code)
    return exit_code


if __name__ == "__main__":  # pragma: no cover
    sys.exit(run())
