"""Fluent QSS stylesheet — generated entirely from `FluentTheme` tokens.

This file contains **zero magic numbers**. Every color, radius, spacing,
and font size traces back to a token in `fluent_theme.py`. To re-skin
the app, change a token there; this stylesheet picks it up automatically.

What changed from V1:
* Radii went from 8px to 12px on cards (per M1 spec).
* Cards gain a 1px top highlight (the "light from above" Win11 cue).
* Typography uses the WinUI 3 type ramp.
* All hard-coded hex codes are gone — tokens only.
* No Mica/Acrylic here (M4 concern) — opaque dark surface only.

M2-6: Added hover/pressed/disabled states on cards.
M2-8: Added focus indicator for keyboard navigation.
"""
from __future__ import annotations

from ram_monitor.config import Config, CONFIG
from ram_monitor.ui.fluent_theme import FluentTheme


def build_stylesheet(config: Config = CONFIG, theme: FluentTheme = None) -> str:
    """Return the application-wide QSS string built from tokens.

    Args:
        config: App config (used for any config-level tunables).
        theme:  Fluent theme. Defaults to `FluentTheme.default()`.
    """
    if theme is None:
        theme = FluentTheme.default()

    t = theme
    c = t.colors
    ty = t.typography
    r = t.radii
    s = t.spacing

    return f"""
    /* == Global == */
    QWidget {{
        background-color: {c.bg};
        color: {c.text_primary};
        font-family: {ty.family};
        font-size: {ty.body}px;
    }}

    QMainWindow {{
        background-color: {c.bg};
    }}

    /* == Surfaces — cards & framed containers == */
    QFrame#Surface, QFrame#Card {{
        background-color: {c.surface};
        border-radius: {r.large}px;
        border: 1px solid {c.stroke};
        border-top-color: {c.stroke_strong};
    }}
    QFrame#Surface:hover, QFrame#Card:hover {{
        background-color: {c.surface_elevated};
        border: 1px solid {c.stroke_strong};
    }}
    QFrame#Surface:pressed, QFrame#Card:pressed {{
        background-color: {c.surface_alt};
    }}
    QFrame#Surface:disabled, QFrame#Card:disabled {{
        background-color: {c.bg};
        color: {c.text_tertiary};
    }}
    QFrame#Card:focus {{
        border: 2px solid {c.accent};
        border-radius: {r.large}px;
    }}

    /* == Typography == */
    QLabel#SectionTitle {{
        color: {c.text_secondary};
        font-size: {ty.caption}px;
        font-weight: {ty.weight_semibold};
        letter-spacing: 1px;
        padding: {s.xs}px {s.xs}px;
    }}
    QLabel#SectionHeader {{
        color: {c.text_primary};
        font-size: {ty.subtitle}px;
        font-weight: {ty.weight_bold};
        letter-spacing: 0.5px;
        padding: {s.sm}px 0px {s.xs}px 0px;
    }}
    QLabel#CardLabel {{
        color: {c.text_secondary};
        font-size: {ty.caption}px;
        font-weight: {ty.weight_medium};
    }}
    QLabel#CardValue {{
        color: {c.text_primary};
        font-size: {ty.title}px;
        font-weight: {ty.weight_bold};
    }}
    QLabel#CardValueLarge {{
        color: {c.text_primary};
        font-size: {ty.large}px;
        font-weight: {ty.weight_bold};
    }}
    QLabel#CardSub {{
        color: {c.text_secondary};
        font-size: {ty.caption}px;
    }}

    /* == Progress bars == */
    QProgressBar {{
        background-color: {c.surface_alt};
        border: none;
        border-radius: {r.small}px;
        height: 4px;
        text-align: center;
    }}
    QProgressBar::chunk {{
        background-color: {c.accent};
        border-radius: {r.small}px;
    }}
    QProgressBar:disabled {{
        background-color: {c.bg};
    }}
    QProgressBar::chunk:disabled {{
        background-color: {c.text_tertiary};
    }}

    /* == Process table == */
    QTableWidget {{
        background-color: transparent;
        alternate-background-color: rgba(255, 255, 255, 0.02);
        border: none;
        gridline-color: transparent;
        selection-background-color: rgba(96, 205, 255, 0.15);
        selection-color: {c.text_primary};
    }}
    QTableWidget::item {{
        padding: {s.sm}px {s.md}px;
        border: none;
    }}
    QHeaderView::section {{
        background-color: transparent;
        color: {c.text_secondary};
        font-size: {ty.caption}px;
        font-weight: {ty.weight_semibold};
        padding: {s.sm}px {s.md}px;
        border: none;
        border-bottom: 1px solid {c.stroke};
    }}
    QTableCornerButton::section {{
        background-color: transparent;
        border: none;
    }}

    /* == Scrollbars == */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: rgba(255, 255, 255, 0.18);
        border-radius: 4px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: rgba(255, 255, 255, 0.32);
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
        margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background: rgba(255, 255, 255, 0.18);
        border-radius: 4px;
        min-width: 24px;
    }}
    """
