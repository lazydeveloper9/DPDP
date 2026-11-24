"""
CS-01 DPDP Compliance Desktop GUI - Executive Dashboard View (Screen 1).

Renders the Bold Enterprise Neo-Brutalist Executive Compliance Dashboard including:
  - Editorial header with direct "START NEW SCAN" action
  - 4 Executive BrutalistMetricCard KPIs (Readiness, Findings, Penalty Ceiling, PII Entities)
  - 0–100 Readiness Gauge with dynamic capping badge and hard shadow
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
    COLOR_RISK_CRITICAL,
    COLOR_RISK_HIGH,
    COLOR_STATUS_SUCCESS,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)
from cs01.gui.widgets.brutalist_widgets import (
    BrutalistButton,
    BrutalistMetricCard,
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
        header_text_vbox.setSpacing(2)

        self.title_label = QLabel("DPDP COMPLIANCE OVERVIEW")
        self.title_label.setStyleSheet(
            f"font-size: 18pt; font-weight: 800; color: {BRUTALIST_BLACK}; letter-spacing: -0.5px;"
        )
        header_text_vbox.addWidget(self.title_label)

        self.subtitle_label = QLabel(
            "Monitor privacy compliance. Identify statutory gaps. Track remediation."
        )
        self.subtitle_label.setStyleSheet(
            f"font-size: 9.5pt; font-weight: 600; color: {BRUTALIST_MUTED};"
        )
        header_text_vbox.addWidget(self.subtitle_label)
        header_layout.addLayout(header_text_vbox, stretch=1)

        # Dynamic Capping Badge
        self.capping_badge = QLabel("SCORE CAPPED (§33 CRITICAL BREACH)")
        self.capping_badge.setStyleSheet(
            f"background-color: {BRUTALIST_RED}; color: #FFFFFF; "
            f"border: 2px solid {BRUTALIST_BORDER}; padding: 4px 10px; "
            "font-weight: 800; font-size: 8.5pt; border-radius: 0px;"
        )
        self.capping_badge.setVisible(False)
        header_layout.addWidget(self.capping_badge)

        # Quick Action: Start New Scan Button
        self.start_scan_btn = BrutalistButton("START NEW SCAN", variant="primary")
        self.start_scan_btn.clicked.connect(self.start_scan_requested.emit)
        header_layout.addWidget(self.start_scan_btn)
        layout.addLayout(header_layout)

        # 2. Executive KPI Cards Row (4 Brutalist Cards)
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)

        self.kpi_score_card = BrutalistMetricCard(
            "DPDP READINESS", "100.0", "Compliant / Audit Ready", bg_color=BRUTALIST_YELLOW
        )
        self.kpi_score_val = self.kpi_score_card.value_label
        self.kpi_score_sub = self.kpi_score_card.subtitle_label

        self.kpi_findings_card = BrutalistMetricCard(
            "TOTAL FINDINGS", "0", "0 Critical · 0 High", bg_color=BRUTALIST_SURFACE
        )
        self.kpi_findings_val = self.kpi_findings_card.value_label
        self.kpi_findings_sub = self.kpi_findings_card.subtitle_label

        self.kpi_penalty_card = BrutalistMetricCard(
            "PENALTY CEILING", "₹0", "None Engaged (§33)", bg_color=BRUTALIST_SURFACE
        )
        self.kpi_penalty_val = self.kpi_penalty_card.value_label
        self.kpi_penalty_sub = self.kpi_penalty_card.subtitle_label

        self.kpi_pii_card = BrutalistMetricCard(
            "INDIAN PII IDENTIFIERS", "0", "Zero-Plaintext In-Memory", bg_color=BRUTALIST_SURFACE_ALT
        )
        self.kpi_pii_val = self.kpi_pii_card.value_label
        self.kpi_pii_sub = self.kpi_pii_card.subtitle_label

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
            f"color: {BRUTALIST_BLACK}; font-size: 8.5pt; font-weight: 700; padding: 6px 10px; "
            f"background-color: {BRUTALIST_SURFACE_ALT}; border: 1.5px solid {BRUTALIST_BORDER}; border-radius: 0px;"
        )
        self.cap_reason_label.setWordWrap(True)
        self.cap_reason_label.setVisible(False)
        v_right.addWidget(self.cap_reason_label)
        v_right.addStretch()
        top_row.addLayout(v_right, stretch=1)
        layout.addLayout(top_row)

        # 4. 8 Statutory DPDP Pillars Section (Responsive 4-Column Grid)
        pillars_header_layout = QHBoxLayout()
        pillars_title = QLabel("8 STATUTORY DPDP COMPLIANCE PILLARS")
        pillars_title.setStyleSheet(
            f"font-size: 11pt; font-weight: 800; color: {BRUTALIST_BLACK}; letter-spacing: 0.5px;"
        )
        pillars_header_layout.addWidget(pillars_title)

        pillars_sub = QLabel("Evaluated against DPDP Act 2023 & Draft DPDP Rules 2025")
        pillars_sub.setStyleSheet(f"font-size: 9pt; font-weight: 600; color: {BRUTALIST_MUTED};")
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
            score_status = "Compliant / Audit Ready"
        elif score >= 60:
            score_status = "Moderate Risk Posture"
        else:
            score_status = "Severe Statutory Breach"

        self.kpi_score_sub.setText("Score Capped" if readiness.is_capped else score_status)

        # Findings Counts
        findings = getattr(bundle, "findings", [])
        crit_count = sum(1 for f in findings if getattr(f.severity, "value", str(f.severity)).upper() == "CRITICAL")
        high_count = sum(1 for f in findings if getattr(f.severity, "value", str(f.severity)).upper() == "HIGH")
        total_findings = len(findings)

        self.kpi_findings_val.setText(str(total_findings))
        self.kpi_findings_sub.setText(f"{crit_count} Critical · {high_count} High")

        # Capping Notification
        if readiness.is_capped:
            self.capping_badge.setVisible(True)
            self.capping_badge.setText(
                f"⚠️ Score Capped at {readiness.overall:.1f} (Unresolved Section 33 Critical Findings)"
            )
            self.cap_reason_label.setText(
                f"⚠ CAPPING ENGAGED: {readiness.cap_reason or 'Score capped due to unresolved Critical findings.'}"
            )
            self.cap_reason_label.setVisible(True)
        else:
            self.capping_badge.setVisible(False)
            self.cap_reason_label.setVisible(False)

        # Section 33 Maximum Statutory Penalty Exposure
        ceiling = (
            getattr(readiness, "max_statutory_ceiling_engaged", None)
            or getattr(readiness, "penalty_ceiling", None)
            or "None Engaged (₹0)"
        )
        self.penalty_banner.set_ceiling(ceiling)
        self.kpi_penalty_val.setText(ceiling)
        if "250" in ceiling or "200" in ceiling:
            pen_color = BRUTALIST_RED
            penalty_sub = "Statutory Max (§33)"
        elif "150" in ceiling or "50" in ceiling:
            pen_color = BRUTALIST_ORANGE
            penalty_sub = "Statutory Medium (§33)"
        else:
            pen_color = BRUTALIST_BLACK
            penalty_sub = "None Engaged (§33)"
        self.kpi_penalty_card.set_values(ceiling, penalty_sub, val_color=pen_color)

        # PII Identifiers count
        pii_identifiers = getattr(bundle, "pii_entities", [])
        pii_count = len(pii_identifiers)
        self.kpi_pii_card.set_values(str(pii_count))

        # 8 Statutory Pillars Scorecards
        pillars_data = getattr(readiness, "pillars", [])
        pillars_map = {p.pillar_id: p for p in pillars_data}

        for pid, widget in self.pillar_widgets.items():
            if pid in pillars_map:
                p_obj = pillars_map[pid]
                p_score = getattr(p_obj, "score", 100.0)
                failing_ids = getattr(p_obj, "failing_rule_ids", None)
                if failing_ids is not None:
                    p_fails = len(failing_ids)
                else:
                    p_fails = getattr(p_obj, "failing_rules_count", 0)
                widget.set_data(p_score, p_fails)
            else:
                widget.set_data(100.0, 0)
