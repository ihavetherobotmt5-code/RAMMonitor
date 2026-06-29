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


# -- Color helpers -------------------------------------------------------

def _hex(h: str) -> Tuple[int, int, int]:
    """Parse '#RRGGBB' -> (r, g, b). Used by the shadow generator."""
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _rgba(rgb: Tuple[int, int, int], alpha: float) -> str:
    """Return a CSS rgba() string. Alpha is 0.0-1.0."""
    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha:.3f})"


# -- Token groups -------------------------------------------------------

@dataclass(frozen=True)
class FluentColors:
    """4-tier surface elevation + accent ramp + semantic colors.

    The four surfaces (bg / surface / surface_alt / surface_elevated) form
    a 4-step depth scale. Elevation increases left-to-right; widgets further
    "above" the background use higher surfaces.
    """

    # 4-step surface scale (depth increases)
    bg:               str = "#1A1A1A"   # app background -- darkened for more card contrast
    surface:          str = "#2D2D2D"   # cards -- lightened for elevation
    surface_alt:      str = "#353535"   # inputs, headers
    surface_elevated: str = "#3D3D3D"   # popovers, hovers

    # Text
    text_primary:     str = "#FFFFFF"
    text_secondary:   str = "#B0B0B0"
    text_tertiary:    str = "#777777"

    # Accent ramp -- Windows 11 accent blue at 3 intensities
    accent:           str = "#60CDFF"   # base
    accent_strong:    str = "#38B6FF"   # hover / pressed
    accent_subtle:    str = "#1F5A7A"   # backgrounds, fills at low alpha

    # Semantic -- RAM / CPU
    ram:              str = "#60CDFF"
    cpu:              str = "#FFB85C"   # M2-6: amber -- contrasting hue

    # Status tier -- used by smart-color selection on meters
    status_good:      str = "#73C991"   # < 60% usage
    status_warn:      str = "#F5C147"   # 60-85%
    status_bad:       str = "#FF6B6B"   # > 85%

    # Delta (per-process memory change)
    delta_up:         str = "#FF6B6B"
    delta_down:       str = "#73C991"
    delta_flat:       str = "#777777"

    # Stroke / divider
    stroke:           str = "rgba(255, 255, 255, 0.08)"
    stroke_strong:    str = "rgba(255, 255, 255, 0.18)"

    def status_for(self, percent: float) -> str:
        """Return the semantic color for a 0-100 usage value.

        Used by `StatCard` to color its meter by tier -- green under 60%,
        amber 60-85%, red above. The thresholds are conservative so the
        app doesn't cry wolf on a normal busy machine.
        """
        if percent < 60.0:
            return self.status_good
        if percent < 85.0:
            return self.status_warn
        return self.status_bad


@dataclass(frozen=True)
class FluentTypography:
    """WinUI 3 type ramp. Sizes in px (Qt interprets as 1:1 at default DPI)."""

    caption:     int = 11   # axis labels, hints
    body:        int = 13   # default text
    subtitle:    int = 14   # section headers
    title:       int = 28   # card values -- bumped for commercial-grade hierarchy
    large:       int = 32   # card values (large) -- bumped to maintain ramp

    # Font family stack -- first available wins.
    family:      str = '"Segoe UI Variable", "Segoe UI", "Inter", "Arial"'

    # Weights
    weight_regular:  int = 400
    weight_medium:   int = 500
    weight_semibold: int = 600
    weight_bold:     int = 700


@dataclass(frozen=True)
class FluentRadii:
    """Corner radii in px. Matches WinUI 3 control guidelines."""

    none:   int = 0
    small:  int = 4    # checkboxes, small chips
    medium: int = 8    # buttons, inputs
    large:  int = 12   # cards, surfaces


@dataclass(frozen=True)
class FluentSpacing:
    """4-based spacing scale. Use these instead of ad-hoc margins."""

    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 24
    xxl: int = 32


@dataclass(frozen=True)
class FluentElevation:
    """Shadow tokens. Each is a CSS box-shadow string for QSS consumption.

    Shadows on frequently-updated widgets are painted from a CACHED QPixmap
    in `paintEvent`, NOT from `QGraphicsDropShadowEffect` (which would
    re-rasterize on every repaint and tank the CPU budget).
    """

    # depth-1: default card -- barely-there shadow
    depth_1: str = "0 2px 8px rgba(0, 0, 0, 0.18)"
    # depth-2: hover / focused card
    depth_2: str = "0 4px 16px rgba(0, 0, 0, 0.28)"
    # depth-3: popovers, modal-like
    depth_3: str = "0 8px 32px rgba(0, 0, 0, 0.38)"


@dataclass(frozen=True)
class FluentAnimation:
    """Durations (ms) and easing curves. Qt-friendly names where applicable."""

    fast:     int = 120    # hover, focus
    normal:   int = 220    # value transitions (matches Config.animation_duration_ms)
    slow:     int = 380    # panel slide-ins (M4)

    # Easing -- Qt QEasingCurve enum names. Used by animations in stats_cards.
    easing_smooth:  str = "OutCubic"        # default -- natural deceleration
    easing_energetic: str = "OutBack"        # subtle overshoot for value pops


@dataclass(frozen=True)
class FluentBreakpoints:
    """Responsive reflow widths (px). See `responsive_grid.py`.

    The 5 breakpoints produce 5 layouts:
        * xxl  (>= 2560): 4-card row, charts side-by-side, content max-width
        * xl   (>= 1280): 4-card row, charts side-by-side
        * lg   (900-1279): 4-card row, charts side-by-side (tighter)
        * md   (700-899):  2x2 cards, charts stacked
        * sm   (< 700):    single column, everything stacked
    """

    sm_max: int = 699      # below this -> single column
    md_max: int = 899      # below this -> 2-col
    lg_max: int = 1279     # below this -> 4-col tight
    xxl_min: int = 2560    # at/above this -> content max-width constraint

    #: Maximum content width on ultra-wide displays (px).
    #: Prevents cards from stretching absurdly wide on 3440px monitors.
    #: Content is centered within the window when it exceeds this width.
    content_max_width: int = 1600

    def tier_for(self, width: int) -> str:
        """Return 'xxl' | 'xl' | 'lg' | 'md' | 'sm' for a given window width."""
        if width >= self.xxl_min:
            return "xxl"
        if width >= self.lg_max + 1:
            return "xl"
        if width >= self.md_max + 1:
            return "lg"
        if width >= self.sm_max + 1:
            return "md"
        return "sm"


# -- Aggregate theme -----------------------------------------------------

@dataclass(frozen=True)
class FluentTheme:
    """Aggregate of all token groups. Pass this around -- never individual values."""

    colors:      FluentColors      = field(default_factory=FluentColors)
    typography:  FluentTypography  = field(default_factory=FluentTypography)
    radii:       FluentRadii       = field(default_factory=FluentRadii)
    spacing:     FluentSpacing     = field(default_factory=FluentSpacing)
    elevation:   FluentElevation   = field(default_factory=FluentElevation)
    animation:   FluentAnimation   = field(default_factory=FluentAnimation)
    breakpoints: FluentBreakpoints = field(default_factory=FluentBreakpoints)

    @classmethod
    def default(cls) -> "FluentTheme":
        """The single shared theme instance."""
        return _DEFAULT_THEME


# Module-level singleton -- all widgets import this via `FluentTheme.default()`.
_DEFAULT_THEME: FluentTheme = FluentTheme()
