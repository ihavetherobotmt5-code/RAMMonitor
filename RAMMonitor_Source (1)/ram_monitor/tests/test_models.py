"""Unit tests for `ram_monitor.core.models`.

Verifies immutability, slot behavior, and the convenience properties on
`SystemMetrics` and `ProcessInfo`.
"""
from __future__ import annotations

import dataclasses
import pytest

from ram_monitor.core.models import ProcessInfo, SystemMetrics


class TestProcessInfo:
    def test_construction(self) -> None:
        p = ProcessInfo(
            pid=42, name="chrome.exe",
            used_bytes=2_000_000_000,
            share_percent=25.0,
            delta_bytes=500_000_000,
        )
        assert p.pid == 42
        assert p.name == "chrome.exe"
        assert p.used_bytes == 2_000_000_000
        assert p.share_percent == 25.0
        assert p.delta_bytes == 500_000_000

    def test_delta_direction_up(self) -> None:
        p = ProcessInfo(pid=1, name="x", used_bytes=100, share_percent=0.0, delta_bytes=50)
        assert p.delta_direction == "up"

    def test_delta_direction_down(self) -> None:
        p = ProcessInfo(pid=1, name="x", used_bytes=100, share_percent=0.0, delta_bytes=-50)
        assert p.delta_direction == "down"

    def test_delta_direction_flat(self) -> None:
        p = ProcessInfo(pid=1, name="x", used_bytes=100, share_percent=0.0, delta_bytes=0)
        assert p.delta_direction == "flat"

    def test_default_delta_is_zero(self) -> None:
        p = ProcessInfo(pid=1, name="x", used_bytes=100, share_percent=0.0)
        assert p.delta_bytes == 0
        assert p.delta_direction == "flat"

    def test_frozen_is_immutable(self) -> None:
        p = ProcessInfo(pid=1, name="x", used_bytes=100, share_percent=0.0)
        with pytest.raises(dataclasses.FrozenInstanceError):
            p.used_bytes = 200  # type: ignore[misc]

    def test_uses_slots(self) -> None:
        p = ProcessInfo(pid=1, name="x", used_bytes=100, share_percent=0.0)
        # slotted dataclasses have no __dict__.
        assert not hasattr(p, "__dict__")


class TestSystemMetrics:
    def test_minimal_construction(self) -> None:
        m = SystemMetrics(
            total_bytes=8_000_000_000,
            available_bytes=4_000_000_000,
            used_bytes=4_000_000_000,
            memory_percent=50.0,
            cpu_percent=12.3,
        )
        assert m.cpu_freq_mhz is None
        assert m.process_count == 0
        assert m.uptime_seconds == 0.0
        assert m.top_processes == ()

    def test_rounded_percent(self) -> None:
        m = SystemMetrics(
            total_bytes=8_000_000_000,
            available_bytes=4_000_000_000,
            used_bytes=4_000_000_000,
            memory_percent=42.3456,
            cpu_percent=12.3,
        )
        assert m.memory_percent_rounded == 42.3

    def test_with_processes(self) -> None:
        procs = (
            ProcessInfo(pid=1, name="a", used_bytes=100, share_percent=1.0),
            ProcessInfo(pid=2, name="b", used_bytes=200, share_percent=2.0),
        )
        m = SystemMetrics(
            total_bytes=10_000, available_bytes=9_000, used_bytes=1_000,
            memory_percent=10.0, cpu_percent=5.0,
            top_processes=procs,
        )
        assert len(m.top_processes) == 2
        assert m.top_processes[0].name == "a"

    def test_frozen(self) -> None:
        m = SystemMetrics(
            total_bytes=10, available_bytes=5, used_bytes=5,
            memory_percent=50.0, cpu_percent=0.0,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            m.cpu_percent = 99.0  # type: ignore[misc]
