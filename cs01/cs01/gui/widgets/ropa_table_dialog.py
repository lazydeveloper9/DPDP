"""
CS-01 DPDP Compliance Desktop GUI - Technical RoPA Table Dialog.

Modal QDialog rendering the Record of Processing Activities (RoPA) as a
5-column QTableWidget with CSV export capability for DPDP §8 compliance.
"""
from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class RopaTableDialog(QDialog):
    """
    Modal dialog displaying Record of Processing Activities (RoPA) with CSV export.

    Args:
        ropa_data: List of RoPA row dicts with keys:
                   system, purpose, lawful_basis, categories, retention.
    """

    HEADERS = [
        "System / Service",
        "Processing Purpose",
        "Lawful Basis",
        "Personal Data Categories",
        "Retention Period",
    ]

    def __init__(
        self,
        ropa_data: list[dict] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("DPDP Section 8 Technical RoPA (Record of Processing Activities)")
        self.resize(850, 500)
        self.ropa_data: list[dict] = ropa_data or []

        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self._populate()

        # Footer buttons
        h_layout = QHBoxLayout()
        self.export_btn = QPushButton("Export RoPA CSV")
        self.export_btn.clicked.connect(self._export_csv_prompt)
        h_layout.addWidget(self.export_btn)
        h_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        h_layout.addWidget(close_btn)
        layout.addLayout(h_layout)

    # -------------------------------------------------------------------------
    # Internal
    # -------------------------------------------------------------------------

    def _populate(self) -> None:
        self.table.setRowCount(len(self.ropa_data))
        for row, item in enumerate(self.ropa_data):
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get("system", "Default Service"))))
            self.table.setItem(row, 1, QTableWidgetItem(str(item.get("purpose", "Processing"))))
            self.table.setItem(row, 2, QTableWidgetItem(str(item.get("lawful_basis", "Consent §6"))))
            self.table.setItem(row, 3, QTableWidgetItem(str(item.get("categories", "Financial / Identity"))))
            self.table.setItem(row, 4, QTableWidgetItem(str(item.get("retention", "5 Years"))))

    def _export_csv_prompt(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export RoPA CSV", "ropa_export.csv", "CSV Files (*.csv)"
        )
        if path:
            self.export_to_csv(Path(path))

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def export_to_csv(self, file_path: Path) -> None:
        """Export the RoPA data to a CSV file at the given path."""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("System,Purpose,Lawful Basis,Categories,Retention\n")
            for item in self.ropa_data:
                cols = [
                    item.get("system", ""),
                    item.get("purpose", ""),
                    item.get("lawful_basis", ""),
                    item.get("categories", ""),
                    item.get("retention", ""),
                ]
                f.write(",".join(f'"{c}"' for c in cols) + "\n")
