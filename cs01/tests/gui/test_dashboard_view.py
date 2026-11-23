"""
Test Suite: Executive Dashboard View, Readiness Gauge, Dynamic Capping & Section 33 Penalties
Verifies R3 (Audit Dashboard and Results Presentation), F13, F14, F15.
"""

from __future__ import annotations

from cs01.gui.views.dashboard_view import DashboardView
from cs01.gui.widgets.penalty_banner import PenaltyCeilingBanner
from cs01.gui.widgets.readiness_gauge import ReadinessGaugeWidget

from cs01.models.scored_finding import (
    DpdpReadinessScore,
    ScoredFindingBundle,
)

# ============================================================================
# Tier 1: Nominal Executive Dashboard & Gauge Rendering
# ============================================================================

def test_readiness_gauge_clean_100(qtbot, clean_bundle: ScoredFindingBundle) -> None:
    """Verify gauge displays 100 on clean audit with zero engaged statutory penalties (F13)."""
    dashboard = DashboardView()
    qtbot.addWidget(dashboard)
    dashboard.show()

    dashboard.bind_bundle(clean_bundle)

    assert dashboard.gauge.score == 100.0
    assert dashboard.capping_badge.isVisible() is False
    assert "None Engaged" in dashboard.penalty_banner.ceiling_label.text()


def test_8_statutory_pillar_cards_rendering(qtbot, clean_bundle: ScoredFindingBundle) -> None:
    """Verify all 8 DPDP statutory pillar scorecards are rendered with compliant 100 scores (F13)."""
    dashboard = DashboardView()
    qtbot.addWidget(dashboard)
    dashboard.show()

    dashboard.bind_bundle(clean_bundle)

    expected_pillars = [
        "notice_consent",
        "security_safeguards",
        "breach_readiness",
        "retention_erasure",
        "children_protection",
        "sdf_duties",
        "data_principal_rights",
        "cross_border_cert_in",
    ]
    assert len(dashboard.pillar_widgets) == 8
    for pid in expected_pillars:
        assert pid in dashboard.pillar_widgets
        w = dashboard.pillar_widgets[pid]
        assert "100.0" in w.score_label.text()
        assert w.progress_bar.value() == 100


def test_pillar_score_progress_bars(qtbot, multi_findings_bundle: ScoredFindingBundle) -> None:
    """Verify pillar scorecards reflect deductions and count failing rules (F13)."""
    dashboard = DashboardView()
    qtbot.addWidget(dashboard)
    dashboard.show()

    dashboard.bind_bundle(multi_findings_bundle)

    # Security safeguards pillar has a failing rule
    sec_w = dashboard.pillar_widgets["security_safeguards"]
    assert "45.0" in sec_w.score_label.text()
    assert sec_w.progress_bar.value() == 45
    assert "1 Failing Rules" in sec_w.issues_badge.text()


def test_penalty_banner_250_crore(qtbot, capped_critical_bundle: ScoredFindingBundle) -> None:
    """Verify PenaltyCeilingBanner prominently renders ₹250 Crore ceiling for Section 8(5) violations (F15)."""
    dashboard = DashboardView()
    qtbot.addWidget(dashboard)
    dashboard.show()

    dashboard.bind_bundle(capped_critical_bundle)

    assert "₹250 Crore" in dashboard.penalty_banner.ceiling_label.text()
    assert "§8(5)" in dashboard.penalty_banner.ceiling_label.text()


def test_statutory_disclaimer_tooltip(qtbot) -> None:
    """Verify statutory legal disclaimer tooltip is present on penalty banner (F15)."""
    banner = PenaltyCeilingBanner()
    qtbot.addWidget(banner)
    banner.show()

    tooltip = banner.disclaimer_icon.toolTip()
    assert "statutory maximum ceiling" in tooltip
    assert "§33(2)" in tooltip
    assert "CS-01 is a technical auditing tool" in tooltip


# ============================================================================
# Tier 2: Boundary, Extreme Conditions & Dynamic Capping Enforcement
# ============================================================================

def test_dynamic_capping_threshold_exact_60(qtbot, capped_critical_bundle: ScoredFindingBundle) -> None:
    """
    Verify dynamic score capping strictly caps the overall readiness score at 60.0
    and activates warning badge when Section 33(1) CRITICAL finding is active (F14).
    """
    dashboard = DashboardView()
    qtbot.addWidget(dashboard)
    dashboard.show()

    dashboard.bind_bundle(capped_critical_bundle)

    assert dashboard.gauge.score == 60.0
    assert dashboard.gauge.is_capped is True
    assert dashboard.capping_badge.isVisible() is True
    assert "60.0" in dashboard.capping_badge.text()


def test_dynamic_capping_reason_display(qtbot, capped_critical_bundle: ScoredFindingBundle) -> None:
    """Verify explanatory dynamic cap reason is displayed to user (F14)."""
    dashboard = DashboardView()
    qtbot.addWidget(dashboard)
    dashboard.show()

    dashboard.bind_bundle(capped_critical_bundle)

    reason_text = dashboard.cap_reason_label.text()
    assert "CODE-DPDP-001" in reason_text
    assert "250_crore" in reason_text


def test_gauge_zero_score_boundary(qtbot) -> None:
    """Boundary test: 0.0 readiness score renders without ZeroDivisionError or crash (F13)."""
    gauge = ReadinessGaugeWidget()
    qtbot.addWidget(gauge)
    gauge.show()

    gauge.set_score(0.0)
    assert gauge.score == 0.0

    # Paint event simulation
    gauge.repaint()
    assert gauge.score == 0.0


