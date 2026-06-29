"""Application-wide tunables.

All magic numbers live here so that performance and visual decisions can be
audited and overridden in a single place. Values are tuned for the < 60 MB /
< 1% CPU budget described in ROADMAP.md.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Frozen config container. mutate by replacing the instance, never in place."""

    # ── Polling ────────────────────────────────────────────────────────────
    #: Polling interval in seconds. 1.5 s balances responsiveness with the
    #: < 1% CPU budget — see ROADMAP §2.1 for the empirical rationale.
    poll_interval_seconds: float = 1.5

    # ── History buffers ────────────────────────────────────────────────────
    #: Number of samples kept in each chart's rolling buffer.
    #: 60 samples × 1.5 s = 90 s of visible history.
    history_length: int = 60

    #: Maximum number of processes shown in the top-processes panel.
    top_processes_count: int = 8

    #: Maximum number of entries kept in the collector's `prev_mem` dict.
    #: Bounded to prevent unbounded growth over long uptimes.
    process_state_ceiling: int = 256

    # ── UI / Visual ────────────────────────────────────────────────────────
    window_title: str = "RAM Monitor"
    window_width: int = 920
    window_height: int = 640

    # Windows 11 dark palette (hex).
    color_bg: str = "#1F1F1F"
    color_surface: str = "#2B2B2B"
    color_surface_alt: str = "#333333"
    color_text_primary: str = "#FFFFFF"
    color_text_secondary: str = "#B0B0B0"
    color_accent: str = "#60CDFF"        # Windows 11 accent blue
    color_ram: str = "#60CDFF"
    color_cpu: str = "#9CDCFE"
    color_delta_up: str = "#FF6B6B"      # grew — neutral red, not alarm
    color_delta_down: str = "#73C991"    # shrank — green
    color_delta_flat: str = "#777777"

    #: Card fade-in / value-transition duration, ms.
    animation_duration_ms: int = 220

    # ── Process table ──────────────────────────────────────────────────────
    #: Column headers for the top-processes panel. Order matters.
    process_columns: tuple[str, ...] = (
        "Process", "Memory", "Share", "Δ since last tick",
    )


#: The single config instance consumed application-wide.
CONFIG: Config = Config()
