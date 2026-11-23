"""
CS-01 DPDP Compliance Desktop GUI - Indian PII Catalog Table Model.

QAbstractTableModel for detected Indian PII entities with zero-plaintext
in-memory storage. All sensitive values are shown only as SHA-256 digests
or masked snippets; never as raw plaintext.
"""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QObject, Qt

from cs01.models.flow_graph import PiiHit


class PiiTableModel(QAbstractTableModel):
    """
    QAbstractTableModel for detected Indian PII entities with zero plaintext storage.

    Columns (7):
        Type | File | Line | Value (Masked) | Validator Result | Confidence | SHA-256
    """

    COLUMNS = [
        "Type",
        "File",
        "Line",
        "Value (Masked)",
        "Validator Result",
        "Confidence",
        "SHA-256",
    ]

    def __init__(
        self,
        pii_hits: list[PiiHit] | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._hits: list[PiiHit] = pii_hits or []

    # -------------------------------------------------------------------------
    # QAbstractTableModel interface
    # -------------------------------------------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._hits)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or index.row() >= len(self._hits):
            return None
        hit = self._hits[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return hit.pii_type.value if hasattr(hit.pii_type, "value") else str(hit.pii_type)
            elif col == 1:
                return hit.file
            elif col == 2:
                return hit.line
            elif col == 3:
                # Zero-plaintext: show masked snippet or truncated SHA-256
                return hit.line_snippet or (hit.value_sha256[:12] + "...")
            elif col == 4:
                return hit.validator_result
            elif col == 5:
                return f"{hit.confidence:.2f}"
            elif col == 6:
                return hit.value_sha256

        return None

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def set_pii_hits(self, hits: list[PiiHit]) -> None:
        """Replace the PII hit list and refresh the view."""
        self.beginResetModel()
        self._hits = hits
        self.endResetModel()
