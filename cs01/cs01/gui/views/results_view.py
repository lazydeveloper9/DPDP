"""
CS-01 DPDP Compliance Desktop GUI - Findings & PII Results View (Screen 4).

Provides:
  - Enterprise vulnerability management workspace
  - Severity-filter + full-text search toolbar with clear action
  - QTableView of all ScoredFinding entries via FindingsTableModel
  - Technical detail drawer panel (rule_id, snippet, statutory citation, diff launcher)
  - Indian PII Catalog table via PiiTableModel (zero-plaintext)
"""
from __future__ import annotations

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
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
from cs01.gui.theme import (
    COLOR_BG_CARD,
    COLOR_BORDER_SUBTLE,
    COLOR_STATUS_SUCCESS,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_FAMILY_MONO,
)
from cs01.gui.widgets.diff_viewer import DiffViewerDialog
from cs01.models.flow_graph import PiiHit
from cs01.models.scored_finding import ScoredFinding, ScoredFindingBundle


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
        self._selected_finding: ScoredFinding | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # 1. Header & Summary Row
        header_layout = QHBoxLayout()
        v_title = QVBoxLayout()
        v_title.setSpacing(2)

        title = QLabel("Security Findings & Statutory Compliance Issues")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {COLOR_TEXT_PRIMARY};")
        v_title.addWidget(title)

        subtitle = QLabel("Inspect identified DPDP statutory violations, AST code flaws, and production fixes.")
        subtitle.setStyleSheet(f"font-size: 9.5pt; color: {COLOR_TEXT_SECONDARY};")
        v_title.addWidget(subtitle)
        header_layout.addLayout(v_title, stretch=1)

        self.findings_counter_label = QLabel("0 Findings")
        self.findings_counter_label.setStyleSheet(
            f"background-color: {COLOR_BG_CARD}; color: #38bdf8; border: 1px solid {COLOR_BORDER_SUBTLE}; "
            "border-radius: 4px; padding: 4px 10px; font-size: 9pt; font-weight: bold;"
        )
        header_layout.addWidget(self.findings_counter_label)
        layout.addLayout(header_layout)

        # 2. Filters toolbar
        tb_layout = QHBoxLayout()
        tb_layout.setSpacing(8)

        sev_lbl = QLabel("Filter Severity:")
        sev_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 9.5pt; font-weight: 500;")
        tb_layout.addWidget(sev_lbl)

        self.severity_combo = QComboBox()
        self.severity_combo.addItems(["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
        self.severity_combo.setFixedHeight(30)
        self.severity_combo.currentTextChanged.connect(self._on_severity_filter)
        tb_layout.addWidget(self.severity_combo)

        search_lbl = QLabel("Search:")
        search_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 9.5pt; font-weight: 500; margin-left: 8px;")
        tb_layout.addWidget(search_lbl)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Rule ID, message, affected file, section…")
        self.search_input.setFixedHeight(30)
        self.search_input.textChanged.connect(self._on_search_filter)
        tb_layout.addWidget(self.search_input, stretch=1)

        self.clear_filters_btn = QPushButton("Clear")
        self.clear_filters_btn.setFixedHeight(30)
        self.clear_filters_btn.setCursor(Qt.PointingHandCursor)
        self.clear_filters_btn.clicked.connect(self._on_clear_filters)
        tb_layout.addWidget(self.clear_filters_btn)
        layout.addLayout(tb_layout)

        # 3. Splitter: Findings table | Detail drawer
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Findings table
        self.findings_model = FindingsTableModel()
        self.findings_table = QTableView()
        self.findings_table.setModel(self.findings_model)
        self.findings_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.findings_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.findings_table.setAlternatingRowColors(True)
        self.findings_table.verticalHeader().setVisible(False)
        self.findings_table.horizontalHeader().setStretchLastSection(True)
        self.findings_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.findings_table.selectionModel().currentRowChanged.connect(self._on_row_selected)
        splitter.addWidget(self.findings_table)

        # Right: Detail drawer panel
        self.detail_frame = QFrame()
        self.detail_frame.setStyleSheet(
            f"QFrame {{ background-color: {COLOR_BG_CARD}; "
            f"padding: 14px; border: 1px solid {COLOR_BORDER_SUBTLE}; border-radius: 8px; }}"
        )
        d_layout = QVBoxLayout(self.detail_frame)
        d_layout.setContentsMargins(14, 14, 14, 14)
        d_layout.setSpacing(10)

        # Drawer Title
        self.drawer_title = QLabel("Select a finding to inspect details")
        self.drawer_title.setStyleSheet("font-weight: bold; font-size: 13.5px; color: #38bdf8;")
        self.drawer_title.setWordWrap(True)
        d_layout.addWidget(self.drawer_title)

        # Statutory citation
        self.drawer_section = QLabel("DPDP Statutory Citation: N/A")
        self.drawer_section.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 9.5pt;")
        self.drawer_section.setWordWrap(True)
        d_layout.addWidget(self.drawer_section)

        # Affected Location
        self.drawer_location = QLabel("Location: N/A")
        self.drawer_location.setStyleSheet("color: #71829b; font-size: 9pt; font-family: monospace;")
        self.drawer_location.setWordWrap(True)
        d_layout.addWidget(self.drawer_location)

        # Code snippet well
        snippet_lbl = QLabel("Vulnerable Code Snippet / AST Evidence:")
        snippet_lbl.setStyleSheet(f"font-size: 8.5pt; font-weight: 600; color: {COLOR_TEXT_SECONDARY}; text-transform: uppercase;")
        d_layout.addWidget(snippet_lbl)

        self.drawer_snippet = QPlainTextEdit()
        self.drawer_snippet.setReadOnly(True)
        self.drawer_snippet.setStyleSheet(
            f"background-color: #090d16; color: #f1f5f9; "
            f"font-family: 'Cascadia Code', 'Consolas', monospace; font-size: 9.5pt; "
            f"border: 1px solid {COLOR_BORDER_SUBTLE}; border-radius: 4px; padding: 6px;"
        )
        d_layout.addWidget(self.drawer_snippet, stretch=1)

        # Remediation
        self.drawer_remediation = QLabel("Remediation: N/A")
        self.drawer_remediation.setStyleSheet("color: #f1f5f9; font-size: 9.5pt; line-height: 1.4;")
        self.drawer_remediation.setWordWrap(True)
        d_layout.addWidget(self.drawer_remediation)

        # Action: Apply / Review Unified Diff
        self.autofix_btn = QPushButton("Apply Unified Diff Auto-Patch")
        self.autofix_btn.setProperty("class", "primary")
        self.autofix_btn.setEnabled(False)
        self.autofix_btn.setCursor(Qt.PointingHandCursor)
        self.autofix_btn.clicked.connect(self._on_apply_patch)
        d_layout.addWidget(self.autofix_btn)

        splitter.addWidget(self.detail_frame)
        splitter.setSizes([620, 420])
        layout.addWidget(splitter, stretch=2)

        # 4. Indian PII Inventory Section
        pii_header_layout = QHBoxLayout()
        self.pii_title = QLabel("Detected Indian PII Identifiers (Zero Plaintext In-Memory)")
        self.pii_title.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        pii_header_layout.addWidget(self.pii_title)

        pii_sub = QLabel("All sensitive values stored exclusively as cryptographic SHA-256 digests.")
        pii_sub.setStyleSheet("font-size: 9pt; color: #22c55e;")
        pii_header_layout.addWidget(pii_sub)
        pii_header_layout.addStretch()
        layout.addLayout(pii_header_layout)

        self.pii_model = PiiTableModel()
        self.pii_table = QTableView()
        self.pii_table.setModel(self.pii_model)
        self.pii_table.setFixedHeight(140)
        self.pii_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.pii_table.setAlternatingRowColors(True)
        self.pii_table.verticalHeader().setVisible(False)
        self.pii_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.pii_table, stretch=1)

    # -------------------------------------------------------------------------
    # Slots
    # -------------------------------------------------------------------------

    def _on_severity_filter(self, text: str) -> None:
        self.findings_model.set_severity_filter(text)
        self._update_counter()

    def _on_search_filter(self, text: str) -> None:
        self.findings_model.set_search_query(text)
        self._update_counter()

    def _on_clear_filters(self) -> None:
        self.severity_combo.setCurrentText("ALL")
        self.search_input.clear()

    def _update_counter(self) -> None:
        count = self.findings_model.rowCount()
        self.findings_counter_label.setText(f"{count} Findings")

    def _on_row_selected(self, current: QModelIndex, _previous: QModelIndex) -> None:
        finding = self.findings_model.get_finding(current.row())
        self._selected_finding = finding
        if finding:
            self.drawer_title.setText(f"{finding.rule_id} — {finding.message}")
            self.drawer_section.setText(
                f"DPDP Statutory Citation: {finding.dpdp_section} ({finding.penalty_band})"
            )
            loc = f"{finding.file or 'N/A'}:{finding.line_start or 0}"
            self.drawer_location.setText(f"Affected File: {loc}")
            self.drawer_snippet.setPlainText(finding.snippet or "No snippet captured.")
            self.drawer_remediation.setText(f"Remediation: {finding.remediation}")
            self.autofix_btn.setEnabled(bool(finding.remediation))
        else:
            self.drawer_title.setText("Select a finding to inspect details")
            self.drawer_section.setText("DPDP Statutory Citation: N/A")
            self.drawer_location.setText("Location: N/A")
            self.drawer_snippet.setPlainText("")
            self.drawer_remediation.setText("Remediation: N/A")
            self.autofix_btn.setEnabled(False)

    def _on_apply_patch(self) -> None:
        """Launches the DiffViewerDialog for the selected finding."""
        if not self._selected_finding:
            return
        remediation = self._selected_finding.remediation or "No patch text."
        # Generate simulated diff or view remediation
        diff_text = f"--- a/{self._selected_finding.file}\n+++ b/{self._selected_finding.file}\n@@ -{self._selected_finding.line_start},5 +{self._selected_finding.line_start},5 @@\n-{self._selected_finding.snippet}\n+{remediation}\n"
        dlg = DiffViewerDialog(diff_content=diff_text, patch_id=self._selected_finding.rule_id, parent=self)
        dlg.exec()

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
        self._update_counter()
        if pii_hits is not None:
            self.pii_model.set_pii_hits(pii_hits)
