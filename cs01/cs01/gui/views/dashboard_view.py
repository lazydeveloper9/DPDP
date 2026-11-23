"""
CS-01 DPDP Compliance Desktop GUI - Executive Dashboard View (Screen 1).

Renders the full DPDP Act 2023 Executive Compliance Dashboard including:
  - Welcome banner with direct "Start New Scan" shortcut
  - 4 Executive KPI Cards (Readiness, Findings, Penalty Ceiling, PII Entities)
  - 0–100 Readiness Gauge with dynamic capping badge
  - Section 33 Penalty Ceiling Banner with legal disclaimer
  - Responsive 4-Column 8 Statutory DPDP Compliance Pillars Grid (Zero Horizontal Scroll)
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from cs01.gui.theme import (
    COLOR_BG_CARD,
    COLOR_BORDER_SUBTLE,
    COLOR_RISK_CRITICAL,
    COLOR_RISK_HIGH,
    COLOR_STATUS_SUCCESS,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)
from cs01.gui.widgets.penalty_banner import PenaltyCeilingBanner
from cs01.gui.widgets.pillar_card import PillarCardWidget
from cs01.gui.widgets.readiness_gauge import ReadinessGaugeWidget
from cs01.models.scored_finding import ScoredFindingBundle

_PILLAR_DEFS: list[tuple[str, str]] = [
    ("notice_consent", "Notice & Consent (§5, §6)"),
    ("security_safeguards", "Security Safeguards (§8(5))"),
    ("breach_readiness", "Breach Readiness (§8(6))"),
    ("retention_erasure", "Retention & Erasure (Rule 6)"),
    ("children_protection", "Children & PwD (§9)"),
    ("sdf_duties", "SDF Duties (§10, Rule 13)"),
    ("data_principal_rights", "Principal Rights (Rule 14)"),
    ("cross_border_cert_in", "Cross-Border & CERT-In"),
]


class DashboardView(QWidget):
    """
    Executive Dashboard with Readiness Gauge, Dynamic Capping, 8 Pillars, Section 33 Penalties.

    Attributes:
        gauge:          ReadinessGaugeWidget showing overall score.
        capping_badge:  Visible only when score has been dynamically capped.
        penalty_banner: Section 33 ceiling banner.
        pillar_widgets: Dict[pillar_id -> PillarCardWidget].
    """

    start_scan_requested = Signal()
    pillar_clicked = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Main scroll area ensuring everything fits vertically without horizontal scroll
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # 1. Welcome & Action Header
        header_layout = QHBoxLayout()
        header_text_vbox = QVBoxLayout()
        header_text_vbox.setSpacing(3)

        self.title_label = QLabel("DPDP Compliance Overview")
        self.title_label.setStyleSheet(
            f"font-size: 20px; font-weight: 700; color: {COLOR_TEXT_PRIMARY};"
        )
        header_text_vbox.addWidget(self.title_label)

        self.subtitle_label = QLabel(
            "Monitor privacy compliance, identify statutory security gaps, and track remediation progress."
        )
        self.subtitle_label.setStyleSheet(
            f"font-size: 10pt; color: {COLOR_TEXT_SECONDARY};"
        )
        header_text_vbox.addWidget(self.subtitle_label)
        header_layout.addLayout(header_text_vbox, stretch=1)

        # Dynamic Capping Badge
        self.capping_badge = QLabel("Score Capped (Unresolved Section 33 Critical Findings)")
        self.capping_badge.setStyleSheet(
            "background-color: #ef4444; color: white; "
            "padding: 5px 10px; border-radius: 4px; font-weight: bold; font-size: 9pt;"
        )
        self.capping_badge.setVisible(False)
        header_layout.addWidget(self.capping_badge)

        # Quick Action: Start New Scan Button
        self.start_scan_btn = QPushButton("Start New Scan")
        self.start_scan_btn.setProperty("class", "primary")
        self.start_scan_btn.setCursor(Qt.PointingHandCursor)
        self.start_scan_btn.clicked.connect(self.start_scan_requested.emit)
        header_layout.addWidget(self.start_scan_btn)
        layout.addLayout(header_layout)

        # 2. Executive KPI Cards Row (4 Cards)
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)

        self.kpi_score_card, self.kpi_score_val, self.kpi_score_sub = self._create_kpi_card(
            "READINESS SCORE", "100.0", "Compliant / Audit Ready", COLOR_STATUS_SUCCESS
        )
        self.kpi_findings_card, self.kpi_findings_val, self.kpi_findings_sub = self._create_kpi_card(
            "TOTAL FINDINGS", "0", "0 Critical · 0 High", COLOR_TEXT_PRIMARY
        )
        self.kpi_penalty_card, self.kpi_penalty_val, self.kpi_penalty_sub = self._create_kpi_card(
            "PENALTY CEILING", "₹0", "None Engaged (§33)", COLOR_STATUS_SUCCESS
        )
        self.kpi_pii_card, self.kpi_pii_val, self.kpi_pii_sub = self._create_kpi_card(
            "INDIAN PII IDENTIFIERS", "0", "Zero-Plaintext In-Memory", "#38bdf8"
        )

        kpi_row.addWidget(self.kpi_score_card)
        kpi_row.addWidget(self.kpi_findings_card)
        kpi_row.addWidget(self.kpi_penalty_card)
        kpi_row.addWidget(self.kpi_pii_card)
        layout.addLayout(kpi_row)

        # 3. Middle Row: Readiness Gauge + Section 33 Penalty Ceiling Banner
        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        self.gauge = ReadinessGaugeWidget()
        top_row.addWidget(self.gauge)

        v_right = QVBoxLayout()
        v_right.setSpacing(8)
        self.penalty_banner = PenaltyCeilingBanner()
        v_right.addWidget(self.penalty_banner)

        self.cap_reason_label = QLabel("")
        self.cap_reason_label.setStyleSheet(
            "color: #f59e0b; font-size: 11px; font-weight: 500; padding: 4px 6px; "
            "background-color: rgba(245, 158, 11, 0.1); border-radius: 4px;"
        )
        self.cap_reason_label.setWordWrap(True)
        self.cap_reason_label.setVisible(False)
        v_right.addWidget(self.cap_reason_label)
        v_right.addStretch()
        top_row.addLayout(v_right, stretch=1)
        layout.addLayout(top_row)

        # 4. 8 Statutory DPDP Pillars Section (Responsive 4-Column Grid)
        pillars_header_layout = QHBoxLayout()
        pillars_title = QLabel("8 Statutory DPDP Compliance Pillars")
        pillars_title.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};"
        )
        pillars_header_layout.addWidget(pillars_title)

        pillars_sub = QLabel("Evaluated against DPDP Act 2023 & Draft DPDP Rules 2025")
        pillars_sub.setStyleSheet(f"font-size: 10.5px; color: {COLOR_TEXT_SECONDARY};")
        pillars_header_layout.addWidget(pillars_sub)
        pillars_header_layout.addStretch()
        layout.addLayout(pillars_header_layout)

        # Responsive 4-Column x 2-Row Grid: NO HORIZONTAL SCROLLING
        self.pillars_container = QWidget()
        self.grid_layout = QGridLayout(self.pillars_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(12)

        self.pillar_widgets: dict[str, PillarCardWidget] = {}
        for idx, (pid, label) in enumerate(_PILLAR_DEFS):
            w = PillarCardWidget(pid, label)
            w.clicked.connect(self.pillar_clicked.emit)
            self.pillar_widgets[pid] = w
            row = idx // 4
            col = idx % 4
            self.grid_layout.addWidget(w, row, col)

        layout.addWidget(self.pillars_container)
        layout.addStretch()

        scroll_area.setWidget(content)
        outer_layout.addWidget(scroll_area)

    def _create_kpi_card(
        self, title: str, value: str, subtitle: str, value_color: str
    ) -> tuple[QFrame, QLabel, QLabel]:
        """Helper to create an executive metric KPI card."""
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background-color: {COLOR_BG_CARD}; "
            f"border: 1px solid {COLOR_BORDER_SUBTLE}; border-radius: 8px; padding: 12px; }}"
        )
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(12, 10, 12, 10)
        vbox.setSpacing(4)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 8.5pt; font-weight: 600; letter-spacing: 0.5px;")
        vbox.addWidget(t_lbl)

        v_lbl = QLabel(value)
        v_lbl.setStyleSheet(f"color: {value_color}; font-size: 19pt; font-weight: 700;")
        vbox.addWidget(v_lbl)

        s_lbl = QLabel(subtitle)
        s_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 8.5pt;")
        vbox.addWidget(s_lbl)

        return card, v_lbl, s_lbl

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def bind_bundle(self, bundle: ScoredFindingBundle) -> None:
        """Populate the dashboard with data from a completed ScoredFindingBundle."""
        readiness = bundle.readiness
        score = readiness.overall

        self.gauge.set_score(score, readiness.is_capped, readiness.cap_reason)

        # Update KPI Cards
        self.kpi_score_val.setText(f"{score:.1f}")
        if score >= 80:
            score_color = COLOR_STATUS_SUCCESS
            score_status = "Compliant / Audit Ready"
        elif score >= 60:
            score_color = "#f59e0b"
            score_status = "Moderate Risk Posture"
        else:
            score_color = COLOR_RISK_CRITICAL
            score_status = "Severe Statutory Non-Compliance"

        self.kpi_score_val.setStyleSheet(f"color: {score_color}; font-size: 19pt; font-weight: 700;")
        self.kpi_score_sub.setText("Score Capped" if readiness.is_capped else score_status)

        # Findings Counts
        findings = getattr(bundle, "findings", [])
        crit_count = sum(1 for f in findings if getattr(f.severity, "value", str(f.severity)).upper() == "CRITICAL")
        high_count = sum(1 for f in findings if getattr(f.severity, "value", str(f.severity)).upper() == "HIGH")
        total_count = len(findings)

        self.kpi_findings_val.setText(str(total_count))
        self.kpi_findings_sub.setText(f"{crit_count} Critical · {high_count} High")
        if crit_count > 0:
            self.kpi_findings_val.setStyleSheet(f"color: {COLOR_RISK_CRITICAL}; font-size: 19pt; font-weight: 700;")
        elif high_count > 0:
            self.kpi_findings_val.setStyleSheet(f"color: {COLOR_RISK_HIGH}; font-size: 19pt; font-weight: 700;")
        else:
            self.kpi_findings_val.setStyleSheet(f"color: {COLOR_STATUS_SUCCESS}; font-size: 19pt; font-weight: 700;")

        # Ceiling
        ceiling = readiness.max_statutory_ceiling_engaged or "None Engaged (₹0)"
        self.penalty_banner.set_ceiling(ceiling)
        self.kpi_penalty_val.setText("₹0" if "None" in ceiling else "₹250 Cr" if "250" in ceiling else ceiling.split()[0])
        self.kpi_penalty_sub.setText(ceiling)
        if "₹0" in ceiling or "None" in ceiling:
            self.kpi_penalty_val.setStyleSheet(f"color: {COLOR_STATUS_SUCCESS}; font-size: 19pt; font-weight: 700;")
        else:
            self.kpi_penalty_val.setStyleSheet(f"color: {COLOR_RISK_CRITICAL}; font-size: 19pt; font-weight: 700;")

        # Dynamic Capping badge and reason
        if readiness.is_capped:
            self.capping_badge.setVisible(True)
            self.capping_badge.setText(
                f"Score Capped at {readiness.overall:.1f} "
                "(Unresolved Section 33 Critical Findings)"
            )
            self.cap_reason_label.setVisible(True)
            self.cap_reason_label.setText(
                f"Dynamic Cap Reason: {readiness.cap_reason or 'CRITICAL section violation'}"
            )
        else:
            self.capping_badge.setVisible(False)
            self.cap_reason_label.setVisible(False)
            self.cap_reason_label.setText("")

        # 8 Pillars
        for p in readiness.pillars:
            if p.pillar_id in self.pillar_widgets:
                self.pillar_widgets[p.pillar_id].set_data(p.score, len(p.failing_rule_ids))
