"""TopProcessesPanel — a live, read-only table of the top RAM consumers."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QHeaderView, QLabel, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from ram_monitor.config import CONFIG, Config
from ram_monitor.core.models import ProcessInfo
from ram_monitor.utils.formatters import format_bytes, format_delta, format_percent


class TopProcessesPanel(QWidget):
    """A framed container holding a section title + the process table."""

    def __init__(self, parent: Optional[QWidget] = None, config: Config = CONFIG) -> None:
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
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setStretchLastSection(False)
        layout.addWidget(self._table)
        self.setLayout(layout)
        self._table.setRowCount(config.top_processes_count)

    def update_processes(self, processes: tuple[ProcessInfo, ...]) -> None:
        cfg = self._config
        rows = cfg.top_processes_count
        for row_idx in range(rows):
            if row_idx < len(processes):
                self._set_row(row_idx, processes[row_idx])
            else:
                self._clear_row(row_idx)

    def _set_row(self, row: int, info: ProcessInfo) -> None:
        cfg = self._config
        name_text = info.name
        mem_text = format_bytes(info.used_bytes, binary=False)
        share_text = format_percent(info.share_percent, decimals=1)
        arrow, delta_text = format_delta(info.delta_bytes)
        delta_full = f"{arrow} {delta_text}"
        if info.delta_direction == "up":
            delta_color = QColor(cfg.color_delta_up)
        elif info.delta_direction == "down":
            delta_color = QColor(cfg.color_delta_down)
        else:
            delta_color = QColor(cfg.color_delta_flat)
        name_item = self._table.item(row, 0)
        if name_item is None:
            name_item = QTableWidgetItem(name_text)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self._table.setItem(row, 0, name_item)
        else:
            name_item.setText(name_text)
        mem_item = self._table.item(row, 1)
        if mem_item is None:
            mem_item = QTableWidgetItem(mem_text)
            mem_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            mem_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 1, mem_item)
        else:
            mem_item.setText(mem_text)
        share_item = self._table.item(row, 2)
        if share_item is None:
            share_item = QTableWidgetItem(share_text)
            share_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            share_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 2, share_item)
        else:
            share_item.setText(share_text)
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
                item = QTableWidgetItem("\u2014")
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self._table.setItem(row, col, item)
            else:
                item.setText("\u2014")
            item.setForeground(QColor(self._config.color_delta_flat))
