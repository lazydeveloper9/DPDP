"""
CS-01 DPDP Compliance Desktop GUI - Findings & PII Results View (Screen 4).

Provides:
  - Severity-filter + full-text search toolbar
  - QTableView of all ScoredFinding entries via FindingsTableModel
  - Detail drawer panel (rule_id, snippet, remediation, diff launcher)
  - Indian PII Catalog table via PiiTableModel (zero-plaintext)
"""
from __future__ import annotations

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from cs01.gui.models.findings_model import FindingsTableModel
from cs01.gui.models.pii_model import PiiTableModel
from cs01.gui.theme import COLOR_BG_CARD, COLOR_BORDER_SUBTLE, FONT_FAMILY_MONO
from cs01.models.flow_graph import PiiHit
from cs01.models.scored_finding import ScoredFindingBundle


class ResultsView(QWidget):
    """
    Detailed Findings Table, Indian PII Catalog, and finding detail drawer.

    Attributes:
        findings_model: FindingsTableModel providing filterable/searchable findings.
        pii_model:      PiiTableModel for zero-plaintext PII inventory.
        findings_table: Main QTableView bound to findings_model.
        pii_table:      PII inventory QTableView.
        severity_combo: Severity filter dropdown.
        search_input:   Full-text search box.
        drawer_title:   Drawer heading with rule_id & short message.
        drawer_section: DPDP statutory citation & penalty band.
        drawer_snippet: Code snippet text area.
        drawer_remediation: Remediation guidance label.
        autofix_btn:    "Apply Unified Diff" button (enabled when patch available).
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        title = QLabel("Scan Findings & Indian PII Inventory")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(title)

        # --- Filters toolbar ---
        tb_layout = QHBoxLayout()
        tb_layout.addWidget(QLabel("Filter Severity:"))
        self.severity_combo = QComboBox()
        self.severity_combo.addItems(["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
        self.severity_combo.currentTextChanged.connect(self._on_severity_filter)
        tb_layout.addWidget(self.severity_combo)

        tb_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Rule ID, message, file…")
        self.search_input.textChanged.connect(self._on_search_filter)
        tb_layout.addWidget(self.search_input)
        tb_layout.addStretch()
        layout.addLayout(tb_layout)

        # --- Splitter: Findings table | Detail drawer ---
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.findings_model = FindingsTableModel()
        self.findings_table = QTableView()
        self.findings_table.setModel(self.findings_model)
        self.findings_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.findings_table.setAlternatingRowColors(True)
        self.findings_table.selectionModel().currentRowChanged.connect(self._on_row_selected)
        splitter.addWidget(self.findings_table)

        # Detail drawer panel
        self.detail_frame = QFrame()
        self.detail_frame.setStyleSheet(
            f"background-color: {COLOR_BG_CARD}; "
            f"padding: 12px; border: 1px solid {COLOR_BORDER_SUBTLE};"
        )
        d_layout = QVBoxLayout(self.detail_frame)

        self.drawer_title = QLabel("Select a finding to inspect details")
        self.drawer_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #38bdf8;")
        d_layout.addWidget(self.drawer_title)

        self.drawer_section = QLabel("DPDP Statutory Citation: N/A")
        self.drawer_section.setWordWrap(True)
        d_layout.addWidget(self.drawer_section)

        self.drawer_snippet = QPlainTextEdit()
        self.drawer_snippet.setReadOnly(True)
        self.drawer_snippet.setStyleSheet(
            f"background-color: #050811; font-family: {FONT_FAMILY_MONO}; font-size: 11px;"
        )
        d_layout.addWidget(self.drawer_snippet)

        self.drawer_remediation = QLabel("Remediation: N/A")
        self.drawer_remediation.setWordWrap(True)
        d_layout.addWidget(self.drawer_remediation)

        self.autofix_btn = QPushButton("Apply Unified Diff Auto-Patch")
        self.autofix_btn.setEnabled(False)
        d_layout.addWidget(self.autofix_btn)
        d_layout.addStretch()

        splitter.addWidget(self.detail_frame)
        splitter.setSizes([600, 400])
        layout.addWidget(splitter, stretch=1)

        # --- PII Catalog ---
        pii_title = QLabel("Detected Indian PII Identifiers (Zero Plaintext In-Memory)")
        pii_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #94a3b8;")
        layout.addWidget(pii_title)

        self.pii_model = PiiTableModel()
        self.pii_table = QTableView()
        self.pii_table.setModel(self.pii_model)
        self.pii_table.setFixedHeight(140)
        layout.addWidget(self.pii_table)

    # -------------------------------------------------------------------------
    # Slots
    # -------------------------------------------------------------------------

    def _on_severity_filter(self, text: str) -> None:
        self.findings_model.set_severity_filter(text)

    def _on_search_filter(self, text: str) -> None:
        self.findings_model.set_search_query(text)

    def _on_row_selected(self, current: QModelIndex, _previous: QModelIndex) -> None:
        finding = self.findings_model.get_finding(current.row())
        if finding:
            self.drawer_title.setText(f"{finding.rule_id} — {finding.message}")
            self.drawer_section.setText(
                f"DPDP Statutory Citation: {finding.dpdp_section} ({finding.penalty_band})"
            )
            self.drawer_snippet.setPlainText(finding.snippet or "No snippet captured.")
            self.drawer_remediation.setText(f"Remediation: {finding.remediation}")
            self.autofix_btn.setEnabled(bool(finding.remediation))

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def bind_bundle(
        self,
        bundle: ScoredFindingBundle,
        pii_hits: list[PiiHit] | None = None,
    ) -> None:
        """Populate findings table and optional PII catalog from a scan bundle."""
        self.findings_model.set_findings(bundle.findings)
        if pii_hits is not None:
            self.pii_model.set_pii_hits(pii_hits)
