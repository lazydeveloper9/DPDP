import pytest
import json
from pathlib import Path
from cs01.models import (
    ScoredFindingBundle, ScoredFinding, PassType, Severity, DpdpReadinessScore,
)
from cs01.pipeline.stage6_report.html_exporter import export_html_report
from cs01.pipeline.stage6_report.gitlab_exporter import export_gitlab_sast


def test_html_and_gitlab_export(tmp_path: Path):
    bundle = ScoredFindingBundle(
        scan_id="test_scan",
        scan_timestamp="2026-11-23T00:00:00Z",
        scan_root=str(tmp_path),
        findings=[
            ScoredFinding(
                id="f1",
                rule_id="SQL-DPDP-001",
                pass_type=PassType.A,
                file="schema.sql",
                line_start=5,
                snippet="aadhaar VARCHAR(12)",
                dpdp_section="§8(5)",
                dpdp_rule="Rule 6(1)(a)",
                penalty_band="250_crore",
                severity=Severity.CRITICAL,
                message="Unencrypted PII column",
                remediation="Enable encryption",
                priority_score=0.90,
                statutory_ceiling_display="₹250 Crore",
            )
        ],
        readiness=DpdpReadinessScore(overall=60.0, max_statutory_ceiling_engaged="₹250 Crore"),
    )

    # HTML Test
    html_file = tmp_path / "report.html"
    export_html_report(bundle, html_file)
    assert html_file.exists()
    html_text = html_file.read_text(encoding="utf-8")
    assert "CS-01 DPDP Compliance Audit" in html_text
    assert "60.0" in html_text
    assert "SQL-DPDP-001" in html_text
    assert "Statutory Disclaimer:" in html_text

    # GitLab SAST Test
    gl_file = tmp_path / "gl-sast-report.json"
    gl_report = export_gitlab_sast(bundle, gl_file)
    assert gl_file.exists()
    assert len(gl_report["vulnerabilities"]) == 1
    assert gl_report["vulnerabilities"][0]["severity"] == "Critical"
