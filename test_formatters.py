"""Unit tests for `ram_monitor.utils.formatters`."""
from __future__ import annotations

import pytest

from ram_monitor.utils.formatters import (
    format_bytes,
    format_delta,
    format_frequency,
    format_percent,
    format_uptime,
)


class TestFormatBytes:
    def test_zero_bytes(self) -> None:
        assert format_bytes(0) == "0 B"

    def test_bytes_under_1k(self) -> None:
        assert format_bytes(512) == "512 B"

    def test_kib_binary(self) -> None:
        assert format_bytes(1024, binary=True) == "1.00 KiB"

    def test_kb_decimal(self) -> None:
        assert format_bytes(1000, binary=False) == "1.00 KB"

    def test_megabytes(self) -> None:
        out = format_bytes(2_150_000_000, binary=False)
        assert out == "2.15 GB"

    def test_gib_binary(self) -> None:
        assert format_bytes(1_073_741_824, binary=True) == "1.00 GiB"

    def test_negative_delta(self) -> None:
        out = format_bytes(-550 * 1_000_000, binary=False)
        assert out.startswith("-") and "MB" in out

    def test_none_returns_dash(self) -> None:
        assert format_bytes(None) == "\u2014"


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
        assert format_percent(float("nan")) == "\u2014"


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
        secs = 86400 + 2 * 3600 + 3 * 60 + 4
        assert format_uptime(secs) == "1d 02:03:04"

    def test_negative_returns_dash(self) -> None:
        assert format_uptime(-1) == "\u2014"


class TestFormatFrequency:
    def test_mhz_under_1k(self) -> None:
        assert format_frequency(800) == "800 MHz"

    def test_ghz(self) -> None:
        assert format_frequency(3400) == "3.40 GHz"

    def test_none(self) -> None:
        assert format_frequency(None) == "\u2014"


class TestFormatDelta:
    def test_zero(self) -> None:
        arrow, text = format_delta(0)
        assert arrow == "\u2014"
        assert text == "0 B"

    def test_positive(self) -> None:
        arrow, text = format_delta(550 * 1_000_000)
        assert arrow == "\u2191"
        assert text.startswith("+") and "MB" in text

    def test_negative(self) -> None:
        arrow, text = format_delta(-128 * 1_000_000)
        assert arrow == "\u2193"
        assert text.startswith("-") and "MB" in text
