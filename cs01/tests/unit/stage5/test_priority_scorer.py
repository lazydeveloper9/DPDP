import pytest
from cs01.models import Severity, ExposureContext
from cs01.pipeline.stage5_classify.priority_scorer import PriorityScorer


def test_priority_score_calculation():
    scorer = PriorityScorer()

    # CRITICAL §8(5) in Production with 0.90 confidence:
    # 1.00 (Critical) * 0.90 (conf) * 1.00 (250 Cr) * 1.00 (prod) = 0.9000
    p_score, s_w, b_w, e_m = scorer.compute_score(
        severity=Severity.CRITICAL,
        penalty_band="250_crore",
        confidence=0.90,
        exposure=ExposureContext.PRODUCTION,
    )
    assert p_score == 0.9000
    assert s_w == 1.00
    assert b_w == 1.00
    assert e_m == 1.00

    # HIGH 50_crore in Production with 0.90 confidence:
    # 0.75 (High) * 0.90 (conf) * 0.40 (50 Cr) * 1.00 (prod) = 0.2700
    p_score_high, _, _, _ = scorer.compute_score(
        severity=Severity.HIGH,
        penalty_band="50_crore",
        confidence=0.90,
        exposure=ExposureContext.PRODUCTION,
    )
    assert p_score_high == 0.2700


def test_internal_exposure_reduction():
    scorer = PriorityScorer()

    # Exposure: INTERNAL has 0.50 multiplier
    p_score, _, _, e_m = scorer.compute_score(
        severity=Severity.CRITICAL,
        penalty_band="250_crore",
        confidence=0.90,
        exposure=ExposureContext.INTERNAL,
    )
    assert e_m == 0.50
    assert p_score == 0.4500
