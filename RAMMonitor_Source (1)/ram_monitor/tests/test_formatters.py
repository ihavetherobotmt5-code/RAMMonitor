"""Unit tests for `ram_monitor.utils.formatters`.

These are pure-Python functions with no Qt / psutil dependencies, so they
run instantly on any platform — including our Linux CI / build env.
"""
from __future__ import annotations

import math

import pytest

from ram_monitor.utils.formatters import (
    format_bytes,
    format_delta,
    format_frequency,
    format_percent,
    format_uptime,
)


# ── format_bytes ──────────────────────────────────────────────────────────

class TestFormatBytes:
    def test_zero_bytes(self) -> None:
        assert format_bytes(0) == "0 B"

    def test_bytes_under_1k(self) -> None:
        assert format_bytes(512) == "512 B"

    def test_kib_binary(self) -> None:
        # 1024 → 1.00 KiB
        assert format_bytes(1024, binary=True) == "1.00 KiB"

    def test_kb_decimal(self) -> None:
        # 1000 → 1.00 KB (Windows Explorer convention)
        assert format_bytes(1000, binary=False) == "1.00 KB"

    def test_megabytes(self) -> None:
        # 2.15 GB (decimal) = 2_150_000_000 bytes
        out = format_bytes(2_150_000_000, binary=False)
        assert out == "2.15 GB"

    def test_gib_binary(self) -> None:
        # 1 GiB = 1024^3 = 1_073_741_824 bytes → "1.00 GiB"
        assert format_bytes(1_073_741_824, binary=True) == "1.00 GiB"

    def test_negative_delta(self) -> None:
        # Negative bytes — used for memory deltas.
        out = format_bytes(-550 * 1_000_000, binary=False)
        assert out.startswith("-") and "MB" in out

    def test_none_returns_dash(self) -> None:
        assert format_bytes(None) == "—"


# ── format_percent ────────────────────────────────────────────────────────

class TestFormatPercent:
    def test_basic(self) -> None:
        assert format_percent(42.345) == "42.3%"

    def test_zero(self) -> None:
        assert format_percent(0.0) == "0.0%"

    def test_hundred(self) -> None:
        assert format_percent(100.0) == "100.0%"

    def test_decimals_param(self) -> None:
        assert format_percent(42.3456, decimals=2) == "42.35%"

    def test_nan_returns_dash(self) -> None:
        assert format_percent(float("nan")) == "—"


# ── format_uptime ─────────────────────────────────────────────────────────

class TestFormatUptime:
    def test_zero(self) -> None:
        assert format_uptime(0) == "00:00:00"

    def test_seconds_only(self) -> None:
        assert format_uptime(42) == "00:00:42"

    def test_minutes(self) -> None:
        assert format_uptime(5 * 60 + 3) == "00:05:03"

    def test_hours(self) -> None:
        assert format_uptime(2 * 3600 + 3 * 60 + 4) == "02:03:04"

    def test_days(self) -> None:
        # 1 day + 2h + 3m + 4s
        secs = 86400 + 2 * 3600 + 3 * 60 + 4
        assert format_uptime(secs) == "1d 02:03:04"

    def test_negative_returns_dash(self) -> None:
        assert format_uptime(-1) == "—"


# ── format_frequency ──────────────────────────────────────────────────────

class TestFormatFrequency:
    def test_mhz_under_1k(self) -> None:
        assert format_frequency(800) == "800 MHz"

    def test_ghz(self) -> None:
        # 3400 MHz → "3.40 GHz"
        assert format_frequency(3400) == "3.40 GHz"

    def test_none(self) -> None:
        assert format_frequency(None) == "—"


# ── format_delta ──────────────────────────────────────────────────────────

class TestFormatDelta:
    def test_zero(self) -> None:
        arrow, text = format_delta(0)
        assert arrow == "—"
        assert text == "0 B"

    def test_positive(self) -> None:
        arrow, text = format_delta(550 * 1_000_000)  # +550 MB
        assert arrow == "↑"
        assert text.startswith("+") and "MB" in text

    def test_negative(self) -> None:
        arrow, text = format_delta(-128 * 1_000_000)  # -128 MB
        assert arrow == "↓"
        assert text.startswith("-") and "MB" in text
