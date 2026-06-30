"""ResponsiveGridLayout — reflows on resize, never on tick."""
from __future__ import annotations
from typing import List, Optional
from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import QGridLayout, QSizePolicy, QWidget
from ram_monitor.ui.fluent_theme import FluentTheme

class ResponsiveGridLayout(QObject):
    def __init__(self, host: QWidget, theme: Optional[FluentTheme] = None, parent: Optional[QObject] = None) -> None:
        super().__init__(parent or host)
        self._host = host
        self._theme = theme or FluentTheme.default()
        self._breakpoints = self._theme.breakpoints
        self._cards: List[QWidget] = []
        self._charts: List[QWidget] = []
        self._section_titles: List[QWidget] = []
        self._process_panel: Optional[QWidget] = None
        self._reserved: Optional[QWidget] = None
        self._current_tier: Optional[str] = None
        s = self._theme.spacing
        self._grid = QGridLayout(host)
        self._grid.setContentsMargins(s.xl, s.xl, s.xl, s.xl)
        self._grid.setSpacing(s.lg)
        host.installEventFilter(self)

    def add_card(self, w: QWidget) -> None:
        w.setParent(self._host); self._cards.append(w); self.relayout(force=True)
    def add_section_title(self, w: QWidget) -> None:
        w.setParent(self._host); self._section_titles.append(w); self.relayout(force=True)
    def add_chart(self, w: QWidget) -> None:
        w.setParent(self._host); self._charts.append(w); self.relayout(force=True)
    def set_process_panel(self, w: QWidget) -> None:
        w.setParent(self._host); self._process_panel = w; self.relayout(force=True)
    def set_reserved(self, w: QWidget) -> None:
        if w is not None: w.setParent(self._host)
        self._reserved = w; self.relayout(force=True)
    def relayout(self, force: bool = False) -> None:
        width = self._host.width()
        new_tier = self._breakpoints.tier_for(width)
        if not force and new_tier == self._current_tier: return
        self._current_tier = new_tier
        self._apply_arrangement(new_tier)
    @property
    def current_tier(self) -> Optional[str]: return self._current_tier
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        host = getattr(self, "_host", None)
        if host is None or obj is not host: return super().eventFilter(obj, event)
        if event.type() == QEvent.Type.Resize: self.relayout(force=False)
        return super().eventFilter(obj, event)
    def _apply_arrangement(self, tier: str) -> None:
        while self._grid.count(): self._grid.takeAt(0)
        cards_per_row = self._cards_per_row(tier)
        charts_per_row = self._charts_per_row(tier)
        full_span = max(cards_per_row, charts_per_row)
        row_cursor = 0; title_idx = 0
        if title_idx < len(self._section_titles):
            self._grid.addWidget(self._section_titles[title_idx], row_cursor, 0, 1, full_span); row_cursor += 1; title_idx += 1
        for i, card in enumerate(self._cards):
            r = row_cursor + i // cards_per_row; c = i % cards_per_row
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            card.setMinimumHeight(90)
            self._grid.addWidget(card, r, c, 1, 1)
        rows_used = (len(self._cards) + cards_per_row - 1) // cards_per_row if self._cards else 0
        row_cursor += rows_used
        if title_idx < len(self._section_titles):
            self._grid.addWidget(self._section_titles[title_idx], row_cursor, 0, 1, full_span); row_cursor += 1; title_idx += 1
        if self._charts:
            cols = charts_per_row
            for i, chart in enumerate(self._charts):
                r = row_cursor + i // cols; c = i % cols; span = 1
                if cols == 2 and i == len(self._charts) - 1 and i % cols == 0: span = 2
                chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                chart.setMinimumHeight(240)
                self._grid.addWidget(chart, r, c, 1, span)
            chart_rows = (len(self._charts) + cols - 1) // cols
            row_cursor += chart_rows
            self._grid.setRowStretch(row_cursor - 1, 1)
        if self._reserved is not None and tier in ("xxl", "xl", "lg"):
            self._grid.addWidget(self._reserved, row_cursor, 0, 1, cards_per_row); row_cursor += 1
        if title_idx < len(self._section_titles):
            self._grid.addWidget(self._section_titles[title_idx], row_cursor, 0, 1, full_span); row_cursor += 1; title_idx += 1
        if self._process_panel is not None:
            self._process_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            self._grid.addWidget(self._process_panel, row_cursor, 0, 1, full_span)
            self._grid.setRowStretch(row_cursor, 1); row_cursor += 1
        for r in range(row_cursor):
            if r != row_cursor - 1 and (self._charts and r == row_cursor - 2): continue
            if r < (len(self._cards) + cards_per_row - 1) // cards_per_row if self._cards else 0:
                self._grid.setRowStretch(r, 0)
    @staticmethod
    def _cards_per_row(tier: str) -> int:
        return {"xxl": 4, "xl": 4, "lg": 4, "md": 2, "sm": 1}[tier]
    @staticmethod
    def _charts_per_row(tier: str) -> int:
        return {"xxl": 2, "xl": 2, "lg": 2, "md": 1, "sm": 1}[tier]
