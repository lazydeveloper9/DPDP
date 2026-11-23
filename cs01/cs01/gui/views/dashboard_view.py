"""
CS-01 DPDP Compliance Desktop GUI - Executive Dashboard View (Screen 1).

Renders the full DPDP Act 2023 Executive Compliance Dashboard including:
  - 0–100 Readiness Gauge with dynamic capping badge
  - Section 33 Penalty Ceiling Banner with legal disclaimer
  - 8 Statutory DPDP Compliance Pillar scorecards
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
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

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header row
        header_layout = QHBoxLayout()
        title = QLabel("DPDP Act 2023 Executive Compliance Dashboard")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8fafc;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.capping_badge = QLabel("⚠️ Score Capped (Unresolved Section 33 Critical Findings)")
        self.capping_badge.setStyleSheet(
            "background-color: #ef4444; color: white; "
            "padding: 4px 8px; border-radius: 4px; font-weight: bold;"
        )
        self.capping_badge.setVisible(False)
        header_layout.addWidget(self.capping_badge)
        layout.addLayout(header_layout)

        # Upper row: Gauge + Penalty Banner
        top_row = QHBoxLayout()
        self.gauge = ReadinessGaugeWidget()
        top_row.addWidget(self.gauge)

        v_right = QVBoxLayout()
        self.penalty_banner = PenaltyCeilingBanner()
        v_right.addWidget(self.penalty_banner)

        self.cap_reason_label = QLabel("")
        self.cap_reason_label.setStyleSheet("color: #f59e0b; font-size: 12px; font-style: italic;")
        self.cap_reason_label.setWordWrap(True)
        v_right.addWidget(self.cap_reason_label)
        v_right.addStretch()
        top_row.addLayout(v_right, stretch=1)
        layout.addLayout(top_row)

        # 8 Statutory Pillars
        pillars_title = QLabel("8 Statutory DPDP Compliance Pillars")
        pillars_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #94a3b8;")
        layout.addWidget(pillars_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.grid_layout = QHBoxLayout(scroll_content)
        self.grid_layout.setSpacing(10)

        self.pillar_widgets: dict[str, PillarCardWidget] = {}
        for pid, label in _PILLAR_DEFS:
            w = PillarCardWidget(pid, label)
            self.pillar_widgets[pid] = w
            self.grid_layout.addWidget(w)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, stretch=1)

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def bind_bundle(self, bundle: ScoredFindingBundle) -> None:
        """Populate the dashboard with data from a completed ScoredFindingBundle."""
        readiness = bundle.readiness

        self.gauge.set_score(readiness.overall, readiness.is_capped, readiness.cap_reason)

        if readiness.is_capped:
            self.capping_badge.setVisible(True)
            self.capping_badge.setText(
                f"⚠️ Score Capped at {readiness.overall:.1f} "
                "(Unresolved Section 33 Critical Findings)"
            )
            self.cap_reason_label.setText(
                f"Dynamic Cap Reason: {readiness.cap_reason or 'CRITICAL section violation'}"
            )
        else:
            self.capping_badge.setVisible(False)
            self.cap_reason_label.setText("")

        self.penalty_banner.set_ceiling(
            readiness.max_statutory_ceiling_engaged or "None Engaged (₹0)"
        )

        for p in readiness.pillars:
            if p.pillar_id in self.pillar_widgets:
                self.pillar_widgets[p.pillar_id].set_data(p.score, len(p.failing_rule_ids))
