"""Settings architecture — persistent configuration without API breaks.

M2-9: Provides a SettingsManager that loads/saves user preferences via
QSettings (Windows registry on Windows, .config on Linux).
"""
from __future__ import annotations
from dataclasses import replace
from typing import Any
from PySide6.QtCore import QSettings
from ram_monitor.config import CONFIG, Config

class SettingsManager:
    """Manages persistent user settings via QSettings."""
    def __init__(self, organization: str = "RAMMonitor", app_name: str = "RAMMonitor") -> None:
        self._settings = QSettings(organization, app_name)

    def load(self, base: Config = CONFIG) -> Config:
        overrides: dict[str, Any] = {}
        if self._settings.contains("poll_interval_seconds"):
            poll = self._settings.value("poll_interval_seconds", type=float)
            if poll is not None and poll > 0 and poll != base.poll_interval_seconds:
                overrides["poll_interval_seconds"] = poll
        if self._settings.contains("animation_threshold_pct"):
            threshold = self._settings.value("animation_threshold_pct", type=float)
            if threshold is not None and threshold >= 0 and threshold != base.animation_threshold_pct:
                overrides["animation_threshold_pct"] = threshold
        if self._settings.contains("history_length"):
            history = self._settings.value("history_length", type=int)
            if history is not None and history > 0 and history != base.history_length:
                overrides["history_length"] = history
        if self._settings.contains("top_processes_count"):
            top_procs = self._settings.value("top_processes_count", type=int)
            if top_procs is not None and top_procs > 0 and top_procs != base.top_processes_count:
                overrides["top_processes_count"] = top_procs
        if self._settings.contains("window_width"):
            window_width = self._settings.value("window_width", type=int)
            if window_width is not None and window_width > 0 and window_width != base.window_width:
                overrides["window_width"] = window_width
        if self._settings.contains("window_height"):
            window_height = self._settings.value("window_height", type=int)
            if window_height is not None and window_height > 0 and window_height != base.window_height:
                overrides["window_height"] = window_height
        if not overrides:
            return base
        return replace(base, **overrides)

    def save(self, config: Config) -> None:
        defaults = CONFIG
        if config.poll_interval_seconds != defaults.poll_interval_seconds:
            self._settings.setValue("poll_interval_seconds", config.poll_interval_seconds)
        if config.animation_threshold_pct != defaults.animation_threshold_pct:
            self._settings.setValue("animation_threshold_pct", config.animation_threshold_pct)
        if config.history_length != defaults.history_length:
            self._settings.setValue("history_length", config.history_length)
        if config.top_processes_count != defaults.top_processes_count:
            self._settings.setValue("top_processes_count", config.top_processes_count)
        if config.window_width != defaults.window_width:
            self._settings.setValue("window_width", config.window_width)
        if config.window_height != defaults.window_height:
            self._settings.setValue("window_height", config.window_height)
        self._settings.sync()

    def reset_to_defaults(self) -> None:
        self._settings.clear()
        self._settings.sync()
