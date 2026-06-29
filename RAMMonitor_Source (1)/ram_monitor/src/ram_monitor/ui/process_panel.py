"""TopProcessesPanel — a live, read-only table of the top RAM consumers.

The panel receives `tuple[ProcessInfo, ...]` via `update_processes()` and
rebuilds its rows in place. Cell widgets (QTableWidgetItem) are recycled
where possible — only the text changes between ticks — to keep Qt's
allocator quiet.

Delta rendering:
    The 4th column ("Δ since last tick") gets per-cell foreground color
    applied via `QBrush`. We do NOT use cell widgets (which would be slow
    at 8 rows × 1.5 s) — just colored text with arrow glyphs.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ram_monitor.config import CONFIG, Config
from ram_monitor.core.models import ProcessInfo
from ram_monitor.utils.formatters import format_bytes, format_delta, format_percent


class TopProcessesPanel(QWidget):
    """A framed container holding a section title + the process table."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        config: Config = CONFIG,
    ) -> None:
        super().__init__(parent)
        self._config = config

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        title = QLabel("Top Processes", self)
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self._table = QTableWidget(self)
        self._table.setColumnCount(len(config.process_columns))
        self._table.setHorizontalHeaderLabels(list(config.process_columns))
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Distribute column widths.
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # mem
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # share
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # delta
        header.setStretchLastSection(False)

        layout.addWidget(self._table)
        self.setLayout(layout)

        # Pre-create N empty rows; we'll mutate them in place on each tick.
        self._table.setRowCount(config.top_processes_count)

    # ── Public API ─────────────────────────────────────────────────────────

    def update_processes(self, processes: tuple[ProcessInfo, ...]) -> None:
        """Refresh the table contents. Called on every metrics tick."""
        cfg = self._config
        rows = cfg.top_processes_count

        # If we got fewer than expected (rare), pad to `rows` so the table
        # doesn't visibly jump in height.
        for row_idx in range(rows):
            if row_idx < len(processes):
                self._set_row(row_idx, processes[row_idx])
            else:
                self._clear_row(row_idx)

    # ── Internals ─────────────────────────────────────────────────────────

    def _set_row(self, row: int, info: ProcessInfo) -> None:
        """Populate one row. Creates items lazily, then mutates in place."""
        cfg = self._config

        name_text = info.name
        mem_text = format_bytes(info.used_bytes, binary=False)
        share_text = format_percent(info.share_percent, decimals=1)
        arrow, delta_text = format_delta(info.delta_bytes)
        delta_full = f"{arrow} {delta_text}"

        # Color for the delta cell.
        if info.delta_direction == "up":
            delta_color = QColor(cfg.color_delta_up)
        elif info.delta_direction == "down":
            delta_color = QColor(cfg.color_delta_down)
        else:
            delta_color = QColor(cfg.color_delta_flat)

        # Column 0: process name
        name_item = self._table.item(row, 0)
        if name_item is None:
            name_item = QTableWidgetItem(name_text)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self._table.setItem(row, 0, name_item)
        else:
            name_item.setText(name_text)

        # Column 1: memory
        mem_item = self._table.item(row, 1)
        if mem_item is None:
            mem_item = QTableWidgetItem(mem_text)
            mem_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            mem_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 1, mem_item)
        else:
            mem_item.setText(mem_text)

        # Column 2: share
        share_item = self._table.item(row, 2)
        if share_item is None:
            share_item = QTableWidgetItem(share_text)
            share_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            share_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 2, share_item)
        else:
            share_item.setText(share_text)

        # Column 3: delta
        delta_item = self._table.item(row, 3)
        if delta_item is None:
            delta_item = QTableWidgetItem(delta_full)
            delta_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            delta_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 3, delta_item)
        else:
            delta_item.setText(delta_full)
        delta_item.setForeground(delta_color)

    def _clear_row(self, row: int) -> None:
        for col in range(self._table.columnCount()):
            item = self._table.item(row, col)
            if item is None:
                item = QTableWidgetItem("—")
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self._table.setItem(row, col, item)
            else:
                item.setText("—")
            item.setForeground(QColor(self._config.color_delta_flat))
