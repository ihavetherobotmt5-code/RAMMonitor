"""Unit tests for `ram_monitor.ui.fluent_theme`."""
from __future__ import annotations

import pytest

from ram_monitor.ui.fluent_theme import (
    FluentAnimation, FluentBreakpoints, FluentColors, FluentElevation,
    FluentRadii, FluentSpacing, FluentTheme, FluentTypography,
)


class TestFluentColors:
    def test_default_colors_present(self) -> None:
        c = FluentColors()
        for attr in ("bg", "surface", "surface_alt", "surface_elevated"):
            v = getattr(c, attr)
            assert isinstance(v, str) and v.startswith("#") and len(v) == 7

    def test_status_tiers(self) -> None:
        c = FluentColors()
        assert c.status_for(0.0) == c.status_good
        assert c.status_for(59.9) == c.status_good
        assert c.status_for(60.0) == c.status_warn
        assert c.status_for(84.9) == c.status_warn
        assert c.status_for(85.0) == c.status_bad
        assert c.status_for(100.0) == c.status_bad

    def test_status_thresholds_are_distinct(self) -> None:
        c = FluentColors()
        assert c.status_good != c.status_warn
        assert c.status_warn != c.status_bad
        assert c.status_good != c.status_bad


class TestFluentTypography:
    def test_type_ramp_is_monotonic(self) -> None:
        t = FluentTypography()
        sizes = [t.caption, t.body, t.subtitle, t.title, t.large]
        for a, b in zip(sizes, sizes[1:]):
            assert a < b

    def test_family_is_nonempty(self) -> None:
        t = FluentTypography()
        assert "Segoe" in t.family


class TestFluentRadii:
    def test_radii_match_winui3(self) -> None:
        r = FluentRadii()
        assert r.small == 4
        assert r.medium == 8
        assert r.large == 12
        assert r.small < r.medium < r.large


class TestFluentSpacing:
    def test_spacing_is_4_based(self) -> None:
        s = FluentSpacing()
        for attr in ("xs", "sm", "md", "lg", "xl", "xxl"):
            assert getattr(s, attr) % 4 == 0

    def test_spacing_is_monotonic(self) -> None:
        s = FluentSpacing()
        sizes = [s.xs, s.sm, s.md, s.lg, s.xl, s.xxl]
        for a, b in zip(sizes, sizes[1:]):
            assert a < b


class TestFluentElevation:
    def test_shadows_present(self) -> None:
        e = FluentElevation()
        for attr in ("depth_1", "depth_2", "depth_3"):
            v = getattr(e, attr)
            assert "rgba" in v

    def test_depth_increases(self) -> None:
        e = FluentElevation()
        def blur(s):
            return int(s.split(" ")[2].rstrip("px"))
        assert blur(e.depth_1) < blur(e.depth_2) < blur(e.depth_3)


class TestFluentAnimation:
    def test_durations_monotonic(self) -> None:
        a = FluentAnimation()
        assert a.fast < a.normal < a.slow

    def test_easing_names_are_qt_friendly(self) -> None:
        a = FluentAnimation()
        assert a.easing_smooth == "OutCubic"
        assert a.easing_energetic == "OutBack"


class TestFluentBreakpoints:
    def test_tier_classification(self) -> None:
        b = FluentBreakpoints()
        assert b.tier_for(1920) == "xxl"
        assert b.tier_for(1280) == "xl"
        assert b.tier_for(1279) == "lg"
        assert b.tier_for(900) == "lg"
        assert b.tier_for(899) == "md"
        assert b.tier_for(700) == "md"
        assert b.tier_for(699) == "sm"
        assert b.tier_for(400) == "sm"

    def test_breakpoint_boundaries_are_distinct(self) -> None:
        b = FluentBreakpoints()
        assert b.sm_max < b.md_max < b.lg_max < b.xxl_min


class TestFluentThemeAggregate:
    def test_default_theme_is_complete(self) -> None:
        t = FluentTheme.default()
        assert isinstance(t.colors, FluentColors)
        assert isinstance(t.typography, FluentTypography)
        assert isinstance(t.radii, FluentRadii)
        assert isinstance(t.spacing, FluentSpacing)
        assert isinstance(t.elevation, FluentElevation)
        assert isinstance(t.animation, FluentAnimation)
        assert isinstance(t.breakpoints, FluentBreakpoints)

    def test_default_is_singleton(self) -> None:
        assert FluentTheme.default() is FluentTheme.default()


class TestNoQtImports:
    def test_no_qt_symbols_in_module(self) -> None:
        import ram_monitor.ui.fluent_theme as ft
        forbidden = ("QFont", "QColor", "QPixmap", "QPainter", "PySide6", "PyQt")
        for sym in forbidden:
            assert not hasattr(ft, sym)

    def test_import_succeeds_without_display(self) -> None:
        import importlib
        import ram_monitor.ui.fluent_theme as ft
        importlib.reload(ft)
