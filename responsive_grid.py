"""ResponsiveGridLayout — reflows on resize, never on tick.

Implementation strategy: a SINGLE QGridLayout lives for the host's lifetime.
On tier change, we update the column-span of each widget (which is cheap)
rather than tearing down and rebuilding the layout tree. This avoids the
classic Qt crash of "deleting a layout while its widgets are still alive"
and keeps reflow O(widgets), not O(layout-tree).

Spec (per M1 plan section 5):
    * xxl  (>= 2560 px): 4 cards in a row, charts side-by-side, content max-width
    * xl   (>= 1280 px): 4 cards in a row, charts side-by-side
    * lg   (900-1279  ): 4 cards in a row, charts side-by-side (tighter)
    * md   (700-899   ): 2x2 cards, charts stacked
    * sm   (< 700     ): single column, everything stacked

Recompute triggers:
    * Window resize (caught via eventFilter on the host)
    * DPI change (rare; handled by re-running the same reflow logic)

Recompute NON-triggers (constraint #3):
    * Monitoring tick — never reflows during a tick
    * Value updates — only `set_value` / `push` calls, no layout change
"""
from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QSizePolicy,
    QWidget,
)

from ram_monitor.ui.fluent_theme import FluentTheme


class ResponsiveGridLayout(QObject):
    """A layout manager that reflows on breakpoint changes only.

    Owns a single QGridLayout on the host widget. On tier change, only the
    column-span of each widget is updated — no layout teardown, no widget
    reparenting. This is the safest possible reflow strategy in Qt.
    """

    def __init__(
        self,
        host: QWidget,
        theme: Optional[FluentTheme] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent or host)
        self._host = host
        self._theme = theme or FluentTheme.default()
        self._breakpoints = self._theme.breakpoints

        self._cards: List[QWidget] = []
        self._charts: List[QWidget] = []
        self._section_titles: List[QWidget] = []  # M2-4: section headers inserted between groups
        self._process_panel: Optional[QWidget] = None
        self._reserved: Optional[QWidget] = None

        self._current_tier: Optional[str] = None  # forces first-time build

        # Single grid layout — lives for the host's lifetime, never deleted.
        # M2-4: Use theme tokens for spacing instead of hardcoded numbers.
        s = self._theme.spacing
        self._grid = QGridLayout(host)
        self._grid.setContentsMargins(s.xl, s.xl, s.xl, s.xl)  # 24px outer margin
        self._grid.setSpacing(s.lg)  # 16px inter-element spacing

        # Listen to host resize events.
        host.installEventFilter(self)

    # -- Public API -------------------------------------------------------

    def add_card(self, w: QWidget) -> None:
        """Register a stat card. Cards reflow as a group."""
        w.setParent(self._host)
        self._cards.append(w)
        self.relayout(force=True)

    def add_section_title(self, w: QWidget) -> None:
        """Register a section title label. M2-4: creates visual hierarchy.

        Section titles are inserted between card/chart/panel groups.
        They span the full width and are created once (static text).
        """
        w.setParent(self._host)
        self._section_titles.append(w)
        self.relayout(force=True)

    def add_chart(self, w: QWidget) -> None:
        """Register a chart. Charts come in pairs and reflow together."""
        w.setParent(self._host)
        self._charts.append(w)
        self.relayout(force=True)

    def set_process_panel(self, w: QWidget) -> None:
        """Register the bottom process panel. Singular."""
        w.setParent(self._host)
        self._process_panel = w
        self.relayout(force=True)

    def set_reserved(self, w: QWidget) -> None:
        """Register a reserved cell (M3 placeholder). May be None."""
        if w is not None:
            w.setParent(self._host)
        self._reserved = w
        self.relayout(force=True)

    def relayout(self, force: bool = False) -> None:
        """Re-arrange widgets if the breakpoint tier changed (or `force`)."""
        width = self._host.width()
        new_tier = self._breakpoints.tier_for(width)

        if not force and new_tier == self._current_tier:
            return  # no change — do nothing, save CPU

        self._current_tier = new_tier
        self._apply_arrangement(new_tier)

    @property
    def current_tier(self) -> Optional[str]:
        return self._current_tier

    # -- Event filter: catch resize ---------------------------------------

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        host = getattr(self, "_host", None)
        if host is None or obj is not host:
            return super().eventFilter(obj, event)
        if event.type() == QEvent.Type.Resize:
            self.relayout(force=False)
        return super().eventFilter(obj, event)

    # -- Layout arrangement -----------------------------------------------

    def _apply_arrangement(self, tier: str) -> None:
        """Place every widget into the grid using the tier's column count.

        M2-4: Section titles are inserted between card/chart/panel groups.
        They span the full width of the grid (all columns).

        Layout order (top to bottom):
            [section_title[0]]  "Overview"
            [cards]             4 cards (or 2x2, or 1-col)
            [section_title[1]]  "Performance History"
            [charts]            2 charts side-by-side (or stacked)
            [section_title[2]]  "Top Processes"
            [process_panel]     full-width table
        """
        # Clear the grid by removing all items (widgets stay alive).
        while self._grid.count():
            item = self._grid.takeAt(0)

        cards_per_row = self._cards_per_row(tier)
        charts_per_row = self._charts_per_row(tier)
        full_span = max(cards_per_row, charts_per_row)

        row_cursor = 0
        title_idx = 0

        # -- Section title: "Overview" (before cards) --
        if title_idx < len(self._section_titles):
            self._grid.addWidget(self._section_titles[title_idx], row_cursor, 0, 1, full_span)
            row_cursor += 1
            title_idx += 1

        # -- Cards --
        for i, card in enumerate(self._cards):
            r = row_cursor + i // cards_per_row
            c = i % cards_per_row
            card.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
            card.setMinimumHeight(90)
            self._grid.addWidget(card, r, c, 1, 1)
        rows_used = (len(self._cards) + cards_per_row - 1) // cards_per_row if self._cards else 0
        row_cursor += rows_used

        # -- Section title: "Performance History" (before charts) --
        if title_idx < len(self._section_titles):
            self._grid.addWidget(self._section_titles[title_idx], row_cursor, 0, 1, full_span)
            row_cursor += 1
            title_idx += 1

        # -- Charts --
        if self._charts:
            cols = charts_per_row
            for i, chart in enumerate(self._charts):
                r = row_cursor + i // cols
                c = i % cols
                span = 1
                if cols == 2 and i == len(self._charts) - 1 and i % cols == 0:
                    span = 2
                chart.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Expanding,
                )
                chart.setMinimumHeight(240)
                self._grid.addWidget(chart, r, c, 1, span)
            chart_rows = (len(self._charts) + cols - 1) // cols
            row_cursor += chart_rows
            self._grid.setRowStretch(row_cursor - 1, 1)

        # -- Reserved cell (xxl / xl / lg only) --
        if self._reserved is not None and tier in ("xxl", "xl", "lg"):
            self._grid.addWidget(self._reserved, row_cursor, 0, 1, cards_per_row)
            row_cursor += 1

        # -- Section title: "Top Processes" (before process panel) --
        if title_idx < len(self._section_titles):
            self._grid.addWidget(self._section_titles[title_idx], row_cursor, 0, 1, full_span)
            row_cursor += 1
            title_idx += 1

        # -- Process panel (spans full width) --
        if self._process_panel is not None:
            self._process_panel.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Preferred,
            )
            self._grid.addWidget(self._process_panel, row_cursor, 0, 1, full_span)
            self._grid.setRowStretch(row_cursor, 1)
            row_cursor += 1

        # Reset stretch on non-content rows.
        for r in range(row_cursor):
            if r != row_cursor - 1 and (self._charts and r == row_cursor - 2):
                continue
            if r < (len(self._cards) + cards_per_row - 1) // cards_per_row if self._cards else 0:
                self._grid.setRowStretch(r, 0)

    # -- Tier -> column-count mapping -------------------------------------

    @staticmethod
    def _cards_per_row(tier: str) -> int:
        return {"xxl": 4, "xl": 4, "lg": 4, "md": 2, "sm": 1}[tier]

    @staticmethod
    def _charts_per_row(tier: str) -> int:
        return {"xxl": 2, "xl": 2, "lg": 2, "md": 1, "sm": 1}[tier]
