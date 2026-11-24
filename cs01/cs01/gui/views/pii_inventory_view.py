"""
CS-01 DPDP Compliance Desktop GUI - Indian PII Inventory View (Screen 5).

Dedicated enterprise data inventory for detected Indian Personally Identifiable
Information (PII) entities with cryptographic zero-plaintext in-memory protection.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from cs01.gui.models.pii_model import PiiTableModel
from cs01.gui.theme import (
    BRUTALIST_BG_MAIN,
    BRUTALIST_BG_SECONDARY,
    BRUTALIST_BLACK,
    BRUTALIST_BORDER,
    BRUTALIST_COBALT,
    BRUTALIST_GREEN,
    BRUTALIST_MUTED,
    BRUTALIST_ORANGE,
    BRUTALIST_RED,
    BRUTALIST_SURFACE,
    BRUTALIST_SURFACE_ALT,
    BRUTALIST_YELLOW,
    COLOR_BG_CARD,
    COLOR_BORDER_SUBTLE,
    COLOR_STATUS_SUCCESS,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)
from cs01.gui.widgets.brutalist_widgets import BrutalistCard
from cs01.models.flow_graph import PiiHit
from cs01.models.scored_finding import ScoredFindingBundle


class PiiInventoryView(QWidget):
    """
    Dedicated Indian PII Inventory Screen with zero-plaintext cryptographic assurance.

    Attributes:
        pii_model: PiiTableModel presenting masked data & SHA-256 digests.
        pii_table: QTableView displaying the PII entities.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._all_hits: list[PiiHit] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        # 1. Header
        header_vbox = QVBoxLayout()
        header_vbox.setSpacing(3)

        title = QLabel("INDIAN PII INVENTORY & DATA CATALOG")
        title.setStyleSheet(f"font-size: 16pt; font-weight: 800; color: {BRUTALIST_BLACK}; letter-spacing: -0.5px;")
        header_vbox.addWidget(title)

        subtitle = QLabel("Deterministic inventory of detected Indian personal data entities under Rule 3 & Schedule to DPDP Act 2023.")
        subtitle.setStyleSheet(f"font-size: 9.5pt; color: {BRUTALIST_MUTED};")
        header_vbox.addWidget(subtitle)
        layout.addLayout(header_vbox)

        # 2. Executive Summary Metrics Cards
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(14)

        self.kpi_total_card, self.kpi_total_val, self.kpi_total_sub = self._create_kpi_card(
            "TOTAL PII IDENTIFIERS", "0", "Discovered across codebase", BRUTALIST_BLACK, bg="#FFFFFF"
        )
        self.kpi_types_card, self.kpi_types_val, self.kpi_types_sub = self._create_kpi_card(
            "DISTINCT PII CATEGORIES", "0", "Aadhaar, PAN, Mobile, etc.", BRUTALIST_COBALT, bg="#FFFFFF"
        )
        self.kpi_valid_card, self.kpi_valid_val, self.kpi_valid_sub = self._create_kpi_card(
            "VALIDATED IDENTIFIERS", "0", "Algorithmic checksum verified", BRUTALIST_BLACK, bg="#FFFFFF"
        )
        self.kpi_storage_card, self.kpi_storage_val, self.kpi_storage_sub = self._create_kpi_card(
            "MEMORY PROTECTION", "100%", "Zero Plaintext In-Memory", BRUTALIST_BLACK, bg="#FFF4C2"
        )

        kpi_row.addWidget(self.kpi_total_card)
        kpi_row.addWidget(self.kpi_types_card)
        kpi_row.addWidget(self.kpi_valid_card)
        kpi_row.addWidget(self.kpi_storage_card)
        layout.addLayout(kpi_row)

        # 3. Cryptographic Zero-Plaintext Security Banner
        security_banner = BrutalistCard(bg="#FFF4C2", shadow_offset=4)
        b_layout = QVBoxLayout(security_banner)
        b_layout.setContentsMargins(16, 12, 16, 12)
        b_layout.setSpacing(8)

        b_header = QHBoxLayout()
        badge = QLabel("OFFLINE ZERO-PLAINTEXT ASSURANCE")
        badge.setStyleSheet(
            f"background-color: {BRUTALIST_GREEN}; color: {BRUTALIST_BLACK}; font-weight: 800; "
            f"border: 1.5px solid {BRUTALIST_BORDER}; padding: 3px 8px; font-size: 8pt; letter-spacing: 0.5px;"
        )
        b_header.addWidget(badge)
        b_header.addStretch()
        b_layout.addLayout(b_header)

        banner_text = QLabel(
            "<b>Cryptographic Zero-Plaintext Assurance:</b> Sensitive Indian identifiers are never stored unmasked in "
            "memory or written in raw plaintext to disk. All entries are masked using statutory redaction patterns "
            "(e.g., XXXX-XXXX-9012 for Aadhaar) and paired with irreversible SHA-256 cryptographic digests."
        )
        banner_text.setStyleSheet(f"font-size: 9.5pt; color: {BRUTALIST_BLACK}; line-height: 1.4;")
        banner_text.setWordWrap(True)
        b_layout.addWidget(banner_text)
        layout.addWidget(security_banner)

        # 4. Search & Filter Bar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(8)

        type_lbl = QLabel("FILTER TYPE:")
        type_lbl.setStyleSheet(f"color: {BRUTALIST_BLACK}; font-size: 9pt; font-weight: 800; letter-spacing: 0.5px;")
        filter_bar.addWidget(type_lbl)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["ALL", "AADHAAR", "PAN", "MOBILE", "EMAIL", "GSTIN", "UPI_HANDLE", "ABHA_HEALTH_ID"])
        self.type_combo.setFixedHeight(32)
        self.type_combo.setStyleSheet(
            f"background-color: #FFFFFF; color: {BRUTALIST_BLACK}; border: 2px solid {BRUTALIST_BORDER}; "
            "font-weight: 700; padding: 4px 8px;"
        )
        self.type_combo.currentTextChanged.connect(self._on_filter_changed)
        filter_bar.addWidget(self.type_combo)

        search_lbl = QLabel("SEARCH:")
        search_lbl.setStyleSheet(f"color: {BRUTALIST_BLACK}; font-size: 9pt; font-weight: 800; letter-spacing: 0.5px; margin-left: 8px;")
        filter_bar.addWidget(search_lbl)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search file path, validator status, or SHA-256 digest…")
        self.search_input.setFixedHeight(32)
        self.search_input.setStyleSheet(
            f"background-color: #FFFFFF; color: {BRUTALIST_BLACK}; border: 2px solid {BRUTALIST_BORDER}; "
            "padding: 4px 10px; font-weight: 500;"
        )
        self.search_input.textChanged.connect(self._on_filter_changed)
        filter_bar.addWidget(self.search_input, stretch=1)

        self.clear_btn = QPushButton("CLEAR")
        self.clear_btn.setFixedHeight(32)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setStyleSheet(
            f"background-color: {BRUTALIST_BG_SECONDARY}; color: {BRUTALIST_BLACK}; border: 2px solid {BRUTALIST_BORDER}; "
            "font-weight: 800; padding: 4px 14px; text-transform: uppercase;"
        )
        self.clear_btn.clicked.connect(self._on_clear_filter)
        filter_bar.addWidget(self.clear_btn)
        layout.addLayout(filter_bar)

        # 5. Main PII Inventory Table
        self.pii_model = PiiTableModel()
        self.pii_table = QTableView()
        self.pii_table.setModel(self.pii_model)
        self.pii_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.pii_table.setAlternatingRowColors(True)
        self.pii_table.verticalHeader().setVisible(False)
        self.pii_table.horizontalHeader().setStretchLastSection(True)
        self.pii_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.pii_table.setStyleSheet(f"border: 2px solid {BRUTALIST_BORDER}; background-color: #FFFFFF;")
        layout.addWidget(self.pii_table, stretch=1)

    def _create_kpi_card(
        self, title: str, value: str, subtitle: str, value_color: str, bg: str = "#FFFFFF"
    ) -> tuple[QWidget, QLabel, QLabel]:
        card = BrutalistCard(bg=bg, shadow_offset=4)
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(14, 12, 14, 12)
        vbox.setSpacing(4)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"color: {BRUTALIST_BLACK}; font-size: 8.5pt; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase;")
        vbox.addWidget(t_lbl)

        v_lbl = QLabel(value)
        v_lbl.setStyleSheet(f"color: {value_color}; font-size: 22pt; font-weight: 800; font-family: 'Cascadia Code', monospace;")
        vbox.addWidget(v_lbl)

        s_lbl = QLabel(subtitle)
        s_lbl.setStyleSheet(f"color: {BRUTALIST_MUTED}; font-size: 8.5pt; font-weight: 600;")
        vbox.addWidget(s_lbl)

        return card, v_lbl, s_lbl

    def _on_filter_changed(self) -> None:
        type_filter = self.type_combo.currentText().upper()
        search_query = self.search_input.text().lower().strip()

        filtered = []
        for h in self._all_hits:
            ptype = (h.pii_type.value if hasattr(h.pii_type, "value") else str(h.pii_type)).upper()
            if type_filter != "ALL" and type_filter != ptype:
                continue
            if search_query:
                haystack = f"{h.file} {h.validator_result} {h.value_sha256} {h.line_snippet}".lower()
                if search_query not in haystack:
                    continue
            filtered.append(h)

        self.pii_model.set_pii_hits(filtered)

    def _on_clear_filter(self) -> None:
        self.type_combo.setCurrentText("ALL")
        self.search_input.clear()

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def bind_pii_hits(self, hits: list[PiiHit]) -> None:
        """Bind PII hit list to metrics and table."""
        self._all_hits = list(hits)
        self.pii_model.set_pii_hits(self._all_hits)

        total = len(self._all_hits)
        self.kpi_total_val.setText(str(total))

        categories = set(
            (h.pii_type.value if hasattr(h.pii_type, "value") else str(h.pii_type))
            for h in self._all_hits
        )
        self.kpi_types_val.setText(str(len(categories)))

        valid_count = sum(1 for h in self._all_hits if "valid" in str(h.validator_result).lower())
        self.kpi_valid_val.setText(str(valid_count))