def test_penalty_ceiling_200_crore_children(qtbot) -> None:
    """Verify Section 33(1) ₹200 Crore ceiling for Section 9 Children's privacy violations (F15)."""
    banner = PenaltyCeilingBanner()
    qtbot.addWidget(banner)
    banner.show()

    banner.set_ceiling("₹200 Crore (§9 Children Protection)")
    assert "₹200 Crore" in banner.ceiling_label.text()
    assert "§9" in banner.ceiling_label.text()


def test_penalty_ceiling_200_crore_breach(qtbot) -> None:
    """Verify Section 33(1) ₹200 Crore ceiling for Section 8(6) Breach notification failure (F15)."""
    banner = PenaltyCeilingBanner()
    qtbot.addWidget(banner)
    banner.show()

    banner.set_ceiling("₹200 Crore (§8(6) Breach Notification)")
    assert "₹200 Crore" in banner.ceiling_label.text()
    assert "§8(6)" in banner.ceiling_label.text()


def test_penalty_ceiling_150_crore_sdf(qtbot) -> None:
    """Verify Section 33(1) ₹150 Crore ceiling for Section 10 Significant Data Fiduciary duty breach (F15)."""
    banner = PenaltyCeilingBanner()
    qtbot.addWidget(banner)
    banner.show()

    banner.set_ceiling("₹150 Crore (§10 Significant Data Fiduciary)")
    assert "₹150 Crore" in banner.ceiling_label.text()
    assert "§10" in banner.ceiling_label.text()


def test_penalty_ceiling_50_crore_residual(qtbot) -> None:
    """Verify Section 33(1) ₹50 Crore residual procedural penalty band (F15)."""
    banner = PenaltyCeilingBanner()
    qtbot.addWidget(banner)
    banner.show()

    banner.set_ceiling("₹50 Crore (Residual / Procedural)")
    assert "₹50 Crore" in banner.ceiling_label.text()


# ============================================================================
# Tier 3: Pairwise Combinations
# ============================================================================

def test_gauge_score_and_banner_correlation(qtbot) -> None:
    """Pairwise test: Verify correlation between engaged penalty ceiling and score cap flag (F14, F15)."""
    dashboard = DashboardView()
    qtbot.addWidget(dashboard)
    dashboard.show()

    # Scenario A: Uncapped 95.0 with ₹50 Crore minor penalty
    bundle_a = ScoredFindingBundle(
        scan_id="scan-a",
        scan_timestamp="2026-11-23T12:00:00Z",
        scan_root="/repo",
        readiness=DpdpReadinessScore(
            overall=95.0,
            is_capped=False,
            max_statutory_ceiling_engaged="₹50 Crore (Residual / Procedural)",
        ),
    )
    dashboard.bind_bundle(bundle_a)
    assert dashboard.gauge.score == 95.0
    assert dashboard.capping_badge.isVisible() is False
    assert "₹50 Crore" in dashboard.penalty_banner.ceiling_label.text()

    # Scenario B: Capped 60.0 with ₹250 Crore critical penalty
    bundle_b = ScoredFindingBundle(
        scan_id="scan-b",
        scan_timestamp="2026-11-23T12:00:00Z",
        scan_root="/repo",
        readiness=DpdpReadinessScore(
            overall=60.0,
            is_capped=True,
            cap_reason="Critical leak",
            max_statutory_ceiling_engaged="₹250 Crore (§8(5) Security Safeguards)",
        ),
    )
    dashboard.bind_bundle(bundle_b)
    assert dashboard.gauge.score == 60.0
    assert dashboard.capping_badge.isVisible() is True
    assert "₹250 Crore" in dashboard.penalty_banner.ceiling_label.text()


# ============================================================================
# Tier 4: Real-World Workflow — Indian Fintech PII Breach & Capping Flow
# ============================================================================

def test_tier4_fintech_pii_breach_and_critical_capping_flow(
    qtbot, capped_critical_bundle: ScoredFindingBundle, multi_pii_hits
) -> None:
    """
    Tier 4 Scenario 2: Indian Fintech PII Breach & Dynamic Capping Flow.
    Verifies binding critical finding under Section 8(5), checking score capped strictly at 60.0,
    penalty banner displaying ₹250 Crore ceiling, and capping badge visible.
    """
    dashboard = DashboardView()
    qtbot.addWidget(dashboard)
    dashboard.show()

    dashboard.bind_bundle(capped_critical_bundle)

    # 1. Readiness gauge capped at 60.0
    assert dashboard.gauge.score == 60.0
    assert dashboard.gauge.is_capped is True

    # 2. Section 33 statutory penalty banner reflects maximum ₹250 Crore
    assert "₹250 Crore" in dashboard.penalty_banner.ceiling_label.text()

    # 3. Dynamic capping badge prominently displayed
    assert dashboard.capping_badge.isVisible() is True
    assert "60.0" in dashboard.capping_badge.text()

    # 4. Security Safeguards pillar scorecard has failing rule
    sec_pillar = dashboard.pillar_widgets["security_safeguards"]
    assert "40.0" in sec_pillar.score_label.text()
    assert "1 Failing Rules" in sec_pillar.issues_badge.text()
