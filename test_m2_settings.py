"""Tests for M2-9: Settings Architecture."""
from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault("LD_LIBRARY_PATH", "/home/z/.local/lib")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
    _QT_OK = True
except Exception:
    _QT_OK = False

from ram_monitor.config import CONFIG, Config


@pytest.fixture(scope="session")
def qapp():
    if not _QT_OK:
        pytest.skip("PySide6 unavailable")
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


@pytest.mark.skipif(not _QT_OK, reason="PySide6 unavailable")
class TestSettingsManager:
    def test_load_returns_config(self, qapp) -> None:
        from ram_monitor.ui.settings import SettingsManager
        sm = SettingsManager()
        config = sm.load()
        assert isinstance(config, Config)

    def test_load_with_no_settings_returns_defaults(self, qapp) -> None:
        from ram_monitor.ui.settings import SettingsManager
        sm = SettingsManager()
        sm.reset_to_defaults()
        config = sm.load()
        assert config.poll_interval_seconds == CONFIG.poll_interval_seconds
        assert config.animation_threshold_pct == CONFIG.animation_threshold_pct

    def test_save_then_load_roundtrip(self, qapp) -> None:
        from ram_monitor.ui.settings import SettingsManager
        sm = SettingsManager()
        sm.reset_to_defaults()
        custom = Config(
            poll_interval_seconds=3.0,
            animation_threshold_pct=5.0,
            history_length=120,
        )
        sm.save(custom)
        loaded = sm.load()
        assert loaded.poll_interval_seconds == 3.0
        assert loaded.animation_threshold_pct == 5.0
        assert loaded.history_length == 120
        sm.reset_to_defaults()

    def test_save_only_persists_non_defaults(self, qapp) -> None:
        from ram_monitor.ui.settings import SettingsManager
        sm = SettingsManager()
        sm.reset_to_defaults()
        sm.save(CONFIG)
        assert not sm._settings.contains("poll_interval_seconds")
        assert not sm._settings.contains("animation_threshold_pct")

    def test_reset_to_defaults(self, qapp) -> None:
        from ram_monitor.ui.settings import SettingsManager
        sm = SettingsManager()
        sm.save(Config(poll_interval_seconds=5.0))
        assert sm._settings.contains("poll_interval_seconds")
        sm.reset_to_defaults()
        assert not sm._settings.contains("poll_interval_seconds")

    def test_config_api_unchanged(self, qapp) -> None:
        c = Config()
        assert c.poll_interval_seconds == 1.5
        assert c.animation_threshold_pct == 2.0
        import dataclasses
        with pytest.raises(dataclasses.FrozenInstanceError):
            c.poll_interval_seconds = 5.0
