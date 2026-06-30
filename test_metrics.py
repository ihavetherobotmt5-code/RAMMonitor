"""Unit + smoke tests for `ram_monitor.core.metrics.MetricsCollector`."""
from __future__ import annotations

from typing import Optional

import pytest

from ram_monitor.config import Config
from ram_monitor.core.metrics import MetricsCollector
from ram_monitor.core.models import ProcessInfo, SystemMetrics


class _FakeMemInfo:
    def __init__(self, rss: int) -> None:
        self.rss = rss


class _FakeVM:
    def __init__(self, total: int, available: int, used: int, percent: float) -> None:
        self.total = total
        self.available = available
        self.used = used
        self.percent = percent


class _FakeProc:
    def __init__(self, pid: int, name: str, rss: int, alive: bool = True) -> None:
        self.info = {
            "pid": pid,
            "name": name,
            "memory_info": _FakeMemInfo(rss) if alive else None,
        }


class _FakeFreq:
    def __init__(self, current: float) -> None:
        self.current = current


class FakePsutil:
    def __init__(self) -> None:
        self._processes: list[_FakeProc] = []
        self._vm = _FakeVM(total=8_000_000_000, available=4_000_000_000,
                           used=4_000_000_000, percent=50.0)
        self._cpu_percent = 10.0
        self._freq: Optional[_FakeFreq] = _FakeFreq(3000.0)
        self._boot_time = 1_700_000_000.0

    def set_processes(self, procs: list[_FakeProc]) -> None:
        self._processes = procs

    def set_vm(self, vm: _FakeVM) -> None:
        self._vm = vm

    def virtual_memory(self) -> _FakeVM:
        return self._vm

    def cpu_percent(self, interval: Optional[float] = None) -> float:
        return self._cpu_percent

    def cpu_freq(self) -> Optional[_FakeFreq]:
        return self._freq

    def boot_time(self) -> float:
        return self._boot_time

    def process_iter(self, attrs=None):
        return list(self._processes)

    class NoSuchProcess(Exception):
        pass

    class AccessDenied(Exception):
        pass


@pytest.fixture
def fake_psutil(monkeypatch):
    fake = FakePsutil()
    import ram_monitor.core.metrics as metrics_mod
    monkeypatch.setattr(metrics_mod, "psutil", fake)
    return fake


class TestMetricsCollector:
    def test_collect_returns_system_metrics(self, fake_psutil) -> None:
        fake_psutil.set_processes([
            _FakeProc(1, "a.exe", 1_000_000_000),
            _FakeProc(2, "b.exe", 500_000_000),
        ])
        c = MetricsCollector(Config(top_processes_count=4))
        m = c.collect()
        assert isinstance(m, SystemMetrics)
        assert m.total_bytes == 8_000_000_000
        assert m.process_count == 2
        assert len(m.top_processes) == 2
        assert m.top_processes[0].name == "a.exe"

    def test_first_tick_has_zero_delta(self, fake_psutil) -> None:
        fake_psutil.set_processes([_FakeProc(1, "a.exe", 1_000_000)])
        c = MetricsCollector()
        m = c.collect()
        assert m.top_processes[0].delta_bytes == 0

    def test_delta_computed_on_second_tick(self, fake_psutil) -> None:
        fake_psutil.set_processes([_FakeProc(1, "a.exe", 1_000_000)])
        c = MetricsCollector()
        c.collect()
        fake_psutil.set_processes([_FakeProc(1, "a.exe", 1_500_000)])
        m = c.collect()
        assert m.top_processes[0].delta_bytes == 500_000

    def test_negative_delta(self, fake_psutil) -> None:
        fake_psutil.set_processes([_FakeProc(1, "a.exe", 2_000_000)])
        c = MetricsCollector()
        c.collect()
        fake_psutil.set_processes([_FakeProc(1, "a.exe", 1_200_000)])
        m = c.collect()
        assert m.top_processes[0].delta_bytes == -800_000
        assert m.top_processes[0].delta_direction == "down"

    def test_top_n_limit(self, fake_psutil) -> None:
        fake_psutil.set_processes([
            _FakeProc(1, "p1", 1_000), _FakeProc(2, "p2", 2_000),
            _FakeProc(3, "p3", 3_000), _FakeProc(4, "p4", 4_000),
            _FakeProc(5, "p5", 5_000),
        ])
        c = MetricsCollector(Config(top_processes_count=3))
        m = c.collect()
        assert len(m.top_processes) == 3
        assert m.top_processes[0].used_bytes == 5_000
        assert m.process_count == 5

    def test_share_percent_computed(self, fake_psutil) -> None:
        fake_psutil.set_vm(_FakeVM(total=10_000_000_000, available=5_000_000_000,
                                    used=5_000_000_000, percent=50.0))
        fake_psutil.set_processes([_FakeProc(1, "x", 2_000_000_000)])
        c = MetricsCollector()
        m = c.collect()
        assert m.top_processes[0].share_percent == pytest.approx(20.0, abs=0.01)

    def test_dead_processes_evicted_from_state(self, fake_psutil) -> None:
        fake_psutil.set_processes([_FakeProc(1, "a", 1_000_000), _FakeProc(2, "b", 1_000_000)])
        c = MetricsCollector()
        c.collect()
        fake_psutil.set_processes([_FakeProc(1, "a", 1_000_000)])
        c.collect()
        assert 2 not in c._prev_mem

    def test_process_with_zero_rss_skipped(self, fake_psutil) -> None:
        fake_psutil.set_processes([_FakeProc(0, "idle", 0), _FakeProc(1, "real", 1_000_000)])
        c = MetricsCollector()
        m = c.collect()
        assert m.process_count == 1
        assert m.top_processes[0].name == "real"

    def test_prev_mem_bounded_by_ceiling(self, fake_psutil) -> None:
        procs = [_FakeProc(pid, f"p{pid}", 1_000 * pid) for pid in range(1, 301)]
        fake_psutil.set_processes(procs)
        c = MetricsCollector(Config(top_processes_count=8, process_state_ceiling=50))
        c.collect()
        assert len(c._prev_mem) <= 8


class TestLiveCollector:
    def test_live_collect_smoke(self) -> None:
        try:
            import psutil
        except ImportError:
            pytest.skip("psutil not installed")
        c = MetricsCollector()
        m = c.collect()
        assert m.total_bytes > 0
        assert 0.0 <= m.memory_percent <= 100.0
        assert 0.0 <= m.cpu_percent <= 100.0
        assert m.process_count >= 1

    def test_live_two_ticks_produce_delta(self) -> None:
        try:
            import psutil
        except ImportError:
            pytest.skip("psutil not installed")
        c = MetricsCollector()
        c.collect()
        m2 = c.collect()
        for p in m2.top_processes:
            assert isinstance(p.delta_bytes, int)
