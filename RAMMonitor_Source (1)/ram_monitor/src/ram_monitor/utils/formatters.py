"""Pure-Python value formatters.

These live outside the UI layer so that tests can verify them headlessly
and so that the same formatter can be reused for both on-screen text and
future export features (CSV, clipboard).
"""
from __future__ import annotations

from typing import Optional


def format_bytes(num_bytes: int, binary: bool = True) -> str:
    """Format an integer byte count as a human-readable string.

    Args:
        num_bytes: Byte count, may be negative (used for deltas).
        binary: If True (default), use 1024-based units (KiB, MiB, GiB).
                If False, use 1000-based units (KB, MB, GB) — matches the
                convention used by Windows Explorer.

    Returns:
        String like "2.15 GB" (negative → "-2.15 GB"). Always two decimals
        for consistency in the UI.
    """
    if num_bytes is None:
        return "—"

    sign = "-" if num_bytes < 0 else ""
    size = abs(num_bytes)
    base = 1024 if binary else 1000
    units = ["B", "KB", "MB", "GB", "TB", "PB"] if not binary else \
            ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]

    if size < base:
        return f"{sign}{size} {units[0]}"

    # Walk up the unit ladder.
    value: float = float(size)
    unit_idx = 0
    while value >= base and unit_idx < len(units) - 1:
        value /= base
        unit_idx += 1
    return f"{sign}{value:.2f} {units[unit_idx]}"


def format_percent(value: float, decimals: int = 1) -> str:
    """Format a 0–100 float as "42.3%"."""
    if value is None or value != value:  # NaN check
        return "—"
    return f"{value:.{decimals}f}%"


def format_uptime(seconds: float) -> str:
    """Format seconds-since-boot as "1d 02:34:56" (days only shown if > 0)."""
    if seconds is None or seconds < 0:
        return "—"
    secs = int(seconds)
    days, rem = divmod(secs, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    if days > 0:
        return f"{days}d {hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_frequency(mhz: Optional[float]) -> str:
    """Format a CPU frequency in MHz as "3.40 GHz" or "820 MHz"."""
    if mhz is None or mhz != mhz:  # NaN
        return "—"
    if mhz >= 1000:
        return f"{mhz / 1000:.2f} GHz"
    return f"{int(mhz)} MHz"


def format_delta(delta_bytes: int) -> tuple[str, str]:
    """Format a memory delta for the top-processes panel.

    Returns:
        (arrow_symbol, signed_text) e.g. ("↑", "+550 MB") or ("↓", "-128 MB").
        The caller decides coloring based on the sign.
    """
    if delta_bytes == 0:
        return ("—", "0 B")
    arrow = "↑" if delta_bytes > 0 else "↓"
    # Show the absolute magnitude but keep the sign prefix on the text.
    sign = "+" if delta_bytes > 0 else "-"
    return (arrow, f"{sign}{format_bytes(abs(delta_bytes), binary=False)}")
