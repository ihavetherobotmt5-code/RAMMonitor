"""Windows 11 dark-mode QSS stylesheet.

The stylesheet is generated from `Config` so all color tuning lives in one
place. Window chrome (rounded corners, accent title bar) is delegated to
Windows' native DWM API via `app.py` on Windows 11; the QSS below styles
the in-window surface only.

Design language:
* Soft 8 px corner radius on all surfaces.
* No flat-black backgrounds — `#1F1F1F` reads as "Windows 11 dark" without
  the harsh contrast of pure black.
* Single accent color (`#60CDFF`) reused for highlights, progress bars,
  and chart series. Visual unity > decoration.
"""
from __future__ import annotations

from ram_monitor.config import Config, CONFIG


def build_stylesheet(config: Config = CONFIG) -> str:
    """Return the application-wide QSS string built from `config`."""
    c = config
    return f"""
    QWidget {{
        background-color: {c.color_bg};
        color: {c.color_text_primary};
        font-family: "Segoe UI Variable", "Segoe UI", "Inter", "Arial";
        font-size: 13px;
    }}

    QMainWindow {{
        background-color: {c.color_bg};
    }}

    /* ── Surfaces ─────────────────────────────────────────────── */
    QFrame#Surface, QFrame#Card {{
        background-color: {c.color_surface};
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.04);
    }}

    /* ── Headings ─────────────────────────────────────────────── */
    QLabel#SectionTitle {{
        color: {c.color_text_secondary};
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1px;
        padding: 4px 2px;
    }}
    QLabel#CardLabel {{
        color: {c.color_text_secondary};
        font-size: 11px;
        font-weight: 500;
    }}
    QLabel#CardValue {{
        color: {c.color_text_primary};
        font-size: 22px;
        font-weight: 600;
    }}
    QLabel#CardSub {{
        color: {c.color_text_secondary};
        font-size: 11px;
    }}

    /* ── Progress bars (used as thin meters on cards) ─────────── */
    QProgressBar {{
        background-color: {c.color_surface_alt};
        border: none;
        border-radius: 3px;
        height: 4px;
        text-align: center;
    }}
    QProgressBar::chunk {{
        background-color: {c.color_accent};
        border-radius: 3px;
    }}

    /* ── Process table ────────────────────────────────────────── */
    QTableWidget {{
        background-color: transparent;
        alternate-background-color: rgba(255, 255, 255, 0.02);
        border: none;
        gridline-color: transparent;
        selection-background-color: rgba(96, 205, 255, 0.15);
        selection-color: {c.color_text_primary};
    }}
    QTableWidget::item {{
        padding: 6px 8px;
        border: none;
    }}
    QHeaderView::section {{
        background-color: transparent;
        color: {c.color_text_secondary};
        font-size: 11px;
        font-weight: 600;
        padding: 6px 8px;
        border: none;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }}
    QTableCornerButton::section {{
        background-color: transparent;
        border: none;
    }}

    /* ── Scrollbars — Windows 11 thin overlay style ───────────── */
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
