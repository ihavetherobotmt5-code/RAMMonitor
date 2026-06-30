"""Immutable data models shared between core and UI layers.

These are `@dataclass(frozen=True, slots=True)` for two reasons:

* **frozen** — the metrics emitted by the worker are conceptually a snapshot
  in time; mutating them mid-flight would be a bug. Frozen makes that intent
  explicit and prevents accidental mutation in UI slots.
* **slots** — eliminates the per-instance `__dict__`, shaving ~40% off the
  memory footprint of each `ProcessInfo`. At 8 top processes per tick, that's
  negligible, but at 256 entries in `prev_mem` it adds up.

The models intentionally contain **no Qt types** so the core layer can be
imported and unit-tested headlessly on any platform.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True, slots=True)
class ProcessInfo:
    """A single process snapshot, with delta vs. the previous tick.

    `delta_bytes` is signed: positive = the process grew, negative = shrank.
    The UI maps this to color + arrow; the core layer is color-blind.
    """

    pid: int
    name: str
    used_bytes: int
    share_percent: float
    delta_bytes: int = 0

    @property
    def delta_direction(self) -> str:
        """One of 'up', 'down', 'flat' — used by UI for color/arrow selection."""
        if self.delta_bytes > 0:
            return "up"
        if self.delta_bytes < 0:
            return "down"
        return "flat"


@dataclass(frozen=True, slots=True)
class SystemMetrics:
    """Complete system snapshot for a single polling tick.

    All byte fields are in **bytes** (not KB/MB) — formatting belongs to the
    UI layer (`utils.formatters`). Time fields are in **seconds**.
    """

    # -- Memory --
    total_bytes: int
    available_bytes: int
    used_bytes: int
    memory_percent: float

    # -- CPU --
    cpu_percent: float
    cpu_freq_mhz: Optional[float] = None

    # -- System --
    process_count: int = 0
    uptime_seconds: float = 0.0

    # -- Top processes, pre-sorted descending by `used_bytes` --
    top_processes: tuple[ProcessInfo, ...] = field(default_factory=tuple)

    @property
    def memory_percent_rounded(self) -> float:
        """Convenience accessor — single source of truth for rounding."""
        return round(self.memory_percent, 1)
