import pytest
import json
from pathlib import Path
from cs01.models import (
    ScoredFindingBundle, ScoredFinding, PassType, Severity,
    DpdpReadinessScore, ExposureContext,
)
from cs01.pipeline.stage6_report.sarif_exporter import export_sarif, MAX_SARIF_FINDINGS

def test_sarif_export_invariants(tmp_path: Path):
    bundle = ScoredFindingBundle(
        scan_id="test_scan",
        scan_timestamp="2026-11-23T00:00:00Z",
        scan_root=str(tmp_path),
        findings=[
            ScoredFinding(
                id="f1",
                rule_id="CODE-DPDP-001",
                pass_type=PassType.A,
                file="app.py",
                line_start=15,
                snippet="logger.info(aadhaar)",
                dpdp_section="§8(5)",
                dpdp_rule="Rule 6(1)(a)",
                penalty_band="250_crore",
                severity=Severity.CRITICAL,
                message="PII logging",
                remediation="Mask data",
                priority_score=0.90,
                statutory_ceiling_display="₹250 Crore",
            )
        ],
        readiness=DpdpReadinessScore(overall=60.0),
    )

    out_file = tmp_path / "report.sarif"
    sarif = export_sarif(bundle, out_file)

    assert len(sarif["runs"]) == 1
    run = sarif["runs"][0]
    assert run["tool"]["driver"]["name"] == "CS-01"

    for r in run["tool"]["driver"]["rules"]:
        tags = r.get("properties", {}).get("tags", [])
        assert len(tags) <= 8

    assert len(run["results"]) == 1
    res = run["results"][0]
    assert res["level"] == "error"
    assert res["ruleId"] == "CODE-DPDP-001"
    assert res["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "app.py"
