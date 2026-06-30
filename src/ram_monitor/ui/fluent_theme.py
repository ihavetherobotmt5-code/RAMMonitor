"""Fluent Design tokens — the single source of truth for visual decisions.

This module is **pure data**: no Qt imports, no PySide6. That makes it:

* Headless-testable on any platform (the tests in `test_fluent_theme.py`
  run without a display).
* Importable by the `core` layer if ever needed (no risk of pulling Qt
  into the monitoring engine).
* Easy to override — swap one token, the whole app re-skins.

Token groups:
    * Colors      — 4-tier surface elevation + accent ramp + semantic colors
    * Typography  — WinUI 3 type ramp (Caption -> Body -> Subtitle -> Title -> Large)
    * Radii       — 4 / 8 / 12 px (controls / cards / surfaces)
    * Spacing     — 4-based spacing scale (xs / sm / md / lg / xl / xxl)
    * Elevation   — shadow tokens (depth-1 / depth-2 / depth-3)
    * Animation   — durations + easings
    * Breakpoints — responsive reflow widths

Every widget reads from `FluentTheme.default()`. **No magic numbers** in
widget code — if a number appears in a widget, it must trace back to a
token defined here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


def _hex(h: str) -> Tuple[int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _rgba(rgb: Tuple[int, int, int], alpha: float) -> str:
    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha:.3f})"


@dataclass(frozen=True)
class FluentColors:
    bg:               str = "#1A1A1A"
    surface:          str = "#2D2D2D"
    surface_alt:      str = "#353535"
    surface_elevated: str = "#3D3D3D"
    text_primary:     str = "#FFFFFF"
    text_secondary:   str = "#B0B0B0"
    text_tertiary:    str = "#777777"
    accent:           str = "#60CDFF"
    accent_strong:    str = "#38B6FF"
    accent_subtle:    str = "#1F5A7A"
    ram:              str = "#60CDFF"
    cpu:              str = "#FFB85C"
    status_good:      str = "#73C991"
    status_warn:      str = "#F5C147"
    status_bad:       str = "#FF6B6B"
    delta_up:         str = "#FF6B6B"
    delta_down:       str = "#73C991"
    delta_flat:       str = "#777777"
    stroke:           str = "rgba(255, 255, 255, 0.08)"
    stroke_strong:    str = "rgba(255, 255, 255, 0.18)"

    def status_for(self, percent: float) -> str:
        if percent < 60.0:
            return self.status_good
        if percent < 85.0:
            return self.status_warn
        return self.status_bad


@dataclass(frozen=True)
class FluentTypography:
    caption:     int = 11
    body:        int = 13
    subtitle:    int = 14
    title:       int = 28
    large:       int = 32
    family:      str = '"Segoe UI Variable", "Segoe UI", "Inter", "Arial"'
    weight_regular:  int = 400
    weight_medium:   int = 500
    weight_semibold: int = 600
    weight_bold:     int = 700


@dataclass(frozen=True)
class FluentRadii:
    none:   int = 0
    small:  int = 4
    medium: int = 8
    large:  int = 12


@dataclass(frozen=True)
class FluentSpacing:
    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 24
    xxl: int = 32


@dataclass(frozen=True)
class FluentElevation:
    depth_1: str = "0 2px 8px rgba(0, 0, 0, 0.18)"
    depth_2: str = "0 4px 16px rgba(0, 0, 0, 0.28)"
    depth_3: str = "0 8px 32px rgba(0, 0, 0, 0.38)"


@dataclass(frozen=True)
class FluentAnimation:
    fast:     int = 120
    normal:   int = 220
    slow:     int = 380
    easing_smooth:  str = "OutCubic"
    easing_energetic: str = "OutBack"


@dataclass(frozen=True)
class FluentBreakpoints:
    sm_max: int = 699
    md_max: int = 899
    lg_max: int = 1279
    xxl_min: int = 2560
    content_max_width: int = 1600

    def tier_for(self, width: int) -> str:
        if width >= self.xxl_min:
            return "xxl"
        if width >= self.lg_max + 1:
            return "xl"
        if width >= self.md_max + 1:
            return "lg"
        if width >= self.sm_max + 1:
            return "md"
        return "sm"


@dataclass(frozen=True)
class FluentTheme:
    colors:      FluentColors      = field(default_factory=FluentColors)
    typography:  FluentTypography  = field(default_factory=FluentTypography)
    radii:       FluentRadii       = field(default_factory=FluentRadii)
    spacing:     FluentSpacing     = field(default_factory=FluentSpacing)
    elevation:   FluentElevation   = field(default_factory=FluentElevation)
    animation:   FluentAnimation   = field(default_factory=FluentAnimation)
    breakpoints: FluentBreakpoints = field(default_factory=FluentBreakpoints)

    @classmethod
    def default(cls) -> "FluentTheme":
        return _DEFAULT_THEME


_DEFAULT_THEME: FluentTheme = FluentTheme()
