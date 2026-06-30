"""Pure-psutil metrics collector.

This module is the *only* place in the codebase that imports `psutil`. The
UI layer depends on `MetricsCollector` (a plain Python class) and on the
frozen `SystemMetrics` dataclass — never on psutil directly. That boundary
is what lets us unit-test the collector headlessly on Linux even though the
shipped binary runs on Windows.

Performance notes:
* `collect()` makes **one** call to `psutil.process_iter` with an `attrs`
  list, so psutil batches the per-process syscalls internally on Windows
  (`EnumProcesses` + `GetProcessMemoryInfo`).
* `boot_time()` is cached on the instance — it changes only across reboots,
  and calling it on every tick is wasteful.
* The `prev_mem` dict is bounded by `process_state_ceiling` (256 by default).
  When it overflows, the smallest entries are evicted — this keeps memory
  flat over days of uptime.
"""
from __future__ import annotations

import time
from typing import Optional

import psutil

from ram_monitor.config import CONFIG, Config
from ram_monitor.core.models import ProcessInfo, SystemMetrics
from ram_monitor.utils.logger import get_logger

_log = get_logger()


class MetricsCollector:
    """Stateful collector. `collect()` returns one `SystemMetrics` snapshot.

    Statefulness is required for delta computation: each call needs to
    remember the previous tick's per-PID memory to compute the delta.
    """

    __slots__ = ("_config", "_boot_time", "_prev_mem")

    def __init__(self, config: Config = CONFIG) -> None:
        self._config: Config = config
        self._boot_time: Optional[float] = None
        self._prev_mem: dict[int, int] = {}

    # -- Public API -------------------------------------------------------

    def collect(self) -> SystemMetrics:
        """Collect a single system snapshot. Safe to call from a worker thread."""
        cfg = self._config

        # -- Memory & CPU --
        vm = psutil.virtual_memory()
        cpu_pct = psutil.cpu_percent(interval=None)
        try:
            freq = psutil.cpu_freq()
            freq_mhz: Optional[float] = freq.current if freq else None
        except (NotImplementedError, OSError):
            freq_mhz = None

        # -- Boot time (cached) --
        if self._boot_time is None:
            try:
                self._boot_time = psutil.boot_time()
            except (NotImplementedError, OSError):
                self._boot_time = time.time()

        uptime = max(0.0, time.time() - self._boot_time)

        # -- Processes --
        top_processes, process_count = self._collect_processes(vm.total)

        return SystemMetrics(
            total_bytes=vm.total,
            available_bytes=vm.available,
            used_bytes=vm.used,
            memory_percent=vm.percent,
            cpu_percent=cpu_pct,
            cpu_freq_mhz=freq_mhz,
            process_count=process_count,
            uptime_seconds=uptime,
            top_processes=top_processes,
        )

    # -- Internals --------------------------------------------------------

    def _collect_processes(
        self, total_memory: int
    ) -> tuple[tuple[ProcessInfo, ...], int]:
        cfg = self._config
        n_top = cfg.top_processes_count

        snapshots: list[tuple[int, str, int]] = []
        for proc in psutil.process_iter(attrs=["pid", "name", "memory_info"]):
            try:
                info = proc.info
                mem_info = info.get("memory_info")
                if mem_info is None:
                    continue
                rss = mem_info.rss
                if rss <= 0:
                    continue
                pid = info["pid"]
                name = info.get("name") or f"<pid {pid}>"
                snapshots.append((pid, name, rss))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        snapshots.sort(key=lambda t: t[2], reverse=True)
        top = snapshots[:n_top]
        total_count = len(snapshots)

        out: list[ProcessInfo] = []
        prev = self._prev_mem
        for pid, name, rss in top:
            delta = rss - prev.get(pid, rss)
            share = (rss / total_memory * 100.0) if total_memory > 0 else 0.0
            out.append(ProcessInfo(
                pid=pid, name=name, used_bytes=rss,
                share_percent=share, delta_bytes=delta,
            ))
            prev[pid] = rss

        live_pids = {p[0] for p in snapshots}
        stale = [pid for pid in prev if pid not in live_pids]
        for pid in stale:
            del prev[pid]
        if len(prev) > cfg.process_state_ceiling:
            sorted_items = sorted(prev.items(), key=lambda kv: kv[1], reverse=True)
            self._prev_mem = dict(sorted_items[:cfg.process_state_ceiling])

        return (tuple(out), total_count)

    # -- Lifecycle helpers -----------------------------------------------

    def reset(self) -> None:
        """Clear internal state. Useful for tests; not used by the worker."""
        self._prev_mem.clear()
        self._boot_time = None
