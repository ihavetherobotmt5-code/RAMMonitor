"""Tests for `ram_monitor.utils.logger`."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from ram_monitor.utils.logger import _default_log_dir


class TestDefaultLogDir:
    def test_linux_path(self) -> None:
        with patch("ram_monitor.utils.logger.sys") as mock_sys, \
             patch("ram_monitor.utils.logger.os") as mock_os:
            mock_sys.platform = "linux"
            mock_os.environ = {}
            result = _default_log_dir()
            assert result == Path.home() / ".ram_monitor" / "logs"

    def test_macos_path(self) -> None:
        with patch("ram_monitor.utils.logger.sys") as mock_sys, \
             patch("ram_monitor.utils.logger.os") as mock_os:
            mock_sys.platform = "darwin"
            mock_os.environ = {}
            result = _default_log_dir()
            assert result == Path.home() / "Library" / "Logs" / "RAMMonitor"

    def test_windows_path_with_localappdata(self) -> None:
        with patch("ram_monitor.utils.logger.sys") as mock_sys, \
             patch("ram_monitor.utils.logger.os") as mock_os:
            mock_sys.platform = "win32"
            mock_os.environ = {"LOCALAPPDATA": "C:/Users/test/AppData/Local"}
            result = _default_log_dir()
            assert str(result) == "C:/Users/test/AppData/Local/RAMMonitor/logs"

    def test_windows_path_without_localappata_falls_back(self) -> None:
        with patch("ram_monitor.utils.logger.sys") as mock_sys, \
             patch("ram_monitor.utils.logger.os") as mock_os:
            mock_sys.platform = "win32"
            mock_os.environ = {}
            result = _default_log_dir()
            assert "RAMMonitor" in str(result)
            assert "logs" in str(result)


class TestLoggerPublicAPI:
    def test_get_logger_returns_logger(self) -> None:
        from ram_monitor.utils.logger import get_logger
        log = get_logger()
        assert log is not None
        assert log.name == "ram_monitor"

    def test_get_logger_is_idempotent(self) -> None:
        from ram_monitor.utils.logger import get_logger
        log1 = get_logger()
        log2 = get_logger()
        assert log1 is log2
