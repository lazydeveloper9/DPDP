"""
Unit tests for canonical Markdown Report Exporter (cs01-report.md).
"""

import tempfile
from pathlib import Path
from cs01.models import (
    ScoredFindingBundle, ScoredFinding, DpdpReadinessScore, PillarScore,
    PassType, Severity, ScanConfig,
)
from cs01.pipeline.stage6_report.markdown_exporter import export_markdown_report


def test_export_markdown_report_structure():
    with tempfile.TemporaryDirectory() as tmp:
        out_file = Path(tmp) / "cs01-report.md"

        pillar = PillarScore(
            pillar_id="p1",
            label="Security Safeguards",
            score=50.0,
            total_rules=4,
            passing_rules=2,
            failing_rule_ids=["CODE-DPDP-001"],
        )
        readiness = DpdpReadinessScore(
            overall=60.0,
            is_capped=True,
            cap_reason="Critical Finding in §8(5)",
            pillars=[pillar],
            max_statutory_ceiling_engaged="₹250 Crore (§8(5))",
            open_critical_count=1,
            open_high_count=0,
        )
        finding = ScoredFinding(
            id="f1",
            rule_id="CODE-DPDP-001",
            pass_type=PassType.A,
            file="src/controllers/auth.py",
            line_start=15,
            line_end=15,
            snippet="logger.info(aadhaar)",
            matched_entity="aadhaar_number",
            dpdp_section="8(5)",
            dpdp_rule="Rule 6(1)(a)",
            penalty_band="250_crore",
            severity=Severity.CRITICAL,
            engine="Semgrep",
            message="Logging unmasked Aadhaar number",
            remediation="Mask Aadhaar number before logging",
            priority_score=0.95,
            confidence=0.95,
            statutory_ceiling_display="Up to ₹250 Crore",
        )
        bundle = ScoredFindingBundle(
            scan_id="test_scan",
            scan_timestamp="2026-11-23T00:00:00Z",
            scan_root=tmp,
            total_files_scanned=5,
            findings=[finding],
            readiness=readiness,
        )
        cfg = ScanConfig(org_name="FinTech Corp", fail_on="high")

        result_path = export_markdown_report(bundle, cfg, out_file)
        assert result_path.exists()
        content = result_path.read_text(encoding="utf-8")

        # Verify all 8 core sections exist
        assert "# Full-Stack Data Protection (DPDP) Compliance Assessment Report" in content
        assert "## 1. Document Control & Scan Provenance" in content
        assert "## 2. Executive & DPO Compliance Summary" in content
        assert "## 3. Compliance Coverage Matrix" in content
        assert "## 4. Auto-Generated RoPA & Personal Data-Flow Inventory" in content
        assert "## 5. Detailed Technical Findings" in content
        assert "## 6. Dynamic & Bonus Assessments" in content
        assert "## 7. Prioritized Remediation Roadmap" in content
        assert "## 8. Audit Methodology, Suppressions & Appendix" in content

        # Verify key template elements
        assert "[FND-0001]" in content
        assert "Sec 8(5) & Rule 6" in content
        assert "Up to ₹250 Crore" in content
        assert "FinTech Corp" in content

        # Verify elaborated subsections
        assert "#### 1. Detailed Technical Failure Analysis (Code Walkthrough)" in content
        assert "#### 2. Statutory & Regulatory Breach Analysis (DPDP Act, 2023 & DPDP Rules, 2025)" in content
        assert "#### 3. Real-World Threat Scenario & Data Principal Blast Radius" in content
        assert "#### 4. Production-Ready Refactored Code Fix" in content
        assert "#### 5. Engineering Verification & Automated Testing Plan" in content
