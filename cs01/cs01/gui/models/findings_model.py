"""
CS-01 DPDP Compliance Desktop GUI - Findings Table Model.

QAbstractTableModel presenting ScoredFinding entries with dynamic
severity filtering and full-text search across rule IDs, messages,
file paths, and DPDP statutory citation fields.
"""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QObject, Qt

from cs01.models.scored_finding import ScoredFinding


class FindingsTableModel(QAbstractTableModel):
    """
    QAbstractTableModel presenting ScoredFinding entries with search & severity filtering.

    Columns (7):
        Severity | Rule ID | DPDP Section | File Path | Line | Penalty Band | Priority Score
    """

    COLUMNS = [
        "Severity",
        "Rule ID",
        "DPDP Section",
        "File Path",
        "Line",
        "Penalty Band",
        "Priority Score",
    ]

    def __init__(
        self,
        findings: list[ScoredFinding] | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._all_findings: list[ScoredFinding] = findings or []
        self._filtered_findings: list[ScoredFinding] = list(self._all_findings)
        self._severity_filter: str = "ALL"
        self._search_query: str = ""

    # -------------------------------------------------------------------------
    # QAbstractTableModel interface
    # -------------------------------------------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._filtered_findings)

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
        if not index.isValid() or index.row() >= len(self._filtered_findings):
            return None
        finding = self._filtered_findings[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return finding.severity.value if hasattr(finding.severity, "value") else str(finding.severity)
            elif col == 1:
                return finding.rule_id
            elif col == 2:
                return finding.dpdp_section
            elif col == 3:
                return finding.file or "N/A"
            elif col == 4:
                return finding.line_start or 0
            elif col == 5:
                return finding.penalty_band
            elif col == 6:
                return f"{finding.priority_score:.1f}"

        return None

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def get_finding(self, row: int) -> ScoredFinding | None:
        """Return the ScoredFinding at the given visible row, or None if out of range."""
        if 0 <= row < len(self._filtered_findings):
            return self._filtered_findings[row]
        return None

    def set_findings(self, findings: list[ScoredFinding]) -> None:
        """Replace the full findings list and re-apply active filters."""
        self.beginResetModel()
        self._all_findings = findings
        self._apply_filters()
        self.endResetModel()

    def set_severity_filter(self, severity: str) -> None:
        """Filter visible rows by severity level (ALL, CRITICAL, HIGH, MEDIUM, LOW)."""
        self.beginResetModel()
        self._severity_filter = severity.upper()
        self._apply_filters()
        self.endResetModel()

    def set_search_query(self, query: str) -> None:
        """Filter visible rows by text search across rule_id, message, file, section, snippet."""
        self.beginResetModel()
        self._search_query = query.strip().lower()
        self._apply_filters()
        self.endResetModel()

    # -------------------------------------------------------------------------
    # Internal
    # -------------------------------------------------------------------------

    def _apply_filters(self) -> None:
        result = []
        for f in self._all_findings:
            sev = f.severity.value if hasattr(f.severity, "value") else str(f.severity)
            if self._severity_filter != "ALL" and sev != self._severity_filter:
                continue
            if self._search_query:
                q = self._search_query
                match = (
                    q in f.rule_id.lower()
                    or q in f.message.lower()
                    or (f.file and q in f.file.lower())
                    or q in f.dpdp_section.lower()
                    or q in (f.snippet or "").lower()
                )
                if not match:
                    continue
            result.append(f)
        self._filtered_findings = result
