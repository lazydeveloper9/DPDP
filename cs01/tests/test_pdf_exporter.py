"""
Unit Tests for Stage 6 Executive PDF Exporter
============================================
Verifies export_pdf_report generates an exhaustive, publication-grade A4 PDF document
with detailed technical findings, before/after code remediation, RoPA inventory,
and Rule 13 evidence citations.
"""

from __future__ import annotations
from pathlib import Path

from cs01.models import (
    ScoredFindingBundle, ScanConfig, Severity, PassType,
    DpdpReadinessScore, PillarScore, ScoredFinding,
    ProductCapabilityReport, PersonalDataInventoryItem, StackCapabilities,
)
from cs01.pipeline.stage6_report.pdf_exporter import export_pdf_report, _build_pdf_html


def _create_mock_bundle(is_capped: bool = True) -> ScoredFindingBundle:
    pillars = [
        PillarScore(pillar_id="p1", label="Notice & Transparency", total_rules=5, passing_rules=4, score=80.0),
        PillarScore(pillar_id="p2", label="Consent Architecture", total_rules=6, passing_rules=3, score=50.0),
        PillarScore(pillar_id="p3", label="Security Safeguards", total_rules=10, passing_rules=6, score=60.0),
    ]
    readiness = DpdpReadinessScore(
        overall=60.0 if is_capped else 92.0,
        is_capped=is_capped,
        cap_reason="Capped due to 4 unresolved critical findings" if is_capped else None,
        pillars=pillars,
        max_statutory_ceiling_engaged="250_crore" if is_capped else None,
    )

    finding = ScoredFinding(
        id="CODE-DPDP-001:app.py:42",
        rule_id="CODE-DPDP-001",
        pass_type=PassType.A,
        file="backend/routes/user.py",
        line_start=42,
        line_end=42,
        snippet="logger.info(f'User registered: {aadhaar}')",
        matched_entity="aadhaar",
        dpdp_section="§8(5)",
        dpdp_rule="Rule 6",
        penalty_band="250_crore",
        severity=Severity.CRITICAL,
        message="Personal data flows directly into an unguarded logger sink",
        remediation="Mask personal data before logging using mask_aadhaar()",
    )

    return ScoredFindingBundle(
        scan_id="test-scan-pdf-001",
        scan_timestamp="2026-11-23T12:00:00Z",
        scan_root="/var/www/test-app",
        findings=[finding] if is_capped else [],
        readiness=readiness,
        max_penalty_band="250_crore" if is_capped else None,
        partial_scan=False,
    )


def test_build_pdf_html_content() -> None:
    """Verify HTML generation contains required DPDP sections, detailed findings, and metrics."""
    cfg = ScanConfig(scan_root="/var/www/test-app", output_dir="/tmp")
    bundle = _create_mock_bundle(is_capped=True)
    html_out = _build_pdf_html(bundle, cfg)

    assert "CS-01 DPDP Compliance Assessment Report" in html_out
    assert "READINESS CAPPED BY STATUTORY CRITICALS" in html_out
    assert "CODE-DPDP-001" in html_out
    assert "backend/routes/user.py:42" in html_out
    assert "250 Crore" in html_out or "250_crore" in html_out
    assert "Security Safeguards" in html_out
    assert "Rule 13" in html_out
    # Detailed 5-part technical breakdown
    assert "1. Detailed Technical Failure Analysis" in html_out
    assert "2. Statutory &amp; Regulatory Breach Analysis" in html_out or "2. Statutory & Regulatory Breach Analysis" in html_out
    assert "3. Real-World Threat Scenario &amp; Data Principal Blast Radius" in html_out or "3. Real-World Threat Scenario & Data Principal Blast Radius" in html_out
    assert "4. Production-Ready Refactored Code Fix" in html_out
    assert "5. Engineering Verification" in html_out
    assert "Prioritized 3-Phase Remediation Roadmap" in html_out


def test_build_pdf_html_with_ropa() -> None:
    """Verify that RoPA inventory items are formatted into the PDF HTML."""
    cfg = ScanConfig(scan_root="/var/www/test-app", output_dir="/tmp")
    bundle = _create_mock_bundle(is_capped=True)
    cap_report = ProductCapabilityReport(
        target_path="/var/www/test-app",
        stack=StackCapabilities(languages=["python"], frameworks=["fastapi"]),
        pii_inventory=[
            PersonalDataInventoryItem(
                category="National Identity",
                field_or_param="users.aadhaar_number",
                location_file="models/user.py",
                location_line=25,
                pii_type="AADHAAR",
                is_stored=True,
                is_encrypted=False,
            )
        ],
        has_personal_data=True,
    )
    html_out = _build_pdf_html(bundle, cfg, capability_report=cap_report)
    assert "Record of Processing Activities (RoPA)" in html_out
    assert "National Identity" in html_out
    assert "models/user.py:25" in html_out
    assert "Plaintext" in html_out


def test_export_pdf_report_generates_valid_pdf(tmp_path: Path) -> None:
    """Verify export_pdf_report writes a binary PDF with valid magic header."""
    cfg = ScanConfig(scan_root=str(tmp_path), output_dir=str(tmp_path))
    bundle = _create_mock_bundle(is_capped=True)
    pdf_target = tmp_path / "cs01-report.pdf"

    result_path = export_pdf_report(bundle, cfg, pdf_target)

    assert result_path.exists()
    assert result_path.stat().st_size > 2000  # Detailed multi-page PDF document

    # Verify standard PDF magic header bytes: %PDF-
    header_bytes = result_path.read_bytes()[:5]
    assert header_bytes == b"%PDF-"


def test_export_pdf_report_clean_bundle(tmp_path: Path) -> None:
    """Verify export_pdf_report handles a clean audit bundle without crashing."""
    cfg = ScanConfig(scan_root=str(tmp_path), output_dir=str(tmp_path))
    bundle = _create_mock_bundle(is_capped=False)
    pdf_target = tmp_path / "clean-report.pdf"

    result_path = export_pdf_report(bundle, cfg, pdf_target)

    assert result_path.exists()
    assert result_path.stat().st_size > 500
    assert result_path.read_bytes()[:5] == b"%PDF-"
