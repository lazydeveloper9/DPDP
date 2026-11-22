import pytest
from cs01.models import RawFinding, PassType, Severity
from cs01.pipeline.stage5_classify.deduplicator import deduplicate_findings


def test_deduplicate_identical_findings():
    f1 = RawFinding(
        id="f1",
        rule_id="CODE-DPDP-001",
        pass_type=PassType.A,
        file="app.py",
        line_start=10,
        snippet="logger.info(data)",
        matched_entity="func:register",
        dpdp_section="§8(5)",
        dpdp_rule="Rule 6(1)(a)",
        penalty_band="250_crore",
        severity=Severity.HIGH,
        message="Logging PII",
        remediation="Mask data",
        contributing_pii_hit_ids=["hit1"],
    )
    # Duplicate with higher severity (CRITICAL) and additional contributing hit
    f2 = f1.model_copy(
        update={
            "id": "f2",
            "severity": Severity.CRITICAL,
            "contributing_pii_hit_ids": ["hit2"],
        }
    )

    merged = deduplicate_findings([f1, f2])
    assert len(merged) == 1

    result = merged[0]
    assert result.severity == Severity.CRITICAL
    assert "hit1" in result.contributing_pii_hit_ids
    assert "hit2" in result.contributing_pii_hit_ids
