"""
CS-01 DPDP Compliance Desktop GUI - Live Theme Preview Engine.

Renders actual production components using active theme tokens:
- Sample KPI Metric Card with hard offset shadow
- Primary, secondary, destructive, and icon buttons
- Form controls and inputs
- Real data table snippet with alternating and selected rows
- DPDP statutory severity badges
- Sidebar active/inactive item simulation
- Progress indicators
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from cs01.gui.theme_engine.theme_manager import ThemeManager
from cs01.gui.widgets.brutalist_widgets import BrutalistCard, BrutalistMetricCard


class ThemePreviewWidget(QFrame):
    """
    Live Visual Preview Panel showing real application components updated dynamically.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.tm = ThemeManager.instance()
        self.setProperty("class", "card")
        self._setup_ui()

        # Connect to theme updates for real-time repainting
        self.tm.theme_changed.connect(self.refresh_preview)

    def _setup_ui(self) -> None:
        self.setStyleSheet(
            "QFrame { background-color: #FFFFFF; border: 2px solid #111111; border-radius: 0px; }"
        )
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(12, 12, 12, 12)
        outer_layout.setSpacing(10)

        # Header
        hdr_layout = QHBoxLayout()
        title = QLabel("LIVE WORKSPACE PREVIEW")
        title.setStyleSheet("font-size: 11pt; font-weight: 800; color: #111111; letter-spacing: -0.2px;")
        hdr_layout.addWidget(title)
        hdr_layout.addStretch()

        self.live_indicator = QLabel("● REAL-TIME")
        self.live_indicator.setStyleSheet(
            "font-size: 8pt; font-weight: 800; color: #111111; background-color: #B8F044; "
            "border: 1px solid #111111; padding: 2px 6px;"
        )
        hdr_layout.addWidget(self.live_indicator)
        outer_layout.addLayout(hdr_layout)

        # Scroll area for preview items
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(4, 4, 4, 4)
        c_layout.setSpacing(14)

        # 1. Sample KPI Metric Card
        c_layout.addWidget(self._make_section_label("1. EXECUTIVE KPI CARD"))
        self.kpi_card = BrutalistMetricCard(
            title="Overall Readiness Score",
            value="87.5%",
            subtitle="DPDP Act Statutory Posture",
            bg_color="#FFFFFF",
            val_color="#111111",
            parent=container,
        )
        c_layout.addWidget(self.kpi_card)

        # 2. Buttons Preview
        c_layout.addWidget(self._make_section_label("2. INTERACTIVE BUTTON CONTROLS"))
        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)

        self.btn_primary = QPushButton("Start Audit")
        self.btn_primary.setProperty("class", "primary")
        btn_box.addWidget(self.btn_primary)

        self.btn_sec = QPushButton("Browse Target")
        self.btn_sec.setProperty("class", "secondary")
        btn_box.addWidget(self.btn_sec)

        self.btn_danger = QPushButton("Cancel")
        self.btn_danger.setProperty("class", "danger")
        btn_box.addWidget(self.btn_danger)

        self.btn_disabled = QPushButton("Locked")
        self.btn_disabled.setEnabled(False)
        btn_box.addWidget(self.btn_disabled)

        c_layout.addLayout(btn_box)

        # 3. Form Controls & Inputs
        c_layout.addWidget(self._make_section_label("3. INPUTS & DROPDOWNS"))
        input_box = QHBoxLayout()
        input_box.setSpacing(8)

        self.sample_input = QLineEdit()
        self.sample_input.setPlaceholderText("Search violations...")
        self.sample_input.setText("C:\\Projects\\DPDP-Target")
        input_box.addWidget(self.sample_input)

        self.sample_combo = QComboBox()
        self.sample_combo.addItems(["All Pillars", "Notice (Sec 5)", "Consent (Sec 6)", "PII Inventory"])
        input_box.addWidget(self.sample_combo)

        self.sample_check = QCheckBox("Mask PII in reports")
        self.sample_check.setChecked(True)
        input_box.addWidget(self.sample_check)

        c_layout.addLayout(input_box)

        # 4. Severity Badges
        c_layout.addWidget(self._make_section_label("4. STATUTORY SEVERITY BADGES"))
        badge_box = QHBoxLayout()
        badge_box.setSpacing(8)

        b_crit = QLabel("CRITICAL · 2")
        b_crit.setProperty("class", "badge-critical")
        badge_box.addWidget(b_crit)

        b_high = QLabel("HIGH · 5")
        b_high.setProperty("class", "badge-high")
        badge_box.addWidget(b_high)

        b_med = QLabel("MEDIUM · 3")
        b_med.setProperty("class", "badge-medium")
        badge_box.addWidget(b_med)

        b_low = QLabel("LOW · 1")
        b_low.setProperty("class", "badge-low")
        badge_box.addWidget(b_low)

        b_clean = QLabel("COMPLIANT")
        b_clean.setProperty("class", "badge-clean")
        badge_box.addWidget(b_clean)

        badge_box.addStretch()
        c_layout.addLayout(badge_box)

        # 5. Table Preview
        c_layout.addWidget(self._make_section_label("5. DATA GRID & TABLE PREVIEW"))
        self.table = QTableWidget(3, 4, container)
        self.table.setHorizontalHeaderLabels(["RULE ID", "SEVERITY", "DESCRIPTION", "STATUS"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setFixedHeight(120)

        rows = [
            ("DPDP-PII-001", "CRITICAL", "Unencrypted Aadhaar storage detected", "ACTION REQUIRED"),
            ("DPDP-SEC-005", "HIGH", "Notice mechanism missing statutory contact", "NEEDS REVIEW"),
            ("DPDP-SEC-008", "MEDIUM", "Consent withdrawal token expired", "REMEDIATED"),
        ]
        for r, data in enumerate(rows):
            for c, val in enumerate(data):
                item = QTableWidgetItem(val)
                self.table.setItem(r, c, item)
        self.table.selectRow(0)
        c_layout.addWidget(self.table)

        # 6. Progress Bar Preview
        c_layout.addWidget(self._make_section_label("6. SCAN PROGRESS BAR"))
        self.progress = QProgressBar()
        self.progress.setValue(72)
        c_layout.addWidget(self.progress)

        c_layout.addStretch()
        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

    def _make_section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size: 8.5pt; font-weight: 800; color: #595959; "
            "letter-spacing: 0.8px; margin-top: 4px;"
        )
        return lbl

    def refresh_preview(self) -> None:
        """Forces repainting and style refresh of preview elements."""
        self.kpi_card.update()
        self.table.viewport().update()
        self.update()
