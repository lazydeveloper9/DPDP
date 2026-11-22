import pytest
from cs01.models import (
    ScoredFinding, PassType, Severity, ExposureContext,
)
from cs01.pipeline.stage5_classify.readiness_scorer import calculate_readiness_score


def test_clean_readiness_score():
    score = calculate_readiness_score([])
    assert score.overall == 100.0
    assert score.is_capped is False
    assert score.open_critical_count == 0
    assert score.open_high_count == 0


def test_critical_cap_enforcement():
    # Construct a CRITICAL §8(5) finding in 250_crore band
    critical_finding = ScoredFinding(
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

    readiness = calculate_readiness_score([critical_finding])

    # Uncapped score would be around 95, but CRITICAL cap must limit to max 60.0
    assert readiness.overall <= 60.0
    assert readiness.is_capped is True
    assert "250 Crore" in (readiness.cap_reason or "")
    assert readiness.open_critical_count == 1
    assert "250 Crore" in readiness.max_statutory_ceiling_engaged